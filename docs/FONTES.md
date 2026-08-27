# De onde vêm as vagas

Pesquisa de 27/08/2026, feita por sete agentes em paralelo, cada um com
uma pergunta diferente. Tudo aqui foi verificado no site ou na
documentação — quando não deu para verificar, está escrito que não deu.

A pergunta que originou isto: *"será que a Adzuna é o único canal?"*

Não é. Mas quase tudo que parece uma fonte não é uma fonte.

---

## O resumo, se você só ler uma coisa

Três descobertas mudaram o programa hoje:

1. **`night fill` devolvia zero porque na Austrália é `nightfill`, uma
   palavra só.** O mesmo tipo de erro estava custando metade do mercado
   em outras cinco funções. O dicionário está no fim deste documento.
2. **`dishwasher` devolve zero.** Na Austrália a palavra é a *máquina*.
   Quem lava louça é `kitchen hand`, `kitchen porter`, `pot wash` ou
   `glassie`.
3. **`storeperson` é o termo nº 1 de armazém** e não tem equivalente
   óbvio em inglês americano. Sem ele, metade da logística some.

E uma descoberta que evita perder tempo: **defesa é o maior setor de
tecnologia de Adelaide (AUKUS, estaleiro de Osborne) e é inalcançável
com visto de estudante** — o clearance da AGSVA exige cidadania
australiana, sem exceção. O programa agora bloqueia essas vagas em vez
de te mostrar oportunidade que não existe.

---

## O que está ligado hoje

| Fonte | O que é | Volume | Link é do empregador? |
|---|---|---|---|
| **Adzuna** | API oficial, chave grátis | ~2.400/varredura | Não (agregador) |
| **ATS diretos** | Workday e SmartRecruiters dos empregadores | dezenas | **Sim** |
| **SA Health (PageUp)** | Portal de carreiras da saúde pública SA | **~625** | **Sim** |

### Adzuna — a base
API documentada, chave gratuita, 250 requisições por dia. Varre oito
categorias inteiras num raio de 25 km e mais 41 termos específicos.
Custo por varredura: cerca de 130 requisições — dá para rodar duas vezes
ao dia.

Limitação conhecida: a descrição vem truncada e o link passa pelo
redirect da Adzuna. Por isso o programa prefere o link do empregador
sempre que consegue um (veja a ordem das fontes no rodapé do relatório).

### ATS diretos — os melhores links
São os próprios empregadores publicando, sem intermediário. Ligados:
Bunnings, Hungry Jack's, Flinders University (Workday), McDonald's
Australia, Guzman y Gomez e **ALDI Australia** (SmartRecruiters,
`ALDIStores`) — adicionado hoje.

O endpoint do Workday da Flinders foi verificado e responde JSON limpo:

    POST https://flinders.wd3.myworkdayjobs.com/wday/cxs/flinders/flinders_employment/jobs
    {"appliedFacets":{},"limit":20,"offset":0,"searchText":""}

O mesmo coletor serve qualquer Workday. Para descobrir o de um
empregador novo, procure no HTML da página de carreiras dele o padrão
`<tenant>.wd<N>.myworkdayjobs.com/<site>`.

### SA Health — a maior fonte de Adelaide, adicionada hoje
~625 vagas ativas, praticamente todas na Grande Adelaide. Hospital
emprega muito back of house: Hotel Services Assistant, Food Services
Assistant, Cleaner, Ward Assistant.

Duas limitações, ambas medidas no navegador, não supostas:

- A **listagem** é HTML e pagina com `?page=N`, 24 por página. Funciona.
- A **página de detalhe** responde HTTP 202 com corpo vazio para quem
  não é navegador. Ou seja: temos título, número, local e prazo, mas
  **não a descrição**. Essas vagas pontuam pelo título e ficam no meio
  da tabela. Clique em "Candidatar-se" para ler o anúncio.
- `?search-keyword=` não filtra (devolve zero). Só a varredura por
  página funciona.

---

## As próximas, por ordem de retorno

