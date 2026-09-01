"""Leva as ferramentas para dentro do repositório.

O PROBLEMA
    Quem clonava o repositório recebia o programa e não recebia nada
    para RODAR o programa: os .bat, os scripts e o material curado
    moravam na pasta `australia`, um nível acima, fora do git. Num
    computador novo, o clone era inútil sozinho.

O QUE MUDA
    adelaide-jobs/
      ferramentas/            ← os .bat e os scripts que se usa sempre
        historico/            ← os que já rodaram, guardados como registro
        caminhos.py           ← quem sabe onde fica cada coisa
      material/               ← o HTML curado, 269 empregadores a mão
      ...

    E na pasta `australia` ficam dois .bat de duas linhas, que só
    chamam os de dentro. O atalho da área de trabalho continua
    apontando para o mesmo lugar e continua funcionando.

POR QUE UM MÓDULO caminhos.py
    Cada script tinha o caminho escrito na mão. Mover um arquivo
    quebrava três outros, e o erro só aparecia na hora de rodar. Agora
    quem procura é uma função só: sobe a partir do próprio arquivo até
    achar o pyproject.toml.

RODAR
    python reestruturar.py          (uma vez só)
"""
import pathlib
import re
import shutil
import subprocess

AQUI = pathlib.Path(__file__).resolve().parent          # …/australia
PROJ = AQUI / "adelaide-jobs"
FERR = PROJ / "ferramentas"
HIST = FERR / "historico"
MAT = PROJ / "material"

# Os que se usa de novo, toda semana.
VIVOS = [
    "ATUALIZAR-VAGAS.bat", "RODAR.bat", "ENVIAR-PARA-GITHUB.bat",
    "CRIAR-ATALHO.bat", "REPARAR-BANCO.bat",
    "reparar_banco.py", "publicar-no-github-pages.py", "aba-empresas.py",
    "play.ico",
]
# Já rodaram e não rodam de novo. Ficam porque explicam por que o
# material é do jeito que é — cada um tem a medição no cabeçalho.
HISTORICOS = [
    "aba-rota.py", "ajuste-mapa.py", "alvos-44.py", "corrige-chip.py",
    "corrigir-acessibilidade.py", "curar-empregadores.py",
    "empresas-celular.py", "filtros-celular.py", "horario.py",
    "mapa-e-rota.py", "mapa-leaflet.py", "mapa-real.py",
    "nomenclatura.py", "registrar-empregadores.py", "render-horario.py",
    "rota-visitas.py", "reestruturar.py",
]
# Superado pelo ENVIAR-PARA-GITHUB.bat, que não usa token.
APAGAR = ["SUBIR-NO-GITHUB.bat"]

CAMINHOS = '''"""Onde fica cada coisa, resolvido a partir deste arquivo.

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
        "não achei o pyproject.toml subindo a partir de " + str(eu) + ".\\n"
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
'''

# Bloco que todo .bat passa a usar para achar o projeto, esteja onde estiver.
# Bloco que todo .bat passa a usar para achar o projeto, esteja onde estiver.
#
# %%~fI resolve o ".." na hora de rodar. A tentação é escrever
#     pushd "%AQUI%.." & set "PROJ=%CD%" & popd
# e isso NÃO funciona dentro de um if(): o batch expande %CD% quando lê
# a linha, antes do pushd rodar, e PROJ fica com a pasta errada.
#
# PROJ nunca termina em barra — todo uso é "%PROJ%\alguma-coisa".
ACHA_PROJ = """rem  Acha a pasta do projeto a partir deste arquivo: ao lado do
rem  pyproject.toml, uma pasta acima, ou dentro de adelaide-jobs\\.
rem  Assim o mesmo .bat funciona em ferramentas\\ e solto na pasta de cima.
set "AQUI=%~dp0"
set "PROJ="
if exist "%AQUI%pyproject.toml" for %%I in ("%AQUI%.") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%..\\pyproject.toml" for %%I in ("%AQUI%..") do set "PROJ=%%~fI"
if not defined PROJ if exist "%AQUI%adelaide-jobs\\pyproject.toml" for %%I in ("%AQUI%adelaide-jobs") do set "PROJ=%%~fI"
if not defined PROJ (
  echo   [ERRO] Nao achei o pyproject.toml a partir de:
  echo          %AQUI%
  echo   Este arquivo precisa estar dentro da pasta do projeto.
  goto FIM
)
cd /d "%PROJ%"
"""

STUB = """@echo off
rem  Atalho. O arquivo de verdade mora em adelaide-jobs\\ferramentas\\.
rem  Este aqui existe para o atalho da area de trabalho nao quebrar
rem  quando as ferramentas foram para dentro do repositorio.
call "%~dp0adelaide-jobs\\ferramentas\\__NOME__" %*
"""


def mover(nome: str, destino: pathlib.Path) -> bool:
    origem = AQUI / nome
    if not origem.exists():
        return False
    destino.mkdir(parents=True, exist_ok=True)
    shutil.move(str(origem), str(destino / nome))
    return True


