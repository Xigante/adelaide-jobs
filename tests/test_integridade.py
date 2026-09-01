"""O banco corrompeu em 01/09/2026 e a coleta só morreu no primeiro UPDATE.

Seis minutos de coleta e um pedaço da cota diária da Adzuna gastos para
depois estourar num traceback de SQLite. `_banco_integro` existe para
parar antes disso, e estes testes existem para que ele continue parando.
"""
import sqlite3

from adelaide_jobs.cli import _banco_integro
from adelaide_jobs.db import Database


def test_banco_saudavel_passa(tmp_path):
    caminho = tmp_path / "jobs.db"
    with Database(caminho):
        pass
    assert _banco_integro(caminho) is True


def test_banco_que_ainda_nao_existe_passa(tmp_path):
    """Primeira execução da vida: não há banco, e isso não é defeito."""
    assert _banco_integro(tmp_path / "nunca-rodou.db") is True


def test_banco_corrompido_reprova(tmp_path, capsys):
    caminho = tmp_path / "jobs.db"
    with Database(caminho) as db:
        db.conn.execute("PRAGMA journal_mode=DELETE")   # sem WAL, um arquivo só
        db.conn.execute(
            "INSERT INTO job_cluster (cluster_id, title) VALUES ('a', 'x')")
        db.conn.commit()

    # Estraga o miolo do arquivo, preservando o cabeçalho de 100 bytes:
    # é assim que o SQLite passa a dizer 'disk image is malformed'.
    dados = bytearray(caminho.read_bytes())
    dados[100:2000] = b"\xff" * 1900
    caminho.write_bytes(bytes(dados))

    assert _banco_integro(caminho) is False
    saida = capsys.readouterr().out
    assert "CORROMPIDO" in saida
    assert "REPARAR-BANCO.bat" in saida       # a saída tem que dizer o conserto


def test_arquivo_que_nem_e_sqlite_reprova(tmp_path):
    caminho = tmp_path / "jobs.db"
    caminho.write_text("isto aqui e um txt, nao um banco")
    assert _banco_integro(caminho) is False