Nenhuma delas está implementada. Estão aqui com endpoint e volume para
que implementar seja uma tarde de trabalho, não uma nova pesquisa.

| Fonte | Como coletar | Volume Adelaide | Esforço |
|---|---|---|---|
| **CareerOne** | `careerone.com.au/{termo}-jobs/in-adelaide-sa?page=N`, HTML | cleaner 66 · retail 144 · warehouse 52 · housekeeping 35 | baixo |
| **Woolworths** (Avature) | `careers.woolworthsgroup.com.au/en_GB/apply/SearchJobs/?jobOffset=N` | 999+ nacional, filtrar SA | médio |
| **Drakes** (Expr3ss!) | `drakesupermarkets.expr3ss.com` — rede local de Adelaide | ~90, maioria SA | médio |
| **Student Job Board** | `studentjobboard.com.au/jobs/hospitality-jobs/adelaide/` | **179 casuais** | médio |
| **iworkfor.sa.gov.au** | Governo SA, robots totalmente liberado | 877 (≈450 metro) | alto |
| **Calvary / Southern Cross Care** (PageUp novo) | `/jobs/search?page=N` | 221 + 36 | baixo |
| **Adelaide Venue Management** | `adelaideconventioncentre.jobs.subscribe-hr.com` | 5–20, eventos | médio |
| **Gumtree Jobs** | `/s-jobs/adelaide/{cat}/...` — robots permite | 47 em limpeza | médio |

Notas que importam:

- **iworkfor.sa.gov.au** é a maior fonte concentrada de Adelaide e o
  robots.txt não proíbe nada (`Crawl-delay: 2`). O bloqueio é técnico: a
  paginação é POST de formulário, não query string. Precisa de uma
  sessão no navegador para descobrir o corpo do POST, uma vez só.
- **Coles** usa Phenom e o endpoint é POST com corpo grande e frágil.
  Deixe para depois do Woolworths.
- **Barcats** e **Adelaide Oval** são SPA pura: só com navegador
  headless.

---

## O que NÃO vale a pena — e por quê

Isto vale tanto quanto a lista de cima. Cada linha aqui é um dia que
você não vai perder.

| Descartada | Motivo |
|---|---|
| **Google Jobs / SerpApi** | O Google **não serve** o recurso na Austrália. A lista de 104 países do SerpApi pula de American Samoa para Áustria. Nenhum fornecedor pode cobrir o que o Google não publica. |
| **Indeed** | A Publisher API foi descontinuada. O que sobrou (Job Sync) serve para *publicar* vagas, não buscar. O robots.txt bloqueia ClaudeBot, GPTBot e CCBot por nome. |
| **SEEK** | Sem API pública, 403 para cliente não-navegador, e os termos proíbem acesso automatizado. Use os **alertas por e-mail** dele. |
| **Jora** | É da SEEK e replica a política. |
| **The Muse** | Diz cobrir Adelaide. Medido: **8 vagas reais**. O contador de 6.345 inclui todas as remotas globais. |
| **Jobicy, Arbeitnow, RemoteOK, Remotive** | Só remoto, e majoritariamente EUA/Alemanha. Zero em Adelaide. |
| **Jooble** | 500 requisições **vitalícias** por chave. Inviável para coleta recorrente. |
| **Workforce Australia** | Sem API pública, robots bloqueia a busca. |
| **data.gov.au** | Só estatística agregada mensal. Nenhuma vaga individual. |
| **Sidekicker** | Marketplace fechado. **Mas vale se cadastrar como pessoa** — é a via mais rápida para turno casual sem experiência local. |
| **Careerjet** | Único agregador AU-nativo com API, mas exige `affid` de conta Publisher (aprovação) e o link passa por rastreador. Talvez, se pedir o affid antes. |
| **JSearch (RapidAPI)** | Cobre AU e dá link direto do empregador, mas **200 requisições/mês** grátis ≈ 6 por dia. Serve como consulta cirúrgica, não varredura. |

---

## O canal que não é um coletor: alertas por e-mail

