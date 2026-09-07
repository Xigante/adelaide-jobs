"""O .env não pode perder nada quando a senha de app entra.

O script grava por cima de um arquivo que também guarda a chave da
Adzuna. Uma reescrita ingênua (abrir, montar tudo de novo, salvar)
apagaria os comentários e, no pior caso, a chave — e o erro só
apareceria na próxima coleta, longe daqui.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTAS = RAIZ / "ferramentas"


def _modulo():
    sys.path.insert(0, str(FERRAMENTAS))
    spec = importlib.util.spec_from_file_location(
        "configurar_email", FERRAMENTAS / "configurar_email.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MODELO = """\
# ─── Adzuna ────────────────────────────────
ADZUNA_APP_ID=abc123
ADZUNA_APP_KEY=segredo

# ─── Alertas de e-mail ─────────────────────
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=
IMAP_PASSWORD=
IMAP_FOLDER=INBOX
"""


def _grava(tmp_path, conteudo=MODELO, **chaves):
    mod = _modulo()
    env = tmp_path / ".env"
    env.write_text(conteudo, encoding="utf-8")
    mod.ENV = env
    mod.gravar(chaves or {"IMAP_USER": "a@gmail.com",
                          "IMAP_PASSWORD": "abcdefghijklmnop",
                          "IMAP_FOLDER": "INBOX"})
    return env.read_text(encoding="utf-8")


def test_grava_usuario_e_senha(tmp_path):
    saida = _grava(tmp_path)
    assert "IMAP_USER=a@gmail.com" in saida
    assert "IMAP_PASSWORD=abcdefghijklmnop" in saida


def test_nao_perde_a_chave_da_adzuna(tmp_path):
    saida = _grava(tmp_path)
    assert "ADZUNA_APP_ID=abc123" in saida
    assert "ADZUNA_APP_KEY=segredo" in saida


def test_nao_perde_os_comentarios(tmp_path):
    saida = _grava(tmp_path)
    assert "# ─── Adzuna" in saida
    assert "# ─── Alertas de e-mail" in saida


def test_nao_muda_o_numero_de_linhas(tmp_path):
    saida = _grava(tmp_path)
    assert len(saida.splitlines()) == len(MODELO.splitlines())


def test_chave_que_faltava_e_criada(tmp_path):
    sem_folder = MODELO.replace("IMAP_FOLDER=INBOX\n", "")
    saida = _grava(tmp_path, sem_folder,
                   IMAP_USER="a@gmail.com", IMAP_FOLDER="INBOX")
    assert "IMAP_FOLDER=INBOX" in saida
    assert "ADZUNA_APP_KEY=segredo" in saida


def test_preserva_crlf(tmp_path):
    """O Bloco de Notas salva com CRLF. Não pode virar LF no meio."""
    mod = _modulo()
    env = tmp_path / ".env"
    env.write_bytes(MODELO.replace("\n", "\r\n").encode("utf-8"))
    mod.ENV = env
    mod.gravar({"IMAP_USER": "a@gmail.com"})
    saida = env.read_bytes()

    assert b"\r\n" in saida
    # Nenhum \n solto: todo \n tem que vir precedido de \r. Se sobrar
    # um, o arquivo fica com quebra misturada e alguns editores do
    # Windows mostram tudo numa linha so.
    assert saida.count(b"\n") == saida.count(b"\r\n")
    assert b"a@gmail.com" in saida


def test_valor_antigo_e_substituido_nao_duplicado(tmp_path):
    cheio = MODELO.replace("IMAP_USER=", "IMAP_USER=velho@gmail.com")
    saida = _grava(tmp_path, cheio, IMAP_USER="novo@gmail.com")
    assert saida.count("IMAP_USER=") == 1
    assert "velho@gmail.com" not in saida
