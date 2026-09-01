"""Onde fica cada coisa, resolvido a partir deste arquivo.

Existe para que um script funcione de qualquer lugar: de dentro de
`ferramentas/`, da raiz do projeto, ou solto ao lado dela. Antes cada
script tinha o caminho escrito na mão — mover um arquivo quebrava três
outros, e o erro só aparecia na hora de rodar.
"""
from __future__ import annotations

import pathlib


def _raiz() -> pathlib.Path:
    """A pasta do pyproject.toml, subindo a partir deste arquivo."""
    eu = pathlib.Path(__file__).resolve()
    for pasta in [eu.parent, *eu.parents]:
        if (pasta / "pyproject.toml").exists():
            return pasta
    raise SystemExit(
        "não achei o pyproject.toml subindo a partir de " + str(eu) + ".\n"
        "Este arquivo precisa estar dentro da pasta do projeto."
    )


RAIZ = _raiz()
FERRAMENTAS = RAIZ / "ferramentas"
MATERIAL_DIR = RAIZ / "material"
EXPORTS = RAIZ / "exports"
DOCS = RAIZ / "docs"
CONFIG = RAIZ / "config"

# Fora do projeto de propósito: o SQLite não funciona dentro de pasta
# sincronizada pelo OneDrive. Ver o cabeçalho de src/adelaide_jobs/db.py.
BANCO = pathlib.Path.home() / ".adelaide-jobs" / "jobs.db"


def material() -> pathlib.Path:
    """O HTML curado — 269 empregadores conferidos a mão.

    Procura por padrão em vez de nome fixo: quando o mês no nome mudar,
    nada aqui precisa mudar junto.
    """
    achados = sorted(MATERIAL_DIR.glob("Trabalho_Adelaide_CONSOLIDADO*.html"))
    if not achados:
        raise SystemExit("não achei o material em " + str(MATERIAL_DIR))
    return achados[-1]


def empregadores_json() -> pathlib.Path:
    return EXPORTS / "empregadores.json"