O SEEK é o maior mercado de Adelaide e não pode ser raspado. Mas nada
impede você de **assinar os alertas dele** e o programa ler a sua caixa
de entrada — são e-mails que você pediu para receber.

O código já está no repo (`email_alerts` em `config/sources.yaml`),
desligado. Para ligar:

1. Crie uma conta Gmail só para isso, por exemplo
   `vagas.adelaide.2026@gmail.com`.
2. Ative a verificação em duas etapas em
   <https://myaccount.google.com/security>.
3. Vá em <https://myaccount.google.com/apppasswords>, crie uma senha de
   app chamada `coletor-vagas` e copie o código de 16 caracteres.
4. Ponha no `.env`: `IMAP_USER` e `IMAP_PASSWORD` (a senha de app, não a
   da conta).
5. Assine os alertas diários de SEEK, Indeed AU, LinkedIn e
   iworkfor.sa.gov.au usando esse e-mail.

Volume esperado com 8 alertas diários: 80 a 200 cartões brutos, que
depois da deduplicação viram **25 a 60 vagas únicas por dia**, das quais
10 a 30 realmente novas.

Dica de organização: crie um filtro no Gmail por remetente que jogue
cada alerta num rótulo `Vagas/SEEK`, `Vagas/Indeed` etc. Rótulo do Gmail
é pasta IMAP — o coletor lê só aquela pasta e ignora o resto da caixa.

Prefira **muitos alertas estreitos a poucos amplos**: cada e-mail mostra
só os primeiros N resultados, e o resto você perde sem saber.

---

## Programador, games e design em Adelaide

Você pediu que essas vagas aparecessem. Elas aparecem — as categorias
`it-jobs` e `creative-design-jobs` estão ligadas. Mas o número honesto
importa mais que a esperança:

- O maior quadro de vagas de games do mundo (Grackle HQ) mostrava **1
  vaga em Adelaide** e 15 na Austrália inteira, 13 delas da Riot em
  Sydney.
- A SAFC conta 35+ estúdios em SA, mas a maioria é uma ou duas pessoas.
  Empregadores de verdade com folha de pagamento: **dois ou três**.
- **Tantalus South (Keywords Studios)** é o maior — 21 pessoas, meta de
  50. Abriu em 2023 atraído pelo incentivo fiscal do estado.
- **Mighty Kingdom**, que era a âncora do setor, **demitiu 40% do quadro
  em fevereiro de 2025** e hoje só aceita "expressão de interesse".
- **Team Cherry** (Hollow Knight) é de Adelaide, tem ~3 pessoas e nunca
  contrata.

Espere **5 a 15 vagas de games por ano na cidade inteira**.

