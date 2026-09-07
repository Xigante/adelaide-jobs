# Começar aqui

Este arquivo existe para uma situação só: **você está num computador
novo e quer tudo funcionando.**

---

## Num computador zerado, três passos

**1. Instale o git**, se ainda não tiver. No menu Iniciar, abra o
*Terminal* e cole:

```powershell
winget install Git.Git
```

**2. Feche o Terminal, abra outro, e cole isto:**

```powershell
git clone https://github.com/Xigante/adelaide-jobs.git "$HOME\adelaide-jobs"
```

**3. Abra a pasta que apareceu e dê dois cliques em `INSTALAR.bat`.**

Ele cria o ambiente, instala o programa, abre o Bloco de Notas para
você colar a chave da Adzuna, confere se ficou tudo certo e oferece o
atalho na área de trabalho. De 2 a 5 minutos.

> A chave da Adzuna é gratuita e sai na hora em
> <https://developer.adzuna.com/>. Ela fica só no arquivo `.env`, que o
> git ignora. **Não mande essa chave por chat, e-mail ou print** — nem
> para mim.

---

## Depois disso, são três botões

| botão | quando | o que faz |
|---|---|---|
| `ferramentas\ATUALIZAR-VAGAS.bat` | **uma vez por dia** | busca vagas novas, recalcula as notas, atualiza o material e abre o relatório |
| `ferramentas\ENVIAR-PARA-GITHUB.bat` | quando quiser publicar | sobe as melhorias e atualiza o site |
| `ferramentas\REPARAR-BANCO.bat` | só se der erro | reconstrói o banco de vagas sem perder nada |
| `ferramentas\CONFIGURAR-EMAIL.bat` | uma vez | pergunta o e-mail e a senha de app e grava no `.env` para você |
| `ferramentas\TESTAR-EMAIL.bat` | ao ligar os alertas | confere a caixa de alertas sem gastar cota |

Uma vez por dia, não mais: cada rodada gasta 173 das 250 chamadas
diárias que a Adzuna dá de graça.

---

## Ainda não ligou os alertas por e-mail?

SEEK, LinkedIn, Indeed, Jora, iworkfor.sa.gov.au e Gumtree entram no
sistema pelos alertas que eles mesmos mandam. São 40 minutos, uma vez.
O passo a passo está em [docs/ALERTAS-DE-EMAIL.md](docs/ALERTAS-DE-EMAIL.md).

---

## Onde fica cada coisa

```
adelaide-jobs/
├── INSTALAR.bat          ← o de cima
├── PROMPT-PARA-IA.md     ← cole numa IA junto com o relatório
├── CLAUDE.md             ← as IAs que abrem a pasta leem sozinhas
├── ferramentas/          ← os botões e os scripts
│   └── historico/        ← os que já rodaram, com a medição no cabeçalho
├── material/             ← o HTML curado, 269 empregadores a mão
├── config/               ← profile.yaml (você) e sources.yaml (as fontes)
├── src/                  ← o programa
├── docs/                 ← o manual e o site publicado
└── exports/              ← o que a coleta gera (fora do git)
```

Duas coisas moram **fora** da pasta, e é de propósito:

- **O banco de vagas** — `C:\Users\<você>\.adelaide-jobs\jobs.db`.
  O SQLite corrompe dentro de pasta sincronizada pelo OneDrive; isso
  já aconteceu aqui, em 01/09/2026, e custou 494 vagas.
- **O ambiente Python** — `C:\Users\<você>\.venvs\adelaide-jobs`.
  São milhares de arquivos pequenos que o OneDrive tentaria sincronizar.

---

## Se algo der errado

1. `ferramentas\ATUALIZAR-VAGAS.bat` e leia a última mensagem da tela preta.
2. A tabela **sintoma → causa → conserto** está em
   `docs/como-funciona.html`, seção 15.
3. `adelaide-jobs doctor` diz o que a sua rede alcança e se as chaves existem.
