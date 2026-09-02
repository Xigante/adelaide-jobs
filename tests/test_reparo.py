"""O reparo do banco, contra os dois jeitos reais de ele quebrar.

Os dois casos aqui aconteceram de verdade, com um dia de diferença.

01/09/2026 — CORRUPÇÃO DE VERDADE
    Uma página da árvore de job_cluster com os rowids fora de ordem.
    5.032 de 5.526 clusters recuperados; o resto voltou na coleta
    seguinte.

02/09/2026 — WAL ÓRFÃO, QUE NÃO É CORRUPÇÃO NENHUMA
    O `jobs.db` foi substituído por outro arquivo e o `jobs.db-wal` do
    banco ANTERIOR ficou para trás. Na abertura seguinte o SQLite
    aplicou páginas velhas em cima do banco novo: "invalid page
    number". O banco estava INTEIRO — 6.895 vagas — e a correção era
    mover um arquivo de lado.

    O reparo tem que tentar isto ANTES de reconstruir. Reconstruir
    resolveria, mas jogando fora vagas que não precisavam ser perdidas.

E o terceiro caso, que derrubou o próprio reparo:
    o ANALYZE cria a tabela interna `sqlite_stat1`, e recriá-la num
    banco novo dá "object name reserved for internal use".
"""
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

FERR = Path(__file__).resolve().parent.parent / "ferramentas"
SCRIPT = FERR / "reparar_banco.py"


def banco(caminho: Path, linhas: int = 60) -> Path:
    con = sqlite3.connect(caminho)
    con.executescript("""
        CREATE TABLE job_cluster (cluster_id TEXT PRIMARY KEY, title TEXT, notes TEXT);
        CREATE TABLE job_sighting (sighting_id TEXT PRIMARY KEY, cluster_id TEXT);
        CREATE TABLE employer (employer_canon TEXT PRIMARY KEY, employer TEXT);
        CREATE INDEX idx_t ON job_cluster(title);
    """)
    con.executemany("INSERT INTO job_cluster VALUES (?,?,NULL)",
                    [(f"c{i}", f"Cleaner {i}") for i in range(linhas)])
    con.executemany("INSERT INTO job_sighting VALUES (?,?)",
                    [(f"s{i}", f"c{i}") for i in range(linhas)])
    con.executemany("INSERT INTO employer VALUES (?,?)",
                    [(f"e{i}", f"Empresa {i}") for i in range(linhas)])
    con.commit()
    con.execute("ANALYZE")          # <- cria a sqlite_stat1
    con.commit()
    con.close()
    return caminho


def rodar(home: Path) -> subprocess.CompletedProcess:
    import os
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    return subprocess.run([sys.executable, str(SCRIPT)],
                          capture_output=True, text=True, env=env)


@pytest.fixture
def casa(tmp_path):
    (tmp_path / ".adelaide-jobs").mkdir()
    return tmp_path


def test_banco_bom_com_sqlite_stat1_nao_e_mexido(casa):
    """O ANALYZE roda a cada coleta. Não pode assustar o reparo."""
    alvo = casa / ".adelaide-jobs" / "jobs.db"
    banco(alvo)
    antes = alvo.read_bytes()
    r = rodar(casa)
    assert r.returncode == 0
    assert "esta integro" in r.stdout
    assert alvo.read_bytes() == antes


def test_wal_orfao_e_resolvido_sem_perder_nada(casa):
    """O caso de 02/09: mover o diário resolve, reconstruir seria perda."""
    alvo = casa / ".adelaide-jobs" / "jobs.db"
    banco(alvo, linhas=400)

    con = sqlite3.connect(alvo)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA wal_autocheckpoint=0")
    con.execute("UPDATE job_cluster SET notes='banco A'")
    con.commit()
    # Guarda o WAL antes de fechar: fechar limpo faz checkpoint e apaga
    # o arquivo. Copiar e devolver depois reproduz o orfao de proposito,
    # em vez de depender do coletor de lixo do Python.
    wal_de_a = (casa / "wal-de-A").write_bytes(
        (casa / ".adelaide-jobs" / "jobs.db-wal").read_bytes())
    con.close()

    time.sleep(1.1)
    # O banco B tem que ser DIFERENTE de A. Com o mesmo tamanho e o
    # mesmo layout de paginas, o WAL de A cai por cima de B sem
    # estragar nada — e o teste passaria sem testar coisa nenhuma.
    banco(casa / ".adelaide-jobs" / "outro.db", linhas=1500)
    alvo.write_bytes((casa / ".adelaide-jobs" / "outro.db").read_bytes())
    (casa / ".adelaide-jobs" / "outro.db").unlink()
    (casa / ".adelaide-jobs" / "jobs.db-wal").write_bytes(
        (casa / "wal-de-A").read_bytes())
    assert wal_de_a > 0

    r = rodar(casa)
    assert r.returncode == 0, r.stdout
    assert "Era isso" in r.stdout, r.stdout
    assert "Reconstruindo" not in r.stdout     # não podia ter reconstruído
    con = sqlite3.connect(f"file:{alvo}?mode=ro", uri=True)
    assert [m for (m,) in con.execute("PRAGMA integrity_check(1)")] == ["ok"]
    assert con.execute("SELECT count(*) FROM job_cluster").fetchone()[0] == 1500
    assert (casa / ".adelaide-jobs").glob("jobs.db-wal.orfao-*")


def test_corrupcao_de_verdade_reconstroi_e_guarda_o_cadastro(casa):
    """Reconstruir não pode jogar fora a tabela employer."""
    alvo = casa / ".adelaide-jobs" / "jobs.db"
    banco(alvo, linhas=2000)
    d = bytearray(alvo.read_bytes())
    # Longe do inicio: as primeiras paginas guardam o esquema, e sem
    # esquema nao ha o que reconstruir — seria testar outra coisa.
    alvo_off = len(d) // 2
    d[alvo_off:alvo_off + 2000] = b"\xff" * 2000
    alvo.write_bytes(bytes(d))

    r = rodar(casa)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "reserved for internal use" not in r.stdout + r.stderr
    con = sqlite3.connect(f"file:{alvo}?mode=ro", uri=True)
    assert [m for (m,) in con.execute("PRAGMA integrity_check(1)")] == ["ok"]
    tabelas = {t for (t,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "employer" in tabelas
    assert con.execute("SELECT count(*) FROM employer").fetchone()[0] == 2000
    assert list((casa / ".adelaide-jobs").glob("jobs.db.corrompido-*"))


def test_sem_banco_nao_e_erro(casa):
    r = rodar(casa)
    assert r.returncode == 0
    assert "nem existe" in r.stdout