**O sinal antecedente que vale mais que qualquer quadro de vagas:**
quando a SAFC anuncia os beneficiários do Digital Games Fund
(<https://www.safilm.com.au/latest-news/>), aqueles estúdios contratam
nos um a três meses seguintes. Em outubro de 2025 foram $500 mil
divididos entre 11 projetos.

Dois feeds RSS de games que funcionam sem chave, se um dia quiser:
`workwithindies.com/careers/rss.xml` e `remotegamejobs.com/feed.rss`.
Volume australiano: baixíssimo, mas custa nada.

**GradConnection** (`au.gradconnection.com/jobs/adelaide/`) tem 243
vagas em Adelaide e é o **único quadro que marca "Accepts
International"** — o inverso exato do problema de clearance.

E o enquadramento honesto: com 48h por quinzena, a via realista para
games e design em Adelaide não é quadro de vagas, é rede local — SAGE,
meetups, portfólio público. O programa existe para você não perder a
vaga rara, não como estratégia principal.

---

## Dicionário: como os australianos escrevem cada função

Esta é a parte mais útil do documento. Cada termo aqui apareceu em
anúncio real de Adelaide. Os que estão em **negrito** são os de maior
rendimento.

**Reposição noturna de supermercado**
`nightfill` (uma palavra!) · **`Store Team Member`** (Woolworths) ·
`Nightfill Team Member` · `Night Filler` · `Grocery Team Member` ·
**`Casual Store Assistant`** (Drakes, termo local) · `Replenishment` ·
`Shelf Stacker` · `Ambient Nightfill` · `Online Pick Packer`

**Cozinha**
**`Kitchen Hand`** · `Kitchenhand` · `Kitchen Assistant` ·
`Kitchen Attendant` · `Kitchen Porter` · `KP` · **`Kitchen Steward`** ·
`Stewarding` · `Pot Wash` · `Dishy` · `Food Services Assistant` ·
`Catering Assistant` · `Kitchen All Rounder` · `Back of House` / `BOH`

**Lavar louça** — nunca busque `dishwasher`, é a máquina
`Kitchen Hand` · `Kitchen Porter` · `Pot Wash` · `Glass Collector` ·
`Glassie`

**Limpeza**
**`Cleaner`** · `Commercial Cleaner` · `Contract Cleaner` ·
`Office Cleaner` · `Hotel Services Assistant` · `Public Area Cleaner` ·
`General Service Assistant` · `Environmental Services` ·
`Cleaning and Trolley Collection Team Member`

**Quarto de hotel**
**`Room Attendant`** · `Housekeeping Attendant` · `Houseperson` ·
`Accommodation Cleaner` · `Public Area Attendant` · `Linen Attendant` ·
`Laundry Attendant` · `Uniform Attendant`

**Salão e eventos**
**`Food & Beverage Attendant`** (o termo dominante — `food runner` é
raro no título) · `F&B Attendant` · `Wait Staff` · `Front of House` /
`FOH` · `Cafe All Rounder` · `Banquet Attendant` · `Function Staff` ·
`Event Crew` · `Glassie`

**Armazém**
**`Storeperson`** (o nº 1, sem equivalente americano) ·
`Warehouse Operator` · `Pick Packer` · `Order Picker` · `Voice Picker` ·
`Freight Handler` · `Freight Sorter` · `Process Worker` ·
`Factory Hand` · `General Labourer` · `Yard Person` · `Despatch Officer`

**Modificadores que valem por si** — são as palavras que o anúncio usa
quando aceita gente sem experiência local
**`No Experience`** · **`Immediate Start`** · `Casual` · `Entry Level` ·
`Expression of Interest` · `Multiple Positions` ·
`After School and Weekend Casuals`

**Níveis, no vocabulário australiano**
`Graduate` (= recém-formado, não pós-graduação) · `Cadet` /
`Cadetship` · `Vacationer` (estágio de férias — não aparece buscando
"intern") · `Casual` (o regime que melhor encaixa em 48h/quinzena)

**Armadilha:** `Gaming` sozinho, na Austrália, quer dizer **cassino e
caça-níquel** (`Gaming Attendant`, `pokies`, `Wagering`, `Keno`). Para
jogos digitais o termo é `Game Development` ou `Video Game`. O programa
já sabe disso — `Gaming Attendant` não conta como ponte de carreira.

**Ortografia britânica:** `Human-Centred Design` com *-tred*. Buscar
"-tered" perde resultados.

---

## Só para humano, não para robô

Coisas que valem o seu tempo mesmo sem coletor:

- **StudyAdelaide Job Shop** — <https://studyadelaide.com/jobshop>.
  Curadoria oficial do governo de SA **para estudante internacional**.
  Empregadores listados: Adelaide Oval, Adelaide Venue Management, AHS
  Hospitality, Cater Care, ibis, Pullman, Rydges Pit Lane, National Wine
  Centre, SkyCity, Drakes, McDonald's, FedEx. Candidatura direta.
- **Sidekicker** — <https://sidekicker.com/au>. Turnos casuais por app.
  Precisa de cadastro e aprovação de perfil, e por isso não é coletável
  — mas é a via mais rápida para o primeiro turno.
- **Pinnacle People** — agência de eventos, ~42 vagas em Adelaide.
  Entrar no "talent pool" rende turno recorrente.
- **Adelaide Central Market** — cada banca contrata direto, não há
  bolsa de vagas. Currículo impresso, de terça a sábado de manhã.
