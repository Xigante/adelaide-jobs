# Alertas por e-mail — passo a passo

O SEEK e o LinkedIn não têm API e proíbem acesso automatizado. Mas os
dois mandam alerta por e-mail: você assina, eles entregam, e o e-mail é
seu. Ler a própria caixa não viola termo nenhum — a plataforma está
entregando o dado de propósito.

São **40 minutos, uma vez**. Depois disso o coletor lê sozinho, todo dia.

> **A ordem importa.** Os alertas só chegam no dia seguinte. Por isso
> eles vêm antes da senha e antes de ligar qualquer coisa: se você fizer
> ao contrário, vai testar numa caixa vazia e achar que quebrou.

---

## Passo 1 — A conta (3 min)

Crie um **Gmail novo, só para isto**. Sugestão de nome:
`vagas.pedro.adelaide@gmail.com`.

Com conta dedicada, a caixa de entrada inteira já é a pasta de alertas:
sem rótulo, sem filtro, e a senha de app não dá acesso a nenhum e-mail
pessoal seu.

**Não use o `pedro.rocha@flowef.com`.** É da FLOW, você perde quando
sair, e é sistema do empregador.

---

## Passo 2 — Os alertas (25 min)

### A armadilha número um

**Crie as contas em cada site COM O GMAIL NOVO.** SEEK, LinkedIn, Indeed
e Jora exigem conta para salvar busca. Se você entrar com o e-mail
antigo, os alertas vão para a caixa errada e nada disso funciona.

### As buscas, e por que estas palavras

Cada termo abaixo foi contado nos **7.819 anúncios reais de Adelaide**
que já estão no seu banco. O número é quantos títulos contêm a palavra.
Não são palavras que eu achei que os australianos usam — são as que eles
usaram.

Em **todos**, use:

- **Local:** `Adelaide SA` — raio de 25 km
- **Tipo:** `Casual` **e** `Part time`. Não marque Full time: 1.012 das
  vagas coletadas foram bloqueadas por isso, porque estouram o seu visto.
- **Frequência:** **diária**. Semanal chega tarde demais para vaga casual.

| # | Site | Buscar por | Por quê |
|---|---|---|---|
| 1 | SEEK | `cleaner` | 120 títulos. A maior família, e a de melhor nota para o seu perfil |
| 2 | SEEK | `storeperson` | 82. É assim que a Austrália escreve, não "stock assistant" |
| 3 | SEEK | `warehouse` | 81 |
| 4 | SEEK | `kitchen hand` | 15. Faça também com `kitchenhand`, uma palavra só — são anúncios diferentes |
| 5 | SEEK | `administration officer` | 65. O seu objetivo secundário: escritório |
| 6 | LinkedIn | `data entry` | 8 no título, e o LinkedIn é onde essas aparecem |
| 7 | LinkedIn | `administration officer` | 65 |
| 8 | Indeed AU | `cleaner` | cobertura diferente da do SEEK |
| 9 | Indeed AU | `storeperson` | |
| 10 | Indeed AU | `no experience` | 27 títulos usam essa frase literal |
| 11 | Jora | `casual` | é espelho do SEEK; um alerta largo basta de redundância |
| 12 | iworkfor.sa.gov.au | tudo em Adelaide metro | **~450 vagas.** Governo de SA. A maior fonte concentrada da cidade |
| 13 | Gumtree | `cleaning`, em Jobs | pequena, mas tem casual que não aparece em lugar nenhum |

**Prefira muitos alertas estreitos a poucos amplos.** Cada e-mail mostra
só os primeiros resultados e o resto some sem aviso. Treze alertas
estreitos cobrem mais do que um alerta de "jobs in Adelaide".

### Onde fica o botão, em cada um

**SEEK** — `seek.com.au`. Faça a busca com os filtros, e no alto da
lista de resultados aparece **Save search**. Ele pergunta a frequência;
escolha diária.

**LinkedIn** — `linkedin.com/jobs`. Faça a busca e ligue o botão
**Job alert** no topo dos resultados. Confira que está em *Daily* e em
*Email*, não só notificação no app.

**Indeed** — `au.indeed.com`. Role até o fim da primeira página de
resultados: tem uma caixa **Receive job alerts / Activate**. Ou o link
*Get new jobs for this search by email*.

