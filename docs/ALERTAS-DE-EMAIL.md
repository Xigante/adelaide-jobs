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

## Passo 3 — A senha de app

### O mal-entendido que custa a tarde inteira

**Você não escolhe essa senha.** O Google sorteia 16 letras e mostra
**uma vez só**, numa janelinha que abre depois do botão **Create**.
Fechou a janelinha, acabou: nem você nem o Google veem de novo. A lista
que fica na página guarda só o **nome** e a **data**, para você poder
revogar.

Um código sorteado é ilegível: `kemu bcrd lsbq gbcn`. Se o que você tem
na mão dá para ler — tem seu nome, tem uma palavra — não é ele.

### 3.1 — Ligar a verificação em duas etapas

`myaccount.google.com/security` → **2-Step Verification** → ligue com o
número do celular. Sem ela o Google nem oferece senha de app.

### 3.2 — Desligar o que bloqueia

A página de senha de app fica indisponível, ou o botão **Create** não
abre janela nenhuma, quando a conta está em modo sem senha. Em
`myaccount.google.com/security`, procure na lista *How you sign in to
Google*:

| O que está lá | O que fazer |
|---|---|
| **Skip password when possible** — `On` | **desligue** |
| **Passkeys and security keys** — `1 passkey` | se depois de desligar o de cima ainda não funcionar, apague a passkey |

O Google esconde a senha de app de propósito quando a conta é
"passwordless": para ele, uma conta sem senha não deveria ter uma senha
avulsa por aí. A troca é consciente — nesta conta, que só recebe alerta
de vaga, vale a pena.

Você pode religar a passkey depois que o coletor estiver funcionando: a
senha de app já criada continua valendo.

### 3.2b — Se você esqueceu a senha DA CONTA

Isto não derruba o coletor: ele não usa a senha da conta, usa a senha de
app, que já está gravada no `.env` e continua funcionando.

Só que resetar a senha da conta **revoga todas as senhas de app**. Então
tente, nesta ordem, antes de resetar:

1. **O navegador guardou?** `chrome://settings/passwords` → procure
   `google.com`. Quase sempre está lá, se a conta foi criada nele.
2. **A passkey.** Se ela ainda existe nesta máquina, dá para entrar sem
   senha nenhuma.
3. **Ainda logado?** Então troque por dentro, em *Security* → *Password*,
   confirmando pelo celular do 2FA. Trocar sabendo que vai trocar é
   melhor do que descobrir trancado do lado de fora.

Se mesmo assim precisar resetar: reseta. O prejuízo é criar outra senha
de app e rodar o `CONFIGURAR-EMAIL.bat` — dois minutos. **Não se perde**
nem os alertas assinados, nem os e-mails, nem o banco, nem nada do
repositório.

> **Enquanto está aí, resolva as duas advertências da tela de
> segurança**: verifique o e-mail de recuperação e cadastre o telefone
> de recuperação. Conta recém-criada, sem recuperação verificada, é
> exatamente o perfil em que o Google recusa devolver o acesso depois.

### 3.3 — Criar

1. Abra `myaccount.google.com/apppasswords`
2. Escreva um nome qualquer — é só etiqueta — e clique em **Create**
3. **Abre uma janelinha com o código em letras grandes, em 4 grupos de
   4.** Aquilo é a senha.
4. Copie **antes** de fechar.

Se ao clicar em **Create** não abrir janela nenhuma, volte ao 3.2: falta
desligar alguma coisa.

> Isso **não** é a senha da conta. É uma senha separada, que só serve
> para ler e-mail e que você revoga nessa mesma página quando quiser.
> Não mande esse código por chat, e-mail ou print — para ninguém.

---

## Passo 4 — Gravar (1 min)

**Ordem invertida de propósito**: deixe o programa esperando *antes* de
criar a senha, para não ter janela para perder.

1. Dois cliques em `ferramentas\CONFIGURAR-EMAIL.bat`
2. Digite o e-mail, Enter. Ele para, esperando a senha. **Deixe aberto.**
3. Só agora faça o 3.3 acima
4. Copie o código e cole na janela preta (Ctrl+V ou botão direito), Enter

Enquanto você cola a senha **a tela não mostra nada** — nem asterisco.
É de propósito. Cole e aperte Enter mesmo assim.

Pode colar com os espaços do jeito que o Google mostra: o script tira
sozinho. Ele também recusa o que claramente não é uma senha de app —
comprimento errado, número, símbolo, ou pedaço legível como seu nome.

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
| `O servidor recusou o login` | é a senha da conta, não a de app; ou é uma senha que você inventou (o Google sorteia, você não escolhe) |
| O botão **Create** não abre janela | *Skip password when possible* ligado, ou passkey — veja 3.2 |
| Funcionava e parou de funcionar | você trocou a senha da conta. O Google revoga todas as senhas de app quando isso acontece, sem avisar. Crie outra e rode o `CONFIGURAR-EMAIL.bat` |
| `A caixa está vazia` | os alertas ainda não chegaram. Espere um dia |
| `Conectou e leu, mas não extraiu nenhuma vaga` | as mensagens não são de plataforma conhecida. Me mande uma e eu acrescento o formato |
| `Não conectei em imap.gmail.com:993` | internet, firewall da empresa, ou antivírus bloqueando a porta 993 |

O programa conhece hoje: **SEEK, LinkedIn, Indeed, Jora, Adzuna,
iworkfor.sa.gov.au e Gumtree.** Cada um tem teste travando o formato do
link em `tests/test_email_formatos.py` — se uma plataforma mudar, o
teste quebra antes de você descobrir na marra.
