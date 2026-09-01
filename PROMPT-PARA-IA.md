# Prompt para uma IA ler o relatório

**Como usar:** abra qualquer IA, cole o texto entre as linhas `---` e
anexe junto o arquivo que quer analisar:

- `exports/fila.csv` — a fila de vagas, é o melhor para analisar
- `exports/vagas.html` — o mesmo, mas para ler no navegador
- `exports/empregadores.csv` — o cadastro de empresas
- `material/Trabalho_Adelaide_CONSOLIDADO_*.html` — o material curado

Se a IA tiver acesso à pasta (Claude Code, Cursor), não precisa colar
nada: ela lê o `CLAUDE.md` sozinha.

---

Você vai analisar um relatório de vagas de emprego gerado por um
programa chamado `adelaide-jobs`. Antes de responder qualquer coisa,
leia estas restrições — elas decidem tudo.

## Quem é a pessoa

Pedro, brasileiro, chega em Adelaide (South Australia) em **24/09/2026**.

| | |
|---|---|
| Visto | Student 500, condição 8105 |
| Limite de trabalho | **48 h por quinzena** durante as aulas (o programa usa 44 como teto seguro) |
| Inglês | **A2** — entende o básico, não sustenta atendimento ao público |
| Carteira de motorista australiana | **não tem** |
| Carro | **não tem** — tudo a pé, ônibus ou trem |
| Escola | ILSC Adelaide, 115 Grenfell St, Adelaide CBD |
| Experiência | 3 anos com **dados e escritório**. Zero em hospitalidade, varejo, armazém ou limpeza |

O objetivo primário é **renda rápida em trabalho de entrada**. O
secundário é **escritório e dados**, que é a formação dele. Não é
recrutador, não é chef, não é enfermeiro.

## O que a nota significa

De 0 a 100. Ela responde **"o quanto esta vaga cabe nas restrições
dele"** — não responde "qual a chance de ele ser contratado", e não é
uma nota de qualidade da vaga.

Sai da soma de oito dimensões, com estes pesos:

| dimensão | peso | o que mede |
|---|---:|---|
| `experience_barrier` | 25 | quanta experiência o anúncio exige |
| `english_load` | 20 | quanto inglês o trabalho exige |
| `visa_hours_fit` | 15 | se as horas cabem no visto |
| `commute` | 12 | distância a pé/transporte até o ILSC |
| `shift_fit` | 10 | se o turno bate com as aulas |
| `certification_barrier` | 8 | RSA, White Card, police check |
| `employer_pattern` | 6 | rede grande contrata mais e treina |
| `career_bridge` | 4 | se aproxima de trabalho com dados |

Faixas: **A+** 85+ · **A** 78–84 · **A-** 70–77 · **B+** 62–69 ·
**B** 55–61 · **C** 40–54 · **D** abaixo de 40 · **X** bloqueada.

Uma vaga **X** foi descartada por um knockout, e o motivo está escrito
na linha: só full-time, exige direito de trabalho irrestrito, exige
2+ anos como requisito duro, título de chefia, ou exige security
clearance.

## As três coisas que você NÃO pode concluir

**1. Ausência de um requisito não é ausência do requisito.**
A fonte principal (Adzuna) devolve a descrição **cortada em 500
caracteres**. Requisito costuma estar no fim do anúncio, depois do
corte. Medido: **73% das vagas ficam com `eng_contact = UNKNOWN`**, não
porque o inglês não importa, mas porque o texto acabou antes. Então:
nunca diga "esta vaga não exige experiência" — diga "o trecho
disponível não menciona experiência".

**2. Nota alta não é vaga boa, é vaga compatível.**
Uma vaga de limpeza com 87 e uma de análise de dados com 72 não estão
dizendo que limpar é melhor. Estão dizendo que, com A2 e sem
experiência local, a de limpeza tem menos barreiras. Se ele perguntar
"o que eu faço da vida", a nota não responde isso.

**3. O mapa é aproximado, o endereço é exato.**
No material, o pino pode cair na quadra vizinha. O endereço escrito e o
link do Google Maps são confiáveis. Nunca invente endereço nem horário
de funcionamento: se não estiver escrito, escreva "não confirmado".

## O que descartar de saída

- Vagas que exigem **carro próprio** ou **carteira australiana** —
  entregador de aplicativo, motorista, muitas de apoio domiciliar.
- **Enfermagem e área clínica** — exigem registro no AHPRA, que ele não
  tem e não vai ter.
- Qualquer coisa **full-time**: estoura o visto e é ilegal para ele.

## O que é realmente útil você fazer

1. **Agrupar e achar padrão.** "Onze das trinta primeiras são da mesma
   agência de limpeza" vale mais do que repetir a lista ordenada.
2. **Achar a contradição.** Vaga com nota alta cujo texto disponível
   sugere um requisito escondido. Diga qual e por quê.
3. **Separar o que dá para hoje do que dá para depois.** Ele chega sem
   experiência local; em três meses terá referência australiana, e aí
   as vagas de escritório passam a ser realistas.
4. **Dizer o que falta.** Se um certificado barato (RSA, White Card,
   police check) abre trinta vagas, isso é a informação mais valiosa
   do relatório.
5. **Ser específico com nome e número.** "Cinco vagas da ISS em
   Adelaide CBD, todas casuais, nota entre 79 e 83" — não "há boas
   oportunidades em limpeza".

## Como responder

Português do Brasil, direto, sem entusiasmo de vendedor. Diga o número
quando tiver o número. Quando não tiver certeza, diga que não tem —
ele prefere isso a uma resposta bonita e errada. Não repita a tabela
inteira de volta: ele já tem a tabela, o que ele não tem é a leitura.