**Jora** — `au.jora.com`. Depois da busca aparece **Email me jobs like
these**.

**iworkfor.sa.gov.au** — tem uma área de **Job Alerts** própria, que
pede cadastro. Escolha a região de Adelaide e a frequência diária. Este
é o que mais vale a pena: são ~450 vagas no metro, e é a fonte que a
gente não consegue coletar direto porque a paginação deles é por
formulário POST. Pelo e-mail o problema some.

**Gumtree** — `gumtree.com.au`, seção Jobs, categoria Cleaning, local
Adelaide. Depois da busca aparece **Save search** com opção de e-mail.

---

## Passo 3 — A senha de app (3 min)

Na conta **nova**:

1. `myaccount.google.com/security` → ligue a **verificação em duas
   etapas**. Sem ela o Google nem deixa criar senha de app.
2. `myaccount.google.com/apppasswords` → nome `coletor-vagas` → copie os
   **16 caracteres**.

> Isso **não** é a senha da conta. É uma senha separada, que só serve
> para ler e-mail e que você revoga nessa mesma página quando quiser.
> Não mande esse código por chat, e-mail ou print — para ninguém.

---

## Passo 4 — Escrever no `.env` (1 min)

Abra `adelaide-jobs\.env` no Bloco de Notas e preencha três linhas:

```
IMAP_USER=aconta-nova@gmail.com
IMAP_PASSWORD=os16caracteres
IMAP_FOLDER=INBOX
```

O `.env` está no `.gitignore`. Ele nunca vai para o GitHub.

---

## Passo 5 — Testar (1 min)

Duplo clique em **`ferramentas\TESTAR-EMAIL.bat`**.

Ele conecta, lista as pastas, conta as mensagens, lê as cinco mais
recentes e mostra o que conseguiu extrair. **Não gasta cota de API
nenhuma.** A senha nunca aparece na tela — só o número de caracteres.

O que você quer ver no fim:

```
  Vagas extraídas dessas mensagens: 23
       9  email:seek
       6  email:indeed
       5  email:linkedin
       3  email:iworkfor

  Está funcionando.
```

Se disser **"A caixa está vazia"**, é só cedo: os alertas chegam no dia
seguinte. Volte amanhã.

---

## Passo 6 — Ligar (1 min)

Só depois que o teste mostrar vagas extraídas. Abra
`config\sources.yaml`, ache o bloco `email_alerts:` e troque uma
palavra:

```yaml
email_alerts:
  enabled: true
```

Rode o **`ATUALIZAR-VAGAS.bat`**. Daí em diante os alertas entram junto
com a Adzuna, o ATS e a SA Health, e a deduplicação junta o que vier
repetido.

---

## O que esperar

**Sai título e link. Não sai descrição.** O alerta não traz o texto do
anúncio. Quando a mesma vaga também vier da Adzuna, a deduplicação junta
as duas e a descrição vem do outro lado. Quando não vier, a vaga entra
com o que tem — e é melhor ter o link do que não saber que ela existe.

Por isso as vagas de e-mail costumam ficar com nota mais baixa: sem
texto, o programa não consegue avaliar experiência exigida nem carga de
inglês, e cai no padrão. **Não confunda nota baixa com vaga ruim** neste
caso.

---

## Se der errado

| a tela diz | é |
|---|---|
| `IMAP_USER ou IMAP_PASSWORD vazios` | você não salvou o `.env`, ou salvou como `.env.txt` |
| `O servidor recusou o login` | é a senha da conta, não a de app; ou a verificação em duas etapas não está ligada |
| `A caixa está vazia` | os alertas ainda não chegaram. Espere um dia |
| `Conectou e leu, mas não extraiu nenhuma vaga` | as mensagens não são de plataforma conhecida. Me mande uma e eu acrescento o formato |
| `Não conectei em imap.gmail.com:993` | internet, firewall da empresa, ou antivírus bloqueando a porta 993 |

O programa conhece hoje: **SEEK, LinkedIn, Indeed, Jora, Adzuna,
iworkfor.sa.gov.au e Gumtree.** Cada um tem teste travando o formato do
link em `tests/test_email_formatos.py` — se uma plataforma mudar, o
teste quebra antes de você descobrir na marra.
