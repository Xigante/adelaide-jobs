# Manual de operação

Como instalar, rodar, e onde cada coisa fica.

---

## O que é preciso

| Item | Obrigatório? | Observação |
|---|---|---|
| **Python 3.10 ou maior** | sim | No Windows, marque **"Add python.exe to PATH"** no instalador |
| **Chave da Adzuna** | não, mas quase | Grátis e instantânea em <https://developer.adzuna.com/signup>. Sem ela sobram só as fontes de ATS |
| **Git** | não | Só para versionar. O programa roda sem |
| **Conexão** | sim | A coleta é feita por rede. Rede corporativa que inspeciona tráfego pode barrar |
| Windows, macOS ou Linux | — | Foi validado em Windows e Linux |

Não precisa de conta em nada além da Adzuna. Não precisa de chave de IA:
a v1 é regex e aritmética, sem LLM.

---

## Instalação

### Windows, jeito curto

Clique duplo em **`RODAR.bat`** (na pasta acima desta). Ele acha o Python,
cria o ambiente virtual, instala tudo, roda os testes, pergunta as chaves
e escreve o `.env`.

### Qualquer sistema, na mão

```bash
python -m venv ~/.venvs/adelaide-jobs        # Windows: python -m venv %USERPROFILE%\.venvs\adelaide-jobs
source ~/.venvs/adelaide-jobs/bin/activate   # Windows: %USERPROFILE%\.venvs\adelaide-jobs\Scripts\activate
pip install -e ".[ats]"
cp .env.example .env                         # e preencha ADZUNA_APP_ID e ADZUNA_APP_KEY
adelaide-jobs doctor
```

> **Crie o ambiente virtual FORA de pasta sincronizada.** Um venv tem
> milhares de arquivos pequenos; o OneDrive tenta sincronizar todos e
> trava. Por isso o comando acima aponta para o perfil do usuário.

---

## Onde cada coisa fica

Esta é a pergunta que mais volta. Os caminhos:

| O quê | Onde | Por quê ali |
|---|---|---|
| **As vagas encontradas** | `C:\Users\<você>\.adelaide-jobs\jobs.db` <br> (Linux/mac: `~/.adelaide-jobs/jobs.db`) | **Fora da pasta do projeto de propósito.** O SQLite não funciona dentro do OneDrive — dá `disk I/O error`, porque precisa de travas de arquivo que pasta sincronizada não oferece |
| **O relatório para olhar** | `<projeto>/exports/vagas.html` | **Clique duplo e abre no navegador.** Gerado automaticamente no fim de cada `collect`. Tem busca e ordenação por coluna |
| **A fila em planilha** | `<projeto>/exports/fila.csv` | Também gerado no fim do `collect`. Abre no Excel |
| **Suas chaves** | `<projeto>/.env` | Ignorado pelo git. Nunca vai para o GitHub |
| **Seu perfil e pesos** | `<projeto>/config/profile.yaml` | Versionado. É a fonte da verdade do que o sistema considera uma vaga boa |
| **As fontes** | `<projeto>/config/sources.yaml` | Liga e desliga coletor, define os termos de busca |
| **O ambiente virtual** | `C:\Users\<você>\.venvs\adelaide-jobs` | Fora do OneDrive |

**Esqueceu onde está tudo?** O programa responde:

```
adelaide-jobs onde
```

Ele lista cada caminho e marca com `*` o que ainda não foi criado.

Para usar outro caminho de banco:

```bash
adelaide-jobs --db "D:\dados\vagas.db" collect
```

### Como olhar as vagas

1. **`exports/vagas.html`** — clique duplo. É o caminho mais direto, e não
   precisa de terminal para nada. Filtra enquanto você digita e reordena
   ao clicar no cabeçalho.
