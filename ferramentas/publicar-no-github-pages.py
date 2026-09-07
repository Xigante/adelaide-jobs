"""Prepara o material para o GitHub Pages.

Rode isto sempre que o material mudar, e depois faça commit e push.
Ele copia o HTML para docs/index.html acrescentando duas coisas:

  1. <meta robots="noindex,nofollow"> — a página fica no ar e acessível
     por quem tem o link, mas NÃO entra no Google. Isso importa porque o
     material tem o seu nome, o seu visto, a sua escola e uma opinião
     por escrito sobre a chance de cada empregador. Um gerente de
     Adelaide que googlar o seu nome não deveria cair numa página que
     classifica a empresa dele como "Muito baixa".

     Atenção: num "project site" o robots.txt do repositório NÃO vale —
     o Google só lê robots.txt na raiz do domínio, que é o seu
     portfólio. Por isso a meta tag é o mecanismo certo aqui.

  2. Um rodapé dizendo o que a página é e quando foi gerada.

O que NÃO vai para o ar: o relatório de vagas. São 2,5 MB que mudam a
cada coleta e trazem a sua nota para cada vaga. Fica no seu computador.
"""
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import re
import shutil

import caminhos

FONTE = caminhos.material()
DESTINO = caminhos.DOCS / "index.html"

NOINDEX = (
    '<meta name="robots" content="noindex,nofollow">\n'
    '<meta name="googlebot" content="noindex,nofollow">\n'
)


def main() -> None:
    if not FONTE.exists():
        raise SystemExit(f"não achei {FONTE.name}")
    s = FONTE.read_text(encoding="utf-8")

    if "noindex" not in s:
        s = s.replace('<meta charset="utf-8">',
                      '<meta charset="utf-8">\n' + NOINDEX, 1)

    hoje = datetime.date.today().strftime("%d/%m/%Y")
    marca = (
        f'<p style="margin-top:var(--sp4);padding-top:var(--sp4);'
        f'border-top:1px solid var(--line);color:var(--ink-3);'
        f'font-size:var(--fs-caption)">Documento de trabalho pessoal, '
        f'publicado em <code>xigante.github.io/adelaide-jobs</code> só para '
        f'ficar acessível no celular. Não indexado em buscadores. '
        f'Gerado em {hoje}.</p>'
    )
    if "Documento de trabalho pessoal" not in s:
        s = s.replace("</footer>", marca + "</footer>", 1)

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": sem isto o Windows grava CRLF e o git ve o
    # arquivo inteiro mudado a cada publicacao.
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)

    kb = DESTINO.stat().st_size / 1024
    print(f"docs/index.html gerado · {kb:.0f} KB")
    print(f"noindex: {'sim' if 'noindex' in s else 'NÃO'}")
    print()
    print("Agora:")
    print("  1. rode o ENVIAR-PARA-GITHUB.bat (ou `git add -A && git commit && git push`)")
    print("  2. no GitHub: Settings → Pages → Source: Deploy from a branch")
    print("     Branch: main · pasta: /docs · Save")
    print("  3. espere uns 2 minutos e abra:")
    print("     https://xigante.github.io/adelaide-jobs/")


if __name__ == "__main__":
    main()
