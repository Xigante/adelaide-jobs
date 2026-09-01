# adelaide-jobs

Pipeline pessoal de **descoberta** de vagas em Adelaide, SA — para quem chega
com visto de estudante 500 e procura trabalho casual de entrada.

Ele coleta de fontes legítimas, deduplica, descarta o que não serve e ordena
o resto por aderência ao perfil. Não se candidata por você — e isso é uma
decisão de projeto, não uma limitação (veja [O que ele não faz](#o-que-ele-não-faz)).

```
fontes  →  SQLite (fonte da verdade)  →  triagem  →  score  →  CSV / Sheets
```

---

> **Num computador novo?** Leia [COMECAR-AQUI.md](COMECAR-AQUI.md) — são
> três passos e um duplo clique em `INSTALAR.bat`.
>
> **É uma IA?** [CLAUDE.md](CLAUDE.md) se você vai mexer no código,
> [PROMPT-PARA-IA.md](PROMPT-PARA-IA.md) se vai analisar o relatório.

---

## Em 5 minutos

```bash
git clone <este-repo> && cd adelaide-jobs
python -m venv ~/.venvs/adelaide-jobs             # Windows: python -m venv %USERPROFILE%\.venvs\adelaide-jobs
. ~/.venvs/adelaide-jobs/bin/activate             # Windows: %USERPROFILE%\.venvs\adelaide-jobs\Scripts\activate
pip install -e ".[ats,dev]"

cp .env.example .env        # cole a chave da Adzuna (grátis, sai na hora)
adelaide-jobs doctor        # o que a SUA rede alcança
adelaide-jobs collect       # coleta, deduplica e pontua
adelaide-jobs queue         # a fila, melhor primeiro
```

> **Por que o ambiente fica fora da pasta:** um virtualenv tem milhares de
> arquivos pequenos, e o OneDrive tenta sincronizar todos. Pelo mesmo motivo
> o banco de vagas fica em `~/.adelaide-jobs/jobs.db` — o SQLite não funciona
> dentro de pasta sincronizada. Ver [docs/OPERACAO.md](docs/OPERACAO.md).

Saída real, rodada contra as fixtures do repositório:

```
score  vaga                                         empregador             local
   95  Night Fill Team Member                       Coles Supermarkets     Mile End
   93  Kitchen Hand - Casual - No Experience Needed Adelaide Bistro Group  Adelaide
   90  Kitchenhand / Dishwasher                     Grenfell Street Cafe   Adelaide
   69  Cleaner - Early Morning                      SA Commercial Cleaning Port Adelaide
```

E o score é auditável — nenhuma nota sai de uma caixa preta:

```
$ adelaide-jobs why b0585ee9
Night Fill Team Member  —  Coles Supermarkets

score 95  (pesos w1)
  experience_barrier       1.00 × peso =  25.0
  english_load             1.00 × peso =  20.0
  visa_hours_fit           1.00 × peso =  15.0
  commute                  0.90 × peso =  10.8
  shift_fit                1.00 × peso =  10.0
  ...
```

---

## Comandos

| Comando | O que faz |
|---|---|
| `doctor` | Checa chaves, pacotes opcionais e **quais fontes a sua rede alcança** |
| `collect` | Coleta das fontes ligadas, deduplica, aplica knockouts e pontua |
| `score --rescore` | Recalcula tudo com os pesos atuais (sem tocar na rede) |
| `queue` | Mostra a fila de candidatura, melhor primeiro |
| `why <id>` | Abre a conta do score de uma vaga, linha por linha |
| `export --sheets` | Grava CSV e, se configurado, o Google Sheets |
| `stats` | Estado do banco |

---

## Fontes

| Fonte | Legitimidade | Estado |
|---|---|---|
| **Adzuna API** (`au`) | API oficial, chave gratuita | ligada |
| **Workday** — Bunnings, Hungry Jack's, Flinders | endpoint público sem auth | ligada (requer `[ats]`) |
| **SmartRecruiters** — McDonald's, Guzman y Gomez, ALDI | API pública documentada | ligada (requer `[ats]`) |
| **PageUp** — SA Health (~625 vagas) | robots.txt permite | ligada |
| **Alertas de e-mail** — SEEK, LinkedIn, Indeed, Jora, Adzuna, iworkfor, Gumtree | seus próprios dados | implementada, **desligada até você configurar o IMAP** |
| **SEEK v5** (direto) | ⚠️ contra os Termos de Uso | **desligada** |

O SEEK e o LinkedIn não têm API pública e proíbem acesso automatizado. O
caminho que este projeto usa para os dois é o **alerta de e-mail deles**,
lido por IMAP na sua própria caixa: mesma informação, entregue pela
plataforma, sem risco para a sua conta. Veja
[docs/FONTES.md](docs/FONTES.md#seek-e-linkedin--pela-porta-que-eles-deixam-aberta).

A camada de ATS usa [`ats-scrapers`](https://github.com/kalil0321/ats-scrapers) (MIT):
70+ ATS numa interface só, com canário noturno que detecta endpoint quebrado
em 24 horas. Não faz sentido reescrever isso.

### Sobre o SEEK

A v5 (`/api/jobsearch/v5/search`) é a API interna do SEEK. Funciona, não pede
autenticação e aceita `where=All Adelaide SA` — é a fonte mais rica que existe
para vaga casual em Adelaide.

Usá-la **viola os Termos de Uso**, que proíbem acesso automatizado. Não é crime
— é inadimplemento contratual. Mas a consequência prática é bloqueio de IP ou
da conta, e a sua conta do SEEK vai ser o canal principal de emprego da cidade
onde você mora. A assimetria é ruim: o ganho é conveniência, a perda é acesso.

Por isso ela vem **desligada**, com o aviso inteiro no cabeçalho de
`collectors/seek_v5.py`. Rode `adelaide-jobs doctor` primeiro: se ela responder
do seu IP, a decisão passa a ser sobre termos, não sobre viabilidade.

*(Nota histórica útil: a v4, `chalice-search`, morreu e devolve 403. É o
endpoint que quase todo repositório e tutorial antigo usa — se você achar
código apontando para lá, é código velho.)*

---

## Como o score funciona

**O extrator não calcula o número.** Ele lê o anúncio e devolve categorias
(`exp_req`, `eng_contact`, `shift_window`…); a aritmética mora em
`scoring.py`, em Python.

Isso não é preciosismo. Quando você recalibrar os pesos com os resultados
reais das suas candidaturas, isso vira um `git commit` — e reprocessar duas
mil vagas históricas vira um loop de 200 ms, em vez de duas mil chamadas de
API. É também o que permite trocar o extrator de regex pelo Gemini depois sem
mexer numa linha do scorer.

Oito dimensões, pesos em `config/profile.yaml`:

| Dimensão | Peso | Por quê |
|---|---:|---|
| `experience_barrier` | 25 | A barreira nº 1. "Full training provided" é ouro |
| `english_load` | 20 | Kitchen hand com inglês A2 funciona; barista não |
| `visa_hours_fit` | 15 | "Casual, up to 38 hours" é armadilha: passa de 48h/quinzena |
| `commute` | 12 | Sem carro. CBD é bem servido; Port Adelaide às 23h não é |
| `shift_fit` | 10 | Turno noturno paga penalty — **menos** o custo de voltar sem ônibus |
| `certification_barrier` | 8 | RSA é curso regulado; Food Handling é online e barato |
| `employer_pattern` | 6 | Rede grande contrata em volume e conhece visto de estudante |
| `career_bridge` | 4 | Peso pequeno de propósito: admin/dados não pode dominar a fila |

### Os knockouts, e as três armadilhas que eles evitam

Descartes gravam o motivo, sempre — sem isso você não consegue auditar quais
regras estão te custando vaga boa.

1. **`full-time` sem lookahead destrói o pipeline.** Uma fração enorme dos
   anúncios entry-level diz *"Casual, part-time and full-time positions
   available"*. Isso é `MIXED`, não `FULL_TIME`, e não bloqueia.
2. **"Senior" só conta no título.** No corpo casa com *"Senior Living
   facility"* — e derruba vaga de limpeza em aged care.
3. **`essential` ≠ `desirable`.** Muito anúncio de limpeza pede carro como
   *preferred*. São três estados, e só `ESSENTIAL` bloqueia. Na ambiguidade,
   o extrator escolhe o mais brando.

A regra de calibração é assimétrica de propósito:

> Manter uma vaga ruim custa alguns tokens.
> Descartar por engano uma vaga boa custa uma oportunidade de emprego.

---

## Deduplicação

A mesma vaga aparece na Adzuna, no alerta do SEEK e na página do empregador,
com títulos diferentes. Sem dedup você se candidata duas vezes na mesma vaga.

1. **Chave canônica exata** — `empregador :: papel :: subúrbio|CEP`, com
   dicionário de sinônimos: `dishwasher`, `kitchen attendant` e `kitchenhand`
   viram o mesmo papel. Pega ~70%, custo zero.
   *Não se aplica quando o empregador é anônimo* ("Private Advertiser", "Our
   client") — aí todos os kitchen hands de agência do CBD colapsariam numa
   vaga só.
2. **Blocking + fuzzy** — compara só dentro do bloco `(papel, 3 primeiros
   dígitos do CEP)`.
3. **Embeddings** — deliberadamente **fora**. Dois kitchen hands em
   restaurantes *diferentes* do CBD são semanticamente quase idênticos;
   embedding sozinho funde vagas legítimas.

### A vaga fantasma

Agências repostam o mesmo anúncio indefinidamente para montar banco de
currículos, sem vaga real. Quatro repostagens em 90 dias sem mudança de
conteúdo → `ghost_flag` e −15 no score.

Isto é o que o pipeline detecta e um humano olhando anúncio por anúncio não
detecta. É a justificativa mais forte para ele existir.

---

## O que ele não faz

Não preenche formulário e não envia candidatura. Três razões, em ordem de peso:

1. **A documentação do próprio SEEK define a fronteira.** Pré-preencher para o
   candidato revisar é o caso de uso sancionado; *"automatically submitting an
   application on a candidate's behalf"* é proibido em texto. Os termos do
   Indeed (07/2026) proíbem explicitamente automação do Indeed Apply.
2. **Volume não é o gargalo.** Uma ferramenta popular de auto-apply rendeu
   2.843 candidaturas → 1 oferta (0,14% de taxa de entrevista). O que decide
   uma vaga casual em Adelaide é: você mora perto? pode trabalhar à noite e no
   fim de semana? tem RSA? tem referência australiana? Automação não move
   nenhuma dessas.
3. **Bunnings, Kmart e Woolworths avaliam por entrevista de chat escrito**
   (Sapia), que roda detector de conteúdo gerado por IA desde 2023, com flag
   visível ao recrutador. Isso não é automação de candidatura — é fraude em
   avaliação, num fornecedor compartilhado pelos maiores empregadores casuais
   da cidade.

> **A regra:** a automação toca em tudo que produz um *rascunho*; em nada que
> produza um *compromisso*. Submit e qualquer palavra dentro de uma avaliação
> são compromissos.

---

## Estrutura

```
config/profile.yaml       perfil, pesos, teto de horas — a fonte da verdade
config/sources.yaml       fontes, ligadas e desligadas
src/adelaide_jobs/
  models.py               Job e Dimensions — o contrato
  collectors/base.py      molde: nenhum coletor derruba o run
  collectors/adzuna.py    API oficial
  collectors/ats.py       Workday / SmartRecruiters via ats-scrapers
  collectors/seek_v5.py   ⚠️ desligado — leia o cabeçalho
  extract.py              texto → dimensões (regex hoje, LLM depois)
  filters.py              knockouts, com o motivo gravado
  scoring.py              a aritmética, em Python
  dedup.py                chave canônica + fuzzy
  db.py                   SQLite: job_cluster + job_sighting
  pipeline.py             orquestração
  export.py               CSV e Google Sheets
  doctor.py               o que a sua rede alcança
tests/                    81 testes, nenhum toca a rede
```

Cada coletor separa `collect()` (rede) de `parse()` (puro) — é o que torna o
parsing testável contra fixture em disco.

---

## Documentação

| Documento | Para quê |
|---|---|
| **[docs/OPERACAO.md](docs/OPERACAO.md)** | Manual: o que é preciso, como instalar, cada comando, **onde ficam as vagas encontradas**, e a tabela de problemas conhecidos |
| **[docs/como-funciona.html](https://xigante.github.io/adelaide-jobs/como-funciona.html)** | **Comece por aqui.** O desenho de todas as peças e o passo a passo de cada alteração — mudar o inglês, os pesos, os termos, acrescentar empregador, publicar. Escrito para quem nunca viu o projeto |
| **[docs/FONTES.md](docs/FONTES.md)** | De onde vêm as vagas: o que está ligado, o que vale implementar a seguir, **o que foi descartado e por quê**, e o dicionário de como os australianos escrevem cada função |
| **[docs/AUTONOMIA.md](docs/AUTONOMIA.md)** | Rodar sem o Claude: trocar o extrator por outra IA (Ollama, Gemini), automatizar com agendador, calibrar os pesos com dados reais |
| **[docs/RELATORIO.md](docs/RELATORIO.md)** | O que foi construído, o que foi validado de verdade e o que não foi, os bugs encontrados rodando, e o que falta |

## Roadmap

- [x] Núcleo: coleta, dedup, knockouts, score, CSV
- [ ] **Coletor de alertas de e-mail (IMAP)** — a peça de maior volume e menor
      risco. Não existe pronta em lugar nenhum: o padrão é `imap_tools` com
      IDLE + regex `seek\.com\.au/job/(\d+)` no corpo, que sobrevive a
      redesenho do template. É meia tarde de trabalho.
- [ ] Extrator Gemini implementando o mesmo protocolo de `extract.py`
- [ ] Tempo real de viagem via GTFS do Adelaide Metro — **incluindo a volta**
      no horário de término do turno
- [ ] Log de resultado por candidatura + teste de monotonicidade do score
- [ ] Contador de horas na quinzena rolante (teto operacional de 44h, não 48)
      e alerta 14 dias antes da transição *break → in session*

---

## Antes de confiar nos números

Duas coisas precisam ser confirmadas e **não podem ser inferidas**:

1. **O calendário oficial de *scheduled breaks* do ILSC.** ELICOS não tem as
   férias longas de uma universidade. Todo o desenho de horas depende disso.
2. **Turma de manhã ou de tarde.** Trava ou destrava turnos inteiros.
   Enquanto `class_pattern` for `UNKNOWN`, o scorer trata conflito de horário
   como penalidade parcial em vez de bloqueio.

E os regex de knockout precisam de um conjunto de teste de ~200 anúncios reais
rotulados à mão antes de merecerem confiança total. Os 81 testes cobrem a
lógica; não substituem dados reais.

## Licença

MIT.
