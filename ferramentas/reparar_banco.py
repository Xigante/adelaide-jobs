"""Conserta o banco de vagas quando o SQLite diz que ele esta corrompido.

QUANDO USAR
    Quando a coleta morre com esta linha:
        sqlite3.DatabaseError: database disk image is malformed

O QUE ACONTECEU NO DIA 01/09/2026 (o caso que originou este arquivo)
    Uma pagina interna da arvore de job_cluster ficou com os rowids fora
    de ordem. O SQLite acha uma linha por busca binaria dentro da pagina;
    com a ordem errada, a busca desce na sub-arvore errada e o banco
    inteiro passa a mentir: `SELECT count(*)` dizia 5.278, um `SELECT *`
    devolvia 5.032, e o indice conhecia 5.526. Qualquer UPDATE estourava.

O QUE ESTE ARQUIVO FAZ
    Nao tenta consertar a pagina. Cria um banco novo em folha e copia
    para dentro dele tudo que ainda da para ler, nesta ordem:

      1. as tabelas, com o mesmo esquema do banco velho;
      2. as linhas de job_cluster que a leitura sequencial alcanca;
      3. as sightings — MENOS as orfas, isto e, as que apontam para um
         cluster que se perdeu. Isso e importante: se uma sighting orfa
         ficar no banco, `sighting_exists` devolve True na proxima coleta,
         o pipeline pula a vaga, e o cluster nunca volta. A vaga sumiria
         para sempre. Descartando a sighting, a proxima coleta rebusca a
         vaga e recria o cluster do zero;
      4. os indices, por ultimo, ja sobre dados corretos.

    No fim roda integrity_check no banco novo. So troca se der 'ok'. O
    banco velho e sempre guardado ao lado, com a data no nome.

O QUE SE PERDE
    As linhas de job_cluster cujas paginas foram sobrescritas. Elas
    voltam na proxima coleta se o anuncio ainda estiver no ar — o que
    se perde de verdade e o `first_seen` delas, ou seja, ha quanto tempo
    aquele anuncio esta publicado. E o sinal de "vaga fantasma".

COMO RODAR
    Duplo clique no REPARAR-BANCO.bat. Ou, no terminal:
        python reparar_banco.py
"""
import datetime
import pathlib
import shutil
import sqlite3
import sys

BANCO = pathlib.Path.home() / ".adelaide-jobs" / "jobs.db"


def diz(msg: str = "") -> None:
    print(msg, flush=True)


def integridade(caminho: pathlib.Path, limite: int = 5) -> list[str]:
    con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
    try:
        return [m for (m,) in con.execute(f"PRAGMA integrity_check({limite})")]
    finally:
        con.close()


