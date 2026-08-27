# Rodar sem o Claude

Este projeto foi construído numa conversa com o Claude. Este documento
existe para que isso deixe de importar: como operar sozinho, como plugar
outra IA, e o que ainda depende de gente.

---

## O estado atual: já é independente

**A v1 não usa IA nenhuma em tempo de execução.** O `RuleExtractor` é
regex; o scorer é aritmética em Python. Não há chamada a modelo, não há
chave de LLM, não há custo por vaga.

Ou seja: você já pode rodar `adelaide-jobs collect` para sempre sem
falar com nenhum assistente. O que uma IA acrescenta é qualidade de
leitura de anúncio ambíguo — não é requisito.

---

## O que foi feito por julgamento, e não está no código

Sendo honesto sobre o que você herda:

| Decisão | Onde está | Como refazer sozinho |
|---|---|---|
| Quais fontes são legítimas | `config/sources.yaml` + `collectors/` | Ler o `robots.txt` e os termos de uso antes de adicionar fonte |
| Os oito pesos do score | `profile.yaml` → `scoring.weights` | São um chute informado. A seção "Calibrar com dados" abaixo mostra como substituí-los por evidência |
| Os termos de busca | `sources.yaml` → `queries` | Testar cada um contra a API e anotar quantas vagas devolveu |
| Os knockouts e as três armadilhas | `filters.py`, `extract.py` | Os testes em `tests/` documentam cada armadilha com um caso |
| Não automatizar candidatura | README, seção "O que ele não faz" | A justificativa está escrita lá com as fontes |

Nada disso é mágico. Tudo está em arquivo de texto versionado, com o
raciocínio em comentário ao lado.

---

## Trocar a camada de inteligência

O ponto de troca é uma coisa só: o **`Extractor`**.

```python
# src/adelaide_jobs/extract.py
class Extractor(Protocol):
    name: str
    def extract(self, job: Job) -> Dimensions: ...
```

Qualquer objeto com esses dois membros serve. O `Pipeline` aceita um no
construtor:

```python
pipeline = Pipeline(cfg, db, extractor=MeuExtrator())
```

**Por que só isso basta:** o extrator devolve `Dimensions` — categorias,
não notas. Quem calcula o score é `scoring.py`, em Python. Trocar o
extrator não mexe no score, no dedup, no banco nem na CLI.

### Os campos que o extrator precisa preencher

```python
Dimensions(
    exp_req        = "NONE_REQUIRED",   # NOT_STATED | SOME_PREFERRED | SOME_REQUIRED | YEARS_REQUIRED
    exp_years      = None,              # int, quando YEARS_REQUIRED
    eng_contact    = "BOH_MINIMAL",     # LOW | MEDIUM | HIGH | UNKNOWN
    emp_type       = "CASUAL",          # PART_TIME | FULL_TIME | MIXED | NOT_STATED
    hours_pattern  = "FLEXIBLE_LOW",    # MODERATE | NEAR_FULL_TIME | NOT_STATED
    shift_window   = "OVERNIGHT",       # EARLY_MORNING | DAYTIME | EVENING | WEEKEND | ROTATING | NOT_STATED
    au_licence     = "NOT_MENTIONED",   # DESIRABLE | ESSENTIAL
    rsa            = "NOT_MENTIONED",   # idem
    white_card     = "NOT_MENTIONED",   # idem
    food_handling  = "NOT_MENTIONED",   # idem
    work_rights    = "NOT_STATED",      # STUDENT_OK | FULL_RIGHTS_REQUIRED
    employer_kind  = "LARGE_CHAIN",     # AGENCY | INDEPENDENT | INSTITUTION | UNKNOWN
    career_bridge  = False,
    distance_km    = 3.1,               # calcule com geo.distance_from_school
    extractor      = "meu-modelo",      # fica gravado em cada vaga
)
```

Regra que vale para qualquer modelo: **na dúvida entre `ESSENTIAL` e
`DESIRABLE`, escolha `DESIRABLE`.** Falso negativo em knockout custa
alguns tokens; falso positivo custa uma oportunidade de emprego.

### Exemplo: Ollama, rodando no seu computador

Sem chave, sem custo, sem mandar dado para fora. Instale de
<https://ollama.com>, rode `ollama pull llama3.2`, e crie
`src/adelaide_jobs/extract_ollama.py`:

```python
import json
import httpx
from .extract import RuleExtractor
from .geo import distance_from_school, guess_coords
from .models import Dimensions, Job

PROMPT = """You classify Australian job ads. Output ONLY a JSON object.

Candidate: international student in Adelaide, student visa 500 (max 48h
per fortnight), English CEFR A2, ZERO experience in hospitality/retail,
no car, no certifications.

Fields and allowed values:
  exp_req: NONE_REQUIRED|NOT_STATED|SOME_PREFERRED|SOME_REQUIRED|YEARS_REQUIRED
  exp_years: integer or null
  eng_contact: BOH_MINIMAL|LOW|MEDIUM|HIGH|UNKNOWN
  emp_type: CASUAL|PART_TIME|FULL_TIME|MIXED|NOT_STATED
  hours_pattern: FLEXIBLE_LOW|MODERATE|NEAR_FULL_TIME|NOT_STATED
  shift_window: EARLY_MORNING|DAYTIME|EVENING|OVERNIGHT|WEEKEND|ROTATING|NOT_STATED
  au_licence, rsa, white_card, food_handling: NOT_MENTIONED|DESIRABLE|ESSENTIAL
  work_rights: STUDENT_OK|FULL_RIGHTS_REQUIRED|NOT_STATED
  employer_kind: LARGE_CHAIN|AGENCY|INDEPENDENT|INSTITUTION|UNKNOWN
  career_bridge: true|false

Rules:
1. Classify only from what the ad states. Silence means NOT_STATED.
2. "essential"/"must have" = ESSENTIAL. "desirable"/"preferred" = DESIRABLE.
   When ambiguous, choose the softer value.
3. "Casual, part-time and full-time available" is MIXED, not FULL_TIME.

AD:
"""


class OllamaExtractor:
    name = "ollama"

    def __init__(self, model: str = "llama3.2", url: str = "http://localhost:11434"):
        self.model, self.url = model, url
        self._fallback = RuleExtractor()

    def extract(self, job: Job) -> Dimensions:
        try:
            r = httpx.post(
                f"{self.url}/api/generate",
                json={"model": self.model, "format": "json", "stream": False,
                      "options": {"temperature": 0},
                      "prompt": PROMPT + job.searchable_text[:4000]},
                timeout=120,
            )
            r.raise_for_status()
            data = json.loads(r.json()["response"])
        except Exception:
            # Modelo fora do ar não pode derrubar o run.
            return self._fallback.extract(job)

        lat, lon = job.lat, job.lon
        if lat is None and (g := guess_coords(job.suburb)):
            lat, lon = g

        campos = {f: data[f] for f in Dimensions.__slots__ if f in data}
        campos["distance_km"] = distance_from_school(lat, lon)   # sempre em código
        campos["extractor"] = self.name
        return Dimensions(**campos)
```

E use:

```python
from adelaide_jobs.extract_ollama import OllamaExtractor
pipeline = Pipeline(cfg, db, extractor=OllamaExtractor())
```

Três detalhes que valem copiar em qualquer implementação:

1. **Fallback para o `RuleExtractor`** quando o modelo falha. O run nunca
   pode parar por causa de uma vaga.
2. **`distance_km` é calculada em código**, nunca pedida ao modelo.
   Distância é aritmética, não opinião.
3. **`temperature 0`**. Você quer o mesmo resultado no mesmo anúncio.

### Exemplo: Gemini, OpenAI ou qualquer API

Mesma estrutura, trocando a chamada HTTP. Duas coisas a saber:

- Use **saída estruturada** (`response_schema` no Gemini, `json_schema`
  no OpenAI) em vez de pedir JSON no texto. O modelo passa a não
  conseguir devolver campo inválido.
- **Mande as vagas em lote**, 10 a 20 por chamada, em vez de uma por
  vaga. Com o filtro deterministico na frente, o custo mensal fica na
  casa de poucos dólares — mas o número de chamadas é o que esbarra em
  rate limit.
- Se for tier gratuito, saiba que costuma haver uso dos dados para
  treino. Isso é indiferente para anúncio público, e não é indiferente
  se um dia você mandar seu currículo no prompt.

### Comparar extratores antes de confiar

O `extractor` fica gravado em cada vaga, então dá para medir:

```bash
adelaide-jobs score --rescore    # roda com o extrator configurado
adelaide-jobs export --csv exports/com-regex.csv
# troque o extrator, repita
adelaide-jobs score --rescore
adelaide-jobs export --csv exports/com-llm.csv
# compare as duas planilhas: onde discordam é onde vale olhar
```

---

## Automatizar

### Windows — Agendador de Tarefas

Crie `coletar.bat` na pasta do projeto:

```bat
@echo off
call "%USERPROFILE%\.venvs\adelaide-jobs\Scripts\activate"
cd /d "%~dp0"
adelaide-jobs collect
adelaide-jobs export
```

