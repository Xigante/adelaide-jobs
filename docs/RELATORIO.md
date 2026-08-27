# Relatório do projeto

O que foi construído, o que foi validado de verdade, e o que ainda não foi.

Data: 27 de agosto de 2026.

---

## Resumo

Um pipeline pessoal de **descoberta** de vagas em Adelaide, para chegada
em setembro de 2026 com visto de estudante 500. Ele coleta de fontes
legítimas, deduplica, descarta o que não serve e ordena o resto por
aderência ao perfil.

Estado: **funcionando com dados reais.** 81 testes passando, primeira
coleta real feita, dois bugs de produção encontrados e corrigidos.

O que ele não faz, por decisão de projeto: preencher formulário e enviar
candidatura. A justificativa está no README com as fontes.

---

## O que foi validado de verdade

Separado do que é projeto no papel.

| Componente | Validado? | Como |
|---|---|---|
| Coleta da Adzuna | ✅ | Chamada real à API: 53 vagas de "kitchen hand" em Adelaide |
| Parsing dos anúncios | ✅ | 7 vagas reais processadas ponta a ponta |
| Extração de dimensões | ✅ | Ver o caso do Hunter and Barrel abaixo |
| Score e ordenação | ✅ | Fila real produzida e conferida à mão |
| Deduplicação | ✅ | Testes com a mesma vaga vinda de duas fontes; reingestão idempotente |
| Knockouts | ✅ | 81 testes, incluindo as três armadilhas conhecidas |
| Banco e persistência | ✅ | Depois de corrigir o bug do OneDrive |
| Export CSV | ✅ | Testado |
| Coletores de ATS | ⚠️ | Código escrito, **nunca executado contra a rede** |
| Coletor do SEEK v5 | ⚠️ | Escrito e desligado. Nunca executado |
| Export para Sheets | ⚠️ | Escrito, nunca executado — falta a service account |
| Coletor de e-mail (IMAP) | ❌ | Não implementado |

**A limitação honesta:** o ambiente onde o código foi escrito não alcança
`api.adzuna.com`, `seek.com.au` nem os hosts de ATS. A validação da
Adzuna foi feita pelo navegador do usuário. Os coletores de ATS
continuam sem nenhuma execução real — é a primeira coisa que o comando
`doctor` vai responder.

---

## A primeira coleta real

Sete vagas da Adzuna, processadas pelo pipeline:

```
score  vaga                                 empregador                       km
   87  Casual Housekeeper Housekeeping      Avani Adelaide Residences       0.7
   79  Kitchen Hand/Cook                    Fasta Pasta Gilles Plains       0.7
   78  Kitchen Hands - Production Kitchen   Vili's Family Bakery            0.7
   74  Kitchen Hand                         Pohkay Hyde Park                0.7
   74  Kitchen Hand                         Hola Amigos                     0.7
   72  Cleaner                              Workforce Extensions            2.2
   60  Kitchen Hand                         Hunter and Barrel               0.7
```

O resultado que importa é o último lugar. **Hunter and Barrel** é uma
vaga de kitchen hand no CBD — pelo título, indistinguível das outras.
O anúncio, porém, pede *"1 years of proven kitchen experience in a fast
paced, high volume environment"*. O extrator leu isso, marcou
`exp_req = YEARS_REQUIRED`, e a dimensão que pesa 25 derrubou a nota.

Do outro lado, **Avani** subiu por três motivos somados: *"no experience
necessary, full training provided"*, housekeeping é back-of-house (inglês
básico funciona), e fica a 700 m da Grenfell St.

Nenhum humano ordenaria sete anúncios assim em segundos, lendo o corpo de
cada um. É o valor do sistema numa frase.

---

## Decisões de arquitetura

### O extrator não calcula o número

A decisão mais importante. O extrator lê o anúncio e devolve
**categorias**; o score sai de `scoring.py`, em Python, a partir de pesos
num arquivo YAML.

Motivo prático: quando os pesos forem recalibrados com o resultado real
das candidaturas, isso vira um `git commit` — e reprocessar duas mil
vagas históricas vira um loop de segundos, em vez de duas mil chamadas de
API. É também o que permite trocar regex por LLM depois sem tocar em nada
além de uma classe.

### Coletores separam rede de parsing

Cada coletor tem `collect()` (rede) e `parse()` (puro). É por isso que
existem testes de parsing rodando contra fixture em disco, sem depender
de nenhum serviço externo.

E `safe_collect()` nunca levanta exceção: falha de uma fonte registra o
erro e o run continua com as outras.

### Dedup para no estágio fuzzy

