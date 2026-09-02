"""Conserta o banco de vagas quando o SQLite diz que ele esta corrompido.

QUANDO USAR
    Quando a coleta parar com uma destas:
        database disk image is malformed
        invalid page number
        database is locked / not a database

A PRIMEIRA COISA QUE ELE TENTA NAO E RECONSTRUIR

    Na maioria das vezes o banco esta INTEIRO e o culpado e um arquivo
    ao lado: o `jobs.db-wal`.

    O SQLite escreve primeiro num diario chamado WAL e so depois passa
    o conteudo para o banco. Se o `jobs.db` for substituido por outro
    arquivo e o `-wal` do banco ANTIGO ficar para tras, na proxima
    abertura o SQLite aplica paginas velhas em cima do banco novo. O
    resultado e exatamente "invalid page number".

    Aconteceu aqui em 02/09/2026: o banco tinha 6.895 vagas, todas
    intactas, e o `-wal` ao lado era uma hora mais VELHO que ele.
    Bastou mover o `-wal` e o `-shm` para o lado.

    Como reconhecer: o `-wal` com data mais velha que o `.db`. Nunca e
    normal. WAL legitimo e sempre mais novo ou do mesmo instante.

    Por isso a ordem aqui e:
        1. ha WAL orfao?  move para o lado e testa de novo
        2. ainda quebrado? aí sim reconstroi
        3. so troca se o banco novo passar no teste

O QUE A RECONSTRUCAO FAZ
    Cria um banco novo em folha e copia tudo que ainda da para ler:
    todas as tabelas, inclusive o cadastro de empregadores, e depois os
    indices. Descarta as sightings orfas — as que apontam para um
    cluster que se perdeu. Isso e importante: se uma sighting orfa
    ficar, `sighting_exists` devolve True na proxima coleta, o pipeline
    pula a vaga, e o cluster nunca volta. A vaga sumiria para sempre.

O QUE NUNCA E APAGADO
    Nada. O banco de antes fica ao lado com a data no nome, e o WAL
    movido tambem.

RODAR
    Duplo clique no REPARAR-BANCO.bat, ou:
        python reparar_banco.py
"""
from __future__ import annotations

import datetime
import pathlib
import shutil
import sqlite3
import sys

BANCO = pathlib.Path.home() / ".adelaide-jobs" / "jobs.db"

# sqlite_stat1 e companhia sao internas: o SQLite recusa um CREATE TABLE
# com esses nomes. O ANALYZE que roda depois da coleta cria a
# sqlite_stat1, e foi ela que derrubou a reconstrucao em 02/09/2026 com
# "object name reserved for internal use".
def _propria_do_sqlite(nome: str) -> bool:
    return nome.lower().startswith("sqlite_")


def diz(msg: str = "") -> None:
    print(msg, flush=True)


def integridade(caminho: pathlib.Path, limite: int = 5) -> list[str]:
    """['ok'] se estiver bom, senao as mensagens do SQLite."""
    try:
        con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    except sqlite3.DatabaseError as exc:
        return [f"nem abriu: {exc}"]
    try:
        return [m for (m,) in con.execute(f"PRAGMA integrity_check({limite})")]
    except sqlite3.DatabaseError as exc:
        return [f"nem abriu: {exc}"]
    finally:
        con.close()


def mover_diario(banco: pathlib.Path, sufixo: str) -> list[str]:
    """Tira o -wal e o -shm da frente. Move, nunca apaga."""
    movidos = []
    for parte in ("-wal", "-shm"):
        arq = banco.with_name(banco.name + parte)
        if not arq.exists():
            continue
        destino = banco.with_name(f"{banco.name}{parte}.{sufixo}")
        i = 2
        while destino.exists():
            destino = banco.with_name(f"{banco.name}{parte}.{sufixo}-{i}")
            i += 1
        shutil.move(str(arq), str(destino))
        movidos.append(destino.name)
    return movidos


def reconstruir(velho: pathlib.Path, novo: pathlib.Path) -> dict:
    if novo.exists():
        novo.unlink()
    v = sqlite3.connect(f"file:{velho}?mode=ro", uri=True)
    n = sqlite3.connect(novo)
    rel: dict = {"tabelas": {}, "orfas": 0}

    tabelas = [(nome, sql) for nome, sql in v.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
        if not _propria_do_sqlite(nome)]
    indices = [sql for (nome, sql) in v.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        if not _propria_do_sqlite(nome)]
    for _, sql in tabelas:
        n.execute(sql)
    n.execute(f"PRAGMA user_version = {v.execute('PRAGMA user_version').fetchone()[0]}")

    def copiar(tabela: str, aceita=None) -> tuple[int, int]:
        cols = [d[1] for d in v.execute(f"PRAGMA table_info({tabela})")]
        lista, marca = ", ".join(cols), ", ".join("?" * len(cols))
        vistos, guardar, recusadas = set(), [], 0
        cur = v.execute(f"SELECT {lista} FROM {tabela}")
        while True:                        # fetchmany: uma pagina ruim no
            try:                           # meio nao derruba o resto
                lote = cur.fetchmany(500)
            except sqlite3.DatabaseError:
                break
            if not lote:
                break
            for linha in lote:
                if linha[0] in vistos:
                    continue
                vistos.add(linha[0])
                if aceita and not aceita(linha):
                    recusadas += 1
                    continue
                guardar.append(linha)
        n.executemany(
            f"INSERT OR IGNORE INTO {tabela} ({lista}) VALUES ({marca})", guardar)
        return len(guardar), recusadas

    # job_cluster primeiro: e ele que diz quais sightings sao orfas.
    ordem = [t for t, _ in tabelas]
    if "job_cluster" in ordem:
        ordem.remove("job_cluster")
        ordem.insert(0, "job_cluster")

    vivos: set = set()
    for tabela in ordem:
        try:
            if tabela == "job_sighting" and vivos:
                qtd, orfas = copiar(tabela, aceita=lambda l: l[1] in vivos)
                rel["orfas"] = orfas
            else:
                qtd, _ = copiar(tabela)
        except sqlite3.DatabaseError as exc:
            diz(f"       [!] {tabela}: {exc}")
            qtd = 0
        rel["tabelas"][tabela] = qtd
        if tabela == "job_cluster":
            vivos = {r[0] for r in n.execute("SELECT cluster_id FROM job_cluster")}
    n.commit()

    for sql in indices:
        try:
            n.execute(sql)
        except sqlite3.DatabaseError as exc:
            diz(f"       [!] índice: {exc}")
    n.commit()
    n.execute("VACUUM")
    n.close()
    v.close()
    return rel