Agendador de Tarefas → Criar Tarefa Básica → diária, 8h → aponte para
esse `.bat`. Marque **"Executar assim que possível após perda de
inicialização"**, senão ele pula os dias em que o PC estava desligado.

### Linux e macOS — cron

```cron
0 8 * * *  cd ~/adelaide-jobs && ~/.venvs/adelaide-jobs/bin/adelaide-jobs collect && ~/.venvs/adelaide-jobs/bin/adelaide-jobs export
```

Rodar todo dia é seguro: a deduplicação garante que reprocessar não cria
vaga repetida.

---

## Calibrar os pesos com dados, não com opinião

Os oito pesos de hoje são um chute informado. Depois de umas 40
candidaturas, eles podem virar evidência.

Registre o resultado de cada candidatura no banco:

```sql
UPDATE job_cluster
SET applied_at = date('now'), outcome = 'NO_RESPONSE'
WHERE cluster_id = 'b0585ee9...';
```

Valores úteis: `NO_RESPONSE`, `TRIAL_SHIFT`, `INTERVIEW`, `OFFER`.
Em hospitality australiana o processo comum não é entrevista — é
*"come in Thursday at 5 and we'll see how you go"*. Por isso
`TRIAL_SHIFT` merece ser um estágio próprio, não sinônimo de entrevista.

Depois, o teste que valida o sistema inteiro:

```sql
SELECT CASE WHEN score >= 85 THEN '85-100'
            WHEN score >= 70 THEN '70-84'
            WHEN score >= 55 THEN '55-69'
            ELSE '<55' END AS faixa,
       COUNT(*) AS n,
       ROUND(AVG(outcome != 'NO_RESPONSE') * 100, 1) AS taxa_resposta
FROM job_cluster
WHERE outcome IS NOT NULL
GROUP BY 1 ORDER BY 1 DESC;
```

**A taxa de resposta tem que subir junto com a faixa.** Se `70-84`
responder melhor que `85-100`, o score está invertido em alguma dimensão
e não adianta ajustar mais nada antes de descobrir qual.

Um cuidado que quase todo mundo esquece: você só observa resultado onde
se candidatou. Se só aplicar em score alto, nunca vai ter dado sobre a
faixa média, e o sistema vai se auto-confirmar para sempre. Reserve umas
duas ou três candidaturas por semana para vagas de score médio, só para
medir.

---

## Pedir ajuda a outra IA

Se um dia você quiser que outro assistente mexa nisto, cole o contexto:

> Este é um pipeline pessoal em Python de descoberta de vagas em
> Adelaide, Austrália, para um estudante com visto 500 (máximo 48h por
> quinzena), inglês A2, sem experiência em hospitality e sem carro.
>
> Arquitetura: coletores → SQLite → extrator (texto vira categorias) →
> scorer (aritmética em Python) → CSV/Sheets.
>
> A decisão de arquitetura mais importante: **o extrator devolve
> categorias, nunca notas.** O score é calculado em `scoring.py`, em
> Python, a partir de pesos em `config/profile.yaml`. Isso é o que torna
> a recalibração um commit em vez de um reprojeto, e é o que permite
> trocar regex por LLM sem tocar no resto.
>
> Leia nesta ordem: `README.md`, `docs/OPERACAO.md`,
> `src/adelaide_jobs/models.py`, `pipeline.py`, `extract.py`,
> `scoring.py`. Os testes em `tests/` documentam as armadilhas reais que
> já foram encontradas — leia antes de "simplificar" qualquer regex.
>
> O sistema deliberadamente não preenche formulário nem envia
> candidatura. A justificativa está no README e não é negociável sem
> reler as fontes citadas lá.

---

## O que nenhuma automação resolve

Vale ter isso escrito, porque é onde o resultado realmente é decidido:

- **Café e padaria de bairro contratam presencialmente.** Currículo
  impresso, entre 14h e 16h, entre os serviços. Esse canal não aparece em
  job board nenhum, e é onde a concorrência é ordens de grandeza menor.
- **RSA, White Card, Food Handling** desbloqueiam mais vagas que qualquer
  ajuste de peso.
- **Referência australiana** é o gargalo real dos primeiros meses.
  Voluntariado resolve em três semanas.
- **Rede grande avalia por processo próprio** — assessment do Coles,
  entrevista por chat do Bunnings e Kmart. O pipeline te leva até a
  porta; entrar é com você.

O sistema existe para devolver o tempo que essas coisas exigem. Não para
substituí-las.