Três estágios projetados, dois implementados: chave canônica exata e
fuzzy com blocking. Embeddings ficaram **deliberadamente de fora** — dois
kitchen hands em restaurantes *diferentes* do CBD são semanticamente
quase idênticos, e embedding sozinho funde vagas legítimas.

### A calibração é assimétrica de propósito

> Manter uma vaga ruim custa alguns tokens.
> Descartar por engano uma vaga boa custa uma oportunidade de emprego.

Todo knockout é de precisão alta e recall baixo. Na dúvida, deixa passar.

---

## Bugs encontrados

Quatro, todos achados rodando e não lendo.

**1. "Night Fill Team Member" virava `team_member`.** O dicionário de
sinônimos escolhia o match mais longo, e "team member" (11 caracteres) é
maior que "night fill" (10). Um turno noturno de supermercado — exatamente
o alvo do perfil — sairia do radar de back-of-house. Corrigido com duas
camadas: papéis específicos antes de genéricos.

**2. Arredondamento bancário do Python.** `round(80.5)` dá 80, mas
`round(65.5)` dá 66. Duas vagas equivalentes apareciam com um ponto de
diferença sem motivo visível. Trocado por meio-para-cima.

**3. SQLite não funciona dentro do OneDrive.** O banco ficava em
`data/jobs.db`, dentro do projeto. Com o projeto numa pasta sincronizada,
o SQLite falha com `disk I/O error` — o WAL precisa de memória
compartilhada que OneDrive, Dropbox e unidade de rede não oferecem. Este
teria quebrado a primeira execução real. O padrão passou para
`~/.adelaide-jobs/jobs.db`, com fallback de journal mode e uma exceção
que explica a causa em vez do erro cru do sqlite3.

**4. "night fill" devolve zero na Adzuna.** Testado contra a API. O termo
está em todo anúncio real de supermercado, mas o índice deles não casa a
expressão. Os termos de busca agora estão anotados com quantas vagas cada
um devolveu, e há uma nota dizendo que turno noturno tem que vir da
página de carreiras do empregador ou dos alertas de e-mail. Este bug é
uma evidência a favor da arquitetura multi-fonte: uma fonte só teria
deixado um segmento inteiro invisível.

---

## Fontes, e por que essas

| Fonte | Legitimidade | Estado |
|---|---|---|
| Adzuna API | API oficial, chave gratuita | ligada, validada |
| Workday (Bunnings, Hungry Jack's, Flinders) | endpoint público sem auth | ligada, não testada |
| SmartRecruiters (McDonald's, Guzman y Gomez) | API pública documentada | ligada, não testada |
| SEEK v5 | ⚠️ contra os termos de uso | **desligada** |
| Alertas de e-mail (IMAP) | seus próprios dados | não implementada |

Os três grandes agregadores australianos estão fechados: o SEEK devolve
403 até no próprio `robots.txt`, e o `robots.txt` do Indeed nomeia e
bloqueia crawlers de IA. A saída projetada é usar os **alertas de e-mail
nativos** deles: mesma informação, entregue pela própria plataforma, sem
tocar no site. É a peça de maior volume que falta construir.

---

## O que falta

Em ordem de valor por esforço:

1. **Coletor de alertas de e-mail (IMAP).** Maior volume, menor risco, e
   não existe pronto em lugar nenhum — foram procurados repositórios e
   não há parser de alerta do SEEK público. A base é `imap_tools` com
   IDLE, e o padrão que sobrevive a redesenho de template é extrair o ID
   da vaga da URL por regex, não parsear o layout.
2. **Rodar os coletores de ATS pela primeira vez.** O `doctor` diz se a
   rede alcança.
3. **Confirmar duas coisas que não podem ser inferidas:** o calendário
   oficial de férias do ILSC (ELICOS não tem as férias longas de
   universidade) e o horário das aulas — manhã ou tarde trava turnos
   inteiros e o bloco de disponibilidade do currículo.
4. **Tempo real de viagem via GTFS do Adelaide Metro**, incluindo o
   trajeto de **volta** no horário de término do turno. Hoje é distância
   em linha reta, o que superestima night fill em subúrbio distante.
5. **Log de resultado por candidatura** e o teste de monotonicidade do
   score. É o que transforma os pesos de chute em evidência.
6. **Conjunto de teste de ~200 anúncios reais rotulados à mão** antes de
   confiar plenamente nos regex de knockout. Os 81 testes cobrem a
   lógica; não substituem dados reais.

---

## Como continuar

- Operação do dia a dia: **[docs/OPERACAO.md](OPERACAO.md)**
- Rodar sem o Claude, trocar de IA, automatizar: **[docs/AUTONOMIA.md](AUTONOMIA.md)**
- Visão geral e as decisões: **[README.md](../README.md)**