def main() -> int:
    diz()
    diz("  Reparo do banco de vagas")
    diz("  " + "=" * 56)
    diz(f"  {BANCO}")
    diz()

    if not BANCO.exists():
        diz("  O banco nem existe ainda. Nao ha o que reparar:")
        diz("  rode o ATUALIZAR-VAGAS.bat para cria-lo.")
        return 0

    hoje = datetime.date.today().strftime("%Y%m%d")

    # ── passo 1: o banco esta bom? ──────────────────────────────────
    diz("  [..] Conferindo o banco. Demora alguns segundos.")
    problemas = integridade(BANCO)
    if problemas == ["ok"]:
        sobra = [p for p in ("-wal", "-shm")
                 if BANCO.with_name(BANCO.name + p).exists()]
        diz("  [ok] O banco esta integro. Nao mexi em nada.")
        if sobra:
            diz()
            diz(f"       (existe um {BANCO.name}{sobra[0]} ao lado, mas o banco")
            diz("        abre normal — e um WAL em uso, nao um orfao.)")
        diz()
        diz("  Se a coleta ainda falha, o problema e outro:")
        diz("  rode o ATUALIZAR-VAGAS.bat e me mande a ultima mensagem.")
        return 0

    diz("  [!!] O banco nao abriu. Primeiras mensagens:")
    for linha in [x.strip() for m in problemas for x in str(m).splitlines() if x.strip()][:4]:
        diz(f"       {linha}")
    diz()

    # ── passo 2: e um WAL orfao? ────────────────────────────────────
    wal = BANCO.with_name(BANCO.name + "-wal")
    if wal.exists():
        mais_velho = wal.stat().st_mtime < BANCO.stat().st_mtime
        diz("  [..] Existe um jobs.db-wal ao lado" +
            (" e ele e MAIS VELHO que o banco." if mais_velho else "."))
        if mais_velho:
            diz("       Isso nunca e normal: WAL legitimo e sempre mais novo.")
            diz("       E o diario de um banco ANTERIOR sendo aplicado neste.")
        diz("  [..] Movendo o diario para o lado e testando de novo...")
        movidos = mover_diario(BANCO, f"orfao-{hoje}")
        problemas = integridade(BANCO)
        if problemas == ["ok"]:
            diz("  [ok] Era isso. O banco esta inteiro — nao perdi nada.")
            diz()
            for m in movidos:
                diz(f"       guardei {m}")
            diz()
            diz("  Pode rodar o ATUALIZAR-VAGAS.bat.")
            return 0
        diz("  [..] Nao era so o diario. Vou reconstruir.")
        diz()

    # ── passo 3: reconstruir ────────────────────────────────────────
    guardado = BANCO.with_name(f"{BANCO.name}.corrompido-{hoje}")
    i = 2
    while guardado.exists():
        guardado = BANCO.with_name(f"{BANCO.name}.corrompido-{hoje}-{i}")
        i += 1

    novo = BANCO.with_name("jobs-reparado.db")
    diz("  [..] Reconstruindo. Isso nao apaga nada — o banco velho fica")
    diz(f"       guardado como {guardado.name}")
    try:
        rel = reconstruir(BANCO, novo)
    except Exception as exc:                                  # noqa: BLE001
        diz(f"  [ERRO] A reconstrucao falhou: {type(exc).__name__}: {exc}")
        diz("         Nada foi trocado. O banco velho continua onde estava.")
        return 1

    ok = integridade(novo)
    if ok != ["ok"]:
        diz("  [ERRO] O banco novo tambem saiu com defeito. Nao troquei nada.")
        diz(f"         {ok[:3]}")
        return 1

    shutil.move(str(BANCO), str(guardado))
    mover_diario(BANCO, f"do-corrompido-{hoje}")
    shutil.move(str(novo), str(BANCO))

    diz("  [ok] Pronto. O banco novo passou no teste de integridade.")
    diz()
    for tabela, qtd in rel["tabelas"].items():
        diz(f"       {tabela:16s} {qtd}")
    if rel["orfas"]:
        diz(f"       {'descartados':16s} {rel['orfas']} anuncios orfaos "
            f"(voltam na proxima coleta)")
    diz()
    diz("  Agora rode o ATUALIZAR-VAGAS.bat. O que se perdeu volta")
    diz("  sozinho, desde que o anuncio ainda esteja no ar.")
    diz()
    diz(f"  O banco de antes esta em:")
    diz(f"      {guardado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
