# adelaide-jobs — para quem for mexer no código

Pipeline de descoberta de vagas em Adelaide para uma pessoa específica.
Se você é uma IA e abriu esta pasta: leia isto antes de mudar qualquer
coisa. Se o que você quer é **analisar o relatório** em vez de mexer no
programa, o arquivo certo é `PROMPT-PARA-IA.md`.

## A pessoa, porque é ela que define as regras

Pedro chega em Adelaide em 24/09/2026 com visto Student 500: **48 h por
quinzena**, inglês **A2**, **sem carteira australiana e sem carro**,
estudando no ILSC em 115 Grenfell St. Três anos de experiência com
dados e escritório; zero em hospitalidade, varejo, armazém e limpeza.
Toda decisão de projeto sai daí.

## A forma

```
coletores → SQLite → extrator (texto → Dimensions) → knockouts
          → scoring.py (aritmética sobre pesos do YAML) → CSV / HTML
```

Quatro invariantes. Quebrar qualquer uma quebra o projeto:

1. **O extrator devolve categorias, nunca notas.** `Dimensions` é
   `NONE_REQUIRED`, `BOH_MINIMAL`, `CASUAL` — nunca um número. Quem
   converte categoria em ponto é o `scoring.py`, sozinho. É isso que
   permite trocar o extrator de regex por um de LLM sem tocar na conta.
2. **O extrator é injetado**, via `Pipeline(..., extractor=...)`.
3. **Coletor separa `collect()` de `parse()`.** `collect` fala com a
   rede; `parse` é puro e testável com fixture.
4. **`safe_collect()` nunca levanta exceção.** Erro de uma fonte vira
   linha no `run_log`; as outras fontes continuam.

## Onde mexer no comportamento

| quero mudar | mexo em |
|---|---|
| o peso de uma dimensão | `config/profile.yaml`, bloco `scoring.weights` (soma 100) |
| quais vagas entram | `config/sources.yaml`, `queries` e `categories` |
| o que conta como inglês baixo | `config/profile.yaml`, `boh_keywords` |
| o que conta como ponte de carreira | `config/profile.yaml`, `career_keywords` |
| o que é bloqueado de saída | `src/adelaide_jobs/filters.py` |
| como o texto vira categoria | `src/adelaide_jobs/extract.py` |

## Armadilhas que já custaram caro

**Palavra sem fronteira casa dentro de outra palavra.** Medido em 6.895
anúncios reais: `unity` casava em comm**unity** e dava bônus de carreira
a 70 vagas de Community Support Worker; `excel` casava em **excel**lent
em 633 anúncios. `RuleExtractor._compilar` põe `(?<!\w)` e `(?!\w)` em
cada termo — e aceita um `s` opcional à direita, porque anúncio
australiano é escrito no plural e fechar sem isso fez "Cleaners" perder
18 pontos. Não ponha termo com menos de quatro letras nas listas.

**A descrição da Adzuna vem cortada em 500 caracteres.** Todo regex que
procura requisito ("2+ anos", "full working rights", RSA, White Card)
está lendo o começo do anúncio, não o anúncio. Por isso 73% das vagas
ficam com `eng_contact = UNKNOWN`. Ausência de sinal não é ausência de
requisito, e nenhum texto gerado pelo programa deve afirmar o contrário.

**`db.unscored()` devolve um LOTE, não tudo.** Já houve um `rows =
db.unscored()` sem laço: 5.026 vagas de 5.526 ficaram sem nota e os 103
testes passaram, porque o banco de teste tinha 7 vagas. Se for mexer em
`score_pending`, o teste `test_pontua_alem_de_um_lote` existe para isso.

**O SQLite não vive dentro do OneDrive.** O banco fica em
`~/.adelaide-jobs/jobs.db` de propósito, e o virtualenv em
`~/.venvs/adelaide-jobs`. Em 01/09/2026 uma cópia do banco através da
pasta sincronizada truncou o arquivo em 12 KB sem dar erro, e custou
494 vagas. Nunca copie o `.db` para dentro ou para fora de pasta
sincronizada — e desconfie de qualquer leitura feita através dela.

**`seek_v5` fica desligado.** Ligar viola os termos de uso do SEEK e
arrisca a conta que ele vai depender em Adelaide. A porta aberta são os
alertas por e-mail (`collectors/email_alerts.py`). A decisão é do dono
do projeto, não sua.

## Antes de dizer que terminou

```bash
python -m pytest -q          # 139 testes, todos verdes
adelaide-jobs doctor         # confere banco, chaves e rede
```

E: se você mudou pesos, suba `scoring.version` no `profile.yaml` — é o
que permite comparar antes e depois. Se mudou vocabulário, repontue uma
**cópia** do banco e compare a distribuição, não confie no olho.

## O que este projeto não faz, de propósito

Não se candidata por ninguém, não preenche formulário, não faz login em
site de vagas e não raspa quem proíbe raspagem. Ele **encontra e
ordena**; quem decide e escreve é a pessoa. Isso não é limitação
técnica, é escolha — e é o que mantém a conta dele viva nos sites de
que ela vai depender.
