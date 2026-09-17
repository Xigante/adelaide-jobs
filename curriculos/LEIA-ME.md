# Currículos

Quatro modelos de referência, um por área. **Eles não são para enviar como
estão** — são a base que você edita para cada vaga.

Cada um vem em dois formatos: o `.docx` para editar no Word, e o `.pdf` para
ver como fica e para imprimir. Depois de editar o `.docx`, gere o PDF de novo
(no Word: *Arquivo → Salvar como → PDF*). **Empregador recebe PDF**, nunca
`.docx` — o Word de outra pessoa reposiciona tudo.

## Qual mandar para qual vaga

| Se a vaga é | Use |
|---|---|
| Cleaner, Storeperson, Warehouse, Night Fill, Trolley Collector | `CV-1-Operacoes` |
| Kitchen Hand, Dishwasher, Food Prep, back of house de café | `CV-2-Hospitalidade` |
| Administration, Data Entry, Reception, Office Assistant | `CV-3-Escritorio` |
| Data Assistant, Reporting, Automation, empresas de tecnologia | `CV-4-Dados-e-Tecnologia` |

**A regra que mais importa: não mande o CV de dados para vaga de cozinha ou
limpeza.** Empregador de casual na Austrália lê "engenheiro de dados se
candidatando para lavar louça" como "vai embora em três meses", e isso é um
dos motivos mais comuns de recusa. O CV-1 e o CV-2 resolvem isso dizendo a
verdade de cara — que você nunca trabalhou na área — em vez de esconder.
Essa frase é a parte mais forte dos dois documentos. Não tire.

## Antes de mandar qualquer um

Os quatro têm três espaços em branco de propósito. **Eles aparecem em
vermelho e negrito** justamente para você não conseguir imprimir sem ver:

1. `[ TELEFONE AUSTRALIANO ]` — só depois que você tiver o chip. A maioria
   dos eSIM de turista é só dados, sem número, e operadora australiana é
   obrigada por lei a verificar identidade antes de ativar pré-pago. Conte
   com resolver isso nos primeiros dias em Adelaide, com o passaporte na mão.
   **Imprima os CVs só depois disso.**
2. `[ E-MAIL ]` — `albertasse.dev@gmail.com`. Não use o e-mail da FLOW: ele
   morre quando você sai.
3. `[ CONFIRMAR NA CARTA DE CONCESSÃO DO VISTO ]` — a data de validade real
   do visto. Está na carta de concessão, em `1-visto-e-documentos/`.

E no `CV-3-Escritorio` tem mais um, também em vermelho:
`[ APAGUE DESTA LINHA O QUE VOCÊ NÃO CONSEGUE EXPLICAR NUMA ENTREVISTA ]`.
Tire dali tudo que você não conseguiria conversar a respeito, em inglês, com
alguém perguntando. Ferramenta listada que você não sabe usar é a maneira
mais rápida de perder a vaga na entrevista.

## Um aviso sobre o CV-4

Ele cita o `adelaide-jobs` e dá o link do repositório. Isso é verdade e é
forte — mas **só mande esse CV se você conseguir abrir o código e explicar o
que cada parte faz.** Se um entrevistador abrir o link e perguntar "como
funciona a deduplicação?", você precisa ter resposta. Ele diz "with AI
pair-programming" exatamente para você não ser pego numa pergunta dessas.

Se não estiver confortável com isso ainda, mande o `CV-3-Escritorio` — que é
honesto, forte, e não depende de você defender código.

## Onde guardar a versão preenchida

Aqui dentro, na pasta `pessoal/`. Ela é **ignorada pelo git de propósito**:
este repositório é público, e a versão preenchida tem seu telefone e o seu
e-mail. Os quatro modelos desta pasta podem ser públicos porque não têm dado
de contato nenhum — a versão que você preenche, não.

Nunca tire `curriculos/pessoal/` do `.gitignore`.

## O que aconteceu com os antigos

Os três CVs que estavam em `australia/2-curriculo/` foram substituídos por
estes. Dois problemas que eles tinham e estes não têm:

- O de hospitalidade dizia **"Four years"** na FLOW. São três (2023 – set/2026).
- Os três afirmavam que as férias do curso são **dezembro a fevereiro**. O
  calendário oficial do ILSC nunca foi confirmado, e ELICOS não tem as férias
  longas de uma universidade. Prometer isso a um empregador é prometer o que
  você não sabe. Aqui está escrito "during scheduled course breaks", que é
  verdade sem inventar data.