2. **`adelaide-jobs queue`** — a mesma fila no terminal.
3. **`exports/fila.csv`** no Excel.
4. **[DB Browser for SQLite](https://sqlitebrowser.org/)** — grátis, abre o
   arquivo e deixa você rodar SQL. Útil para perguntas que a CLI não faz:

```sql
-- vagas de back-of-house a menos de 5 km, ainda não aplicadas
SELECT score, title, employer, suburb
FROM job_cluster
WHERE verdict = 'SCORED'
  AND applied_at IS NULL
  AND json_extract(dims_json, '$.eng_contact') = 'BOH_MINIMAL'
  AND json_extract(dims_json, '$.distance_km') < 5
ORDER BY score DESC;
```

---

## Os comandos

### `doctor` — o que a sua rede alcança

```
adelaide-jobs doctor
```

Testa seis endereços e diz quais respondem **do seu IP**. Rode este
primeiro, sempre. Ele também confere se as chaves estão no `.env` e se os
pacotes opcionais estão instalados.

Um 403 na linha do SEEK é resultado esperado, não erro seu — leia
`src/adelaide_jobs/collectors/seek_v5.py` para entender por quê.

### `collect` — buscar, deduplicar e pontuar

```
adelaide-jobs collect
adelaide-jobs collect --source adzuna     # só uma fonte
```

Coleta das fontes ligadas no `sources.yaml`, deduplica contra o que já
está no banco, aplica os knockouts e pontua. Imprime um resumo com quanto
entrou, quanto era repetido, quanto foi bloqueado e por qual regra.

No fim ele **gera o `exports/vagas.html` e o `exports/fila.csv` sozinho**,
e imprime o caminho completo dos dois. Use `--no-export` para pular.

A coleta da Adzuna varre **por categoria**, não só por palavra-chave.
Categoria traz o setor inteiro num raio de 25 km; palavra-chave traz só o
que casa a frase. A diferença é grande: "kitchen hand" devolve 53 vagas,
a categoria de hospitality devolve 1.262.

Rodar duas vezes seguidas não duplica nada — a segunda execução vê tudo
como "já visto".

### `queue` — a fila

```
adelaide-jobs queue
adelaide-jobs queue --threshold 70 --limit 20
```

As vagas ordenadas por aderência ao seu perfil, melhor primeiro. O corte
padrão está em `queue_threshold` no `profile.yaml`.

### `why` — por que essa nota

```
adelaide-jobs why b0585ee9
```

Abre a conta linha por linha. É o comando que impede o score de ser
opinião:

```
score 87  (pesos w1)
  experience_barrier       1.00 × peso =  25.0
  english_load             1.00 × peso =  20.0
  visa_hours_fit           0.84 × peso =  12.6
  commute                  1.00 × peso =  12.0
  ...
```

Se uma vaga boa aparecer com nota baixa, este comando mostra qual
dimensão a derrubou — e aí você ajusta o peso ou o extrator, com
evidência.

### `score --rescore` — recalcular tudo

```
adelaide-jobs score --rescore
```

Apaga as notas e recalcula com os pesos atuais, **sem tocar na rede**.
É o comando que torna a recalibração barata: mudou peso no
`profile.yaml`, roda isso e vê o efeito em segundos.

### `export` — para o Excel e o Sheets

```
adelaide-jobs export
adelaide-jobs export --sheets
```

### `stats` — estado do banco

```
adelaide-jobs stats
```

---

## Ajustar o sistema ao seu caso

### `config/profile.yaml`

O que mais importa mexer:

- **`study.class_pattern`** — `AM`, `PM` ou `UNKNOWN`. Assim que souber o
  horário das aulas, preencha. Turma de manhã libera turno noturno; turma
  de tarde mata metade das vagas de jantar. Enquanto for `UNKNOWN`, o
  scorer trata conflito de horário como penalidade parcial em vez de
  bloqueio.
- **`visa.operational_cap`** — está em 44h, não 48. Turno casual estoura,
  e a responsabilidade pelo limite é sua, não do empregador.
- **`scoring.weights`** — os oito pesos, somando 100. Mudou? Suba o
  `scoring.version` junto, para conseguir comparar antes e depois.
- **`transport.max_commute_km`** — acima disso a vaga é bloqueada.

### Quando o seu inglês melhorar

Este é o ajuste que mais muda o resultado, e ele é uma linha só:

```yaml
english:
  current_level: A2      # A1 A2 B1 B2 C1 C2
```

Depois de mudar, rode `adelaide-jobs score --rescore`.

Duas coisas acontecem sozinhas. Primeiro, **vaga com atendimento ao
cliente deixa de ser penalizada** — em A2 uma vaga de balcão perde quase
todos os pontos de inglês; em B2 ela perde metade; em C1, quase nada.
Segundo, **o peso da própria dimensão de inglês cai**, porque ela deixa
de ser o gargalo, e os 14 pontos liberados são redistribuídos entre as
outras sete dimensões, proporcionalmente.

| Nível | Peso do inglês | O que muda na prática |
|---|---|---|
| A2 | 20 | Só back of house pontua bem |
| B1 | 15 | Balcão de café começa a aparecer |
| B2 | 10 | Atendimento vira opção normal |
| C1 | 6 | O inglês quase não pesa mais |

A soma continua exatamente 100 em qualquer nível, então as notas de
meses diferentes seguem comparáveis — uma vaga que era A- em março e
continua A- em julho é a mesma qualidade de vaga, não um artefato da
mudança de peso.

Exemplo real, a mesma vaga de atendimento:
**A2 → 58 pontos · B1 → 64 · B2 → 67.** Ela sobe de "talvez" para "vale
olhar" sem que nada no anúncio tenha mudado.

### `config/sources.yaml`

- `enabled: true/false` liga e desliga cada fonte.
- `adzuna.queries` são os termos de busca, **um request por termo**. Cada
  um está anotado com quantas vagas devolveu no teste real.
- `seek_v5` vem **desligado**. O cabeçalho do módulo explica o risco antes
  de você decidir.

---

## Problemas conhecidos

Todos foram encontrados rodando de verdade, não em teoria.

| Sintoma | Causa | Solução |
|---|---|---|
| `disk I/O error` ao abrir o banco | Caminho dentro do OneDrive, Dropbox ou unidade de rede | Use o padrão (`~/.adelaide-jobs/jobs.db`) ou passe `--db` para fora da pasta sincronizada |
| `AUTH_FAIL` da Adzuna | Chave errada, trocada de lugar, ou marcador não substituído na URL | `app_id` é o curto (~8 caracteres), `app_key` é o longo (~32). Confira em <https://developer.adzuna.com/admin/access_details> |
| Busca por "night fill" volta vazia | O índice da Adzuna não casa essa expressão | Já documentado no `sources.yaml`. Turno noturno de supermercado tem que vir da página de carreiras do Coles/Woolworths ou dos alertas de e-mail |
| `git status` mostra todos os arquivos modificados | Pasta git no OneDrive: o modo de arquivo muda de 644 para 755 | `git config core.filemode false` |
| `ats-scrapers não instalado` | Extra opcional | `pip install -e ".[ats]"` |
| Coleta lenta | Proposital: 3 s entre chamadas | Respeita o limite de 25/min da Adzuna. Não reduza |
| `429` da Adzuna | Passou de 250 chamadas no dia | Espere o dia virar. Cada termo de busca é uma chamada |

---

## Limites e cuidados

**Adzuna:** 25 requisições por minuto, 250 por dia, 2.500 por mês. Se um
dia você exibir esses dados em público, os termos pedem a atribuição
"Jobs by Adzuna" com link. Uso pessoal não se aplica.

**ATS dos empregadores:** endpoints públicos, sem autenticação. O
`min_interval` de 1,5 s existe por educação. Não paralelize.

**SEEK:** desligado. Ler `collectors/seek_v5.py` antes de ligar.

**O que o sistema nunca faz:** preencher formulário, enviar candidatura,
ou responder entrevista. É decisão de projeto, explicada no README.