def reconstruir(velho: pathlib.Path, novo: pathlib.Path) -> dict:
    if novo.exists():
        novo.unlink()
    v = sqlite3.connect(f"file:{velho}?mode=ro", uri=True)
    n = sqlite3.connect(novo)
    rel: dict = {}

    esquema = [r[0] for r in v.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")]
    indices = [r[0] for r in v.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")]
    for sql in esquema:
        n.execute(sql)
    n.execute(f"PRAGMA user_version = {v.execute('PRAGMA user_version').fetchone()[0]}")

    def copiar(tabela: str, aceita=None) -> tuple[int, int, int]:
        cols = [d[1] for d in v.execute(f"PRAGMA table_info({tabela})")]
        lista, marca = ", ".join(cols), ", ".join("?" * len(cols))
        vistos, guardar, repetidas, recusadas = set(), [], 0, 0
        cur = v.execute(f"SELECT {lista} FROM {tabela}")
        while True:                       # fetchmany: uma pagina ruim no
            try:                          # meio nao derruba o resto
                lote = cur.fetchmany(500)
            except sqlite3.DatabaseError:
                break
            if not lote:
                break
            for linha in lote:
                if linha[0] in vistos:
                    repetidas += 1
                    continue
                vistos.add(linha[0])
                if aceita and not aceita(linha):
                    recusadas += 1
                    continue
                guardar.append(linha)
        n.executemany(
            f"INSERT OR IGNORE INTO {tabela} ({lista}) VALUES ({marca})", guardar)
        return len(guardar), repetidas, recusadas

    rel["clusters"], rel["clusters_repetidos"], _ = copiar("job_cluster")
    vivos = {r[0] for r in n.execute("SELECT cluster_id FROM job_cluster")}
    rel["sightings"], _, rel["orfas"] = copiar(
        "job_sighting", aceita=lambda l: l[1] in vivos)
    try:
        rel["runs"], _, _ = copiar("run_log")
    except sqlite3.DatabaseError:
        rel["runs"] = 0
    n.commit()

    for sql in indices:
        n.execute(sql)
    n.execute("ANALYZE")
    n.commit()
    n.execute("VACUUM")
    rel["com_nota"] = n.execute(
        "SELECT count(*) FROM job_cluster WHERE score IS NOT NULL").fetchone()[0]
    n.close()
    v.close()
    return rel


def main() -> int:
    diz()
    diz("  Reparo do banco de vagas")
    diz("  " + "=" * 52)
    diz(f"  {BANCO}")
    diz()

    if not BANCO.exists():
        diz("  O banco nem existe ainda. Nao ha o que reparar:")
        diz("  rode o ATUALIZAR-VAGAS.bat para cria-lo.")
        return 0

    for sufixo in ("-wal", "-shm"):
        extra = BANCO.with_name(BANCO.name + sufixo)
        if extra.exists():
            diz(f"  [!] existe um {BANCO.name}{sufixo} ao lado. Feche qualquer")
            diz("      janela preta do adelaide-jobs antes de continuar.")
            diz()

    diz("  [..] Conferindo o banco. Demora alguns segundos.")
    try:
        problemas = integridade(BANCO)
    except sqlite3.DatabaseError as e:
        problemas = [f"nem abriu: {e}"]

    if problemas == ["ok"]:
        diz("  [ok] O banco esta integro. Nao mexi em nada.")
        diz()
        diz("  Se a coleta ainda falha, o problema e outro:")
        diz("  rode o ATUALIZAR-VAGAS.bat e me mande a ultima mensagem.")
        return 0

    diz("  [!!] O banco esta corrompido. Primeiras mensagens:")
    linhas = [x.strip() for m in problemas for x in str(m).splitlines() if x.strip()]
    for m in linhas[:4]:
        diz(f"       {m}")
    diz()

    hoje = datetime.date.today().strftime("%Y%m%d")
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
    except Exception as e:
        diz(f"  [ERRO] A reconstrucao falhou: {type(e).__name__}: {e}")
        diz("         Nada foi trocado. O banco velho continua onde estava.")
        return 1

    ok = integridade(novo)
    if ok != ["ok"]:
        diz("  [ERRO] O banco novo tambem saiu com defeito. Nao troquei nada.")
        diz(f"         {ok[:3]}")
        return 1

    shutil.move(str(BANCO), str(guardado))
    for sufixo in ("-wal", "-shm"):
        antigo = BANCO.with_name(BANCO.name + sufixo)
        if antigo.exists():
            shutil.move(str(antigo), str(guardado) + sufixo)
    shutil.move(str(novo), str(BANCO))
    for sufixo in ("-wal", "-shm"):
        sobra = BANCO.with_name(BANCO.name + sufixo)
        if sobra.exists():
            try:
                sobra.unlink()
            except OSError:
                diz(f"  [!] nao consegui remover {sobra.name}; apague na mao.")

    diz("  [ok] Pronto. O banco novo passou no teste de integridade.")
    diz()
    diz(f"       vagas (clusters)   {rel['clusters']}")
    diz(f"       com nota           {rel['com_nota']}")
    diz(f"       anuncios vistos    {rel['sightings']}")
    diz(f"       descartados orfaos {rel['orfas']}  (voltam na proxima coleta)")
    diz()
    diz("  Agora rode o ATUALIZAR-VAGAS.bat. As vagas que se perderam")
    diz("  voltam sozinhas, desde que o anuncio ainda esteja no ar.")
    diz()
    diz(f"  Se algo ficou estranho, o banco de antes esta em:")
    diz(f"      {guardado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