def main() -> None:
    if FERR.exists() and (FERR / "caminhos.py").exists():
        raise SystemExit("já reestruturado")

    FERR.mkdir(parents=True, exist_ok=True)
    HIST.mkdir(parents=True, exist_ok=True)
    MAT.mkdir(parents=True, exist_ok=True)

    # ── 1. o material curado ────────────────────────────────────────
    n_mat = 0
    for f in sorted(AQUI.glob("Trabalho_Adelaide_CONSOLIDADO*.html")):
        shutil.move(str(f), str(MAT / f.name))
        n_mat += 1
    # Os .bak ficam de fora do git mas continuam ao lado, no disco.
    for f in sorted(AQUI.glob("Trabalho_Adelaide_CONSOLIDADO*.bak*")):
        shutil.move(str(f), str(MAT / f.name))

    # ── 2. as ferramentas ───────────────────────────────────────────
    v = sum(mover(n, FERR) for n in VIVOS)
    h = sum(mover(n, HIST) for n in HISTORICOS)
    (FERR / "caminhos.py").write_text(CAMINHOS, encoding="utf-8")

    for n in APAGAR:
        f = AQUI / n
        if f.exists():
            f.unlink()

    # ── 3. os .bat acham o projeto sozinhos ─────────────────────────
    for nome in ("ATUALIZAR-VAGAS.bat", "ENVIAR-PARA-GITHUB.bat",
                 "CRIAR-ATALHO.bat", "REPARAR-BANCO.bat", "RODAR.bat"):
        p = FERR / nome
        if not p.exists():
            continue
        b = p.read_bytes()
        # troca o bloco antigo de descoberta de pasta pelo novo
        # re.sub trata a substituicao como template: o "\p" de %~dp0
        # dentro do bloco novo vira "bad escape". Lambda resolve.
        novo_bloco = ACHA_PROJ.replace("\n", "\r\n").encode("cp1252", "replace")
        b = re.sub(rb'set "AQUI=%~dp0"\r\n(?:set "PROJ=[^\r]*"\r\n)?'
                   rb'(?:if (?:not defined PROJ )?if exist[^\r]*\r\n)*',
                   lambda _m: novo_bloco, b, count=1)
        b = b.replace(b'set "PROJ=%~dp0adelaide-jobs"\r\n', novo_bloco)
        b = b.replace(b'set "PROJ=%AQUI%adelaide-jobs"\r\n', b"")
        # o bloco de erro antigo virou duplicata do novo
        b = re.sub(rb'if not exist "%PROJ%\\pyproject\.toml" \(\r\n'
                   rb'(?:[^\r]*\r\n)*?\)\r\ncd /d "%PROJ%"\r\n', b"", b, count=1)
        # caminhos que apontavam para a pasta de cima
        b = b.replace(b'"%AQUI%aba-empresas.py"', b'"%~dp0aba-empresas.py"')
        b = b.replace(b'"%AQUI%reparar_banco.py"', b'"%~dp0reparar_banco.py"')
        b = b.replace(b'%AQUI%Vagas_Adelaide.html', b'%PROJ%exports\\Vagas_Adelaide.html')
        b = b.replace(b'"%AQUI%ATUALIZAR-VAGAS.bat"', b'"%~dp0ATUALIZAR-VAGAS.bat"')
        b = b.replace(b"%AQUI%ATUALIZAR-VAGAS.bat", b"%~dp0ATUALIZAR-VAGAS.bat")
        b = b.replace(b"%AQUI%play.ico", b"%~dp0play.ico")
        # Por último: PROJ não termina mais em barra, então todo uso
        # precisa da barra explícita. Tem que vir depois das trocas
        # acima, senão elas reintroduzem "%PROJ%exports" grudado.
        b = b.replace(b"%PROJ%exports", b"%PROJ%\\exports")
        b = b.replace(b"%PROJ%\\\\", b"%PROJ%\\")
        p.write_bytes(b)

    # ── 4. stubs, para o atalho da area de trabalho sobreviver ──────
    for nome in ("ATUALIZAR-VAGAS.bat", "ENVIAR-PARA-GITHUB.bat"):
        (AQUI / nome).write_text(STUB.replace("__NOME__", nome),
                                 encoding="ascii", newline="\r\n")

    # ── 5. scripts .py: passam a usar o caminhos.py ─────────────────
    ajustar_py()

    print(f"material    : {n_mat} arquivo(s) → material/")
    print(f"ferramentas : {v} vivos, {h} históricos")
    print(f"stubs       : ATUALIZAR-VAGAS.bat e ENVIAR-PARA-GITHUB.bat "
          f"ficaram na pasta de cima")
    subprocess.run(["git", "add", "-A"], cwd=PROJ, check=False)
    print("\ngit add feito — confira com `git status` antes de commitar")


def ajustar_py() -> None:
    """Troca os caminhos escritos na mão pelo módulo caminhos."""
    trocas = {
        "aba-empresas.py": [
            ('AQUI = pathlib.Path(__file__).resolve().parent\n'
             'ARQ = AQUI / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"\n'
             'DADOS = AQUI / "adelaide-jobs" / "exports" / "empregadores.json"',
             'import caminhos\n\n'
             'ARQ = caminhos.material()\n'
             'DADOS = caminhos.empregadores_json()'),
        ],
        "publicar-no-github-pages.py": [
            ('RAIZ = pathlib.Path(__file__).resolve().parent\n'
             'FONTE = RAIZ / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"\n'
             'DESTINO = RAIZ / "adelaide-jobs" / "docs" / "index.html"',
             'import caminhos\n\n'
             'FONTE = caminhos.material()\n'
             'DESTINO = caminhos.DOCS / "index.html"'),
        ],
    }
    for nome, pares in trocas.items():
        p = FERR / nome
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        for velho, novo in pares:
            if velho in s:
                s = s.replace(velho, novo, 1)
            else:
                print(f"   [!] {nome}: âncora não encontrada, ajuste à mão")
        # o import tem que ver a própria pasta
        if "sys.path" not in s:
            s = s.replace("import pathlib",
                          "import pathlib\nimport sys\n\n"
                          "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))",
                          1)
        p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    main()
