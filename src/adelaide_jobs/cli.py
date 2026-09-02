"""Interface de linha de comando.

    adelaide-jobs doctor            o que a sua rede alcança
    adelaide-jobs collect           coleta das fontes ligadas
    adelaide-jobs score             (re)pontua o que está pendente
    adelaide-jobs queue             mostra a fila
    adelaide-jobs why <cluster_id>  abre a conta do score de uma vaga
    adelaide-jobs export            CSV e/ou Google Sheets
    adelaide-jobs stats             estado do banco
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import config as config_mod
from .db import DEFAULT_DB, Database
from .models import Dimensions
from .scoring import nota, score as compute_score


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def _banco_integro(caminho: str | Path) -> bool:
    """Confere o banco antes de qualquer comando que escreva nele.

    Em 01/09/2026 uma página interna da árvore de `job_cluster` ficou com
    os rowids fora de ordem. O SQLite acha uma linha por busca binária
    dentro da página; com a ordem errada ele desce na sub-árvore errada e
    o banco passa a mentir — `count(*)` dizia 5.278, um `SELECT *`
    devolvia 5.032, e o índice conhecia 5.526. A coleta rodou seis
    minutos, gastou cota da Adzuna, e só morreu no primeiro UPDATE, com
    um traceback de SQLite que não diz o que fazer.

    Custa 0,02 s num banco de 10 MB. Vale sempre a pena.
    """
    import sqlite3
    p = Path(caminho)
    if not p.exists():
        return True                       # ainda não existe: normal
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            problemas = [m for (m,) in con.execute("PRAGMA integrity_check(1)")]
        finally:
            con.close()
    except sqlite3.DatabaseError as exc:
        problemas = [str(exc)]
    if problemas == ["ok"]:
        return True
    print()
    print("  O BANCO DE VAGAS ESTÁ CORROMPIDO. Parei antes de gastar cota.")
    print()
    for linha in str(problemas[0]).splitlines()[:3]:
        print(f"    {linha.strip()}")
    print()
    print("  O conserto: rode o REPARAR-BANCO.bat, na pasta australia.")
    print("  Ele reconstrói o banco com tudo que ainda dá para ler e")
    print("  guarda o antigo ao lado, com a data no nome. Depois é só")
    print("  rodar o ATUALIZAR-VAGAS.bat de novo.")
    print()
    return False


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import doctor
    config_mod.load()          # carrega o .env
    banco_ok = _banco_integro(args.db)
    checks, all_ok = doctor.run(skip_network=args.offline)
    for c in checks:
        print(c.line())
    print()
    seek = next((c for c in checks if c.name.startswith("SEEK")), None)
    if seek:
        if seek.ok:
            print("A v5 do SEEK responde do seu IP. A decisão agora é sobre os")
            print("termos de uso, não sobre viabilidade — leia o cabeçalho de")
            print("collectors/seek_v5.py antes de ligar em config/sources.yaml.")
        else:
            print("A v5 do SEEK não respondeu. Os alertas de e-mail continuam")
            print("sendo o caminho — e são o de menor risco de qualquer forma.")
    return 0 if (all_ok and banco_ok) else 1


def cmd_collect(args: argparse.Namespace) -> int:
    from . import export
    from .pipeline import Pipeline
    cfg = config_mod.load()
    if not _banco_integro(args.db):
        return 1
    with Database(args.db) as db:
        report = Pipeline(cfg, db).run(sources=args.source or None)
        print(report.summary())
        if args.no_export:
            return 0
        # Exporta sempre. O banco fica escondido no perfil do usuário de
        # propósito (SQLite não funciona em pasta sincronizada), então sem
        # isto ninguém acha o resultado.
        csv_path = export.to_csv(db, "exports/fila.csv", cfg.queue_threshold)
        html_path = export.to_html(db, "exports/vagas.html", cfg.queue_threshold)
        export.empregadores_to_csv(db, "exports/empregadores.csv")
        emp_json = export.empregadores_to_json(db, "exports/empregadores.json")
    print()
    print("─" * 62)
    print("  SEUS RESULTADOS")
    print("─" * 62)
    print(f"  Abra no navegador : {html_path.resolve()}")
    print(f"  Planilha (Excel)  : {csv_path.resolve()}")
    print(f"  Cadastro de empresas: {emp_json.resolve()}")
    print(f"  Banco completo    : {Path(args.db).resolve()}")
    print()
    print("  Na linha de comando:  adelaide-jobs queue")
    print()
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    from .pipeline import Pipeline
    cfg = config_mod.load()
    with Database(args.db) as db:
        if args.rescore:
            with db.tx():
                db.conn.execute("UPDATE job_cluster SET verdict=NULL, score=NULL")
        report = Pipeline(cfg, db).score_pending()
        print(report.summary())
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    cfg = config_mod.load()
    threshold = args.threshold if args.threshold is not None else cfg.queue_threshold
    with Database(args.db) as db:
        rows = db.queue(threshold, args.limit)
        if not rows:
            print("Fila vazia. Rode `collect` primeiro, ou baixe o --threshold.")
            return 0
        print(f"{'nota':>4} {'pts':>4}  {'vaga':<42} {'empregador':<22} {'local':<14} id")
        print("─" * 118)
        for r in rows:
            letra, _ = nota(r["score"])
            ghost = " 👻" if r["ghost_flag"] else ""
            print(f"{letra:>4} {r['score']:>4}  {(r['title'] or '')[:42]:<42} "
                  f"{(r['employer'] or '')[:22]:<22} {(r['suburb'] or '')[:14]:<14} "
                  f"{r['cluster_id'][:8]}{ghost}")
    return 0


def cmd_why(args: argparse.Namespace) -> int:
    """A conta aberta de uma vaga. Sem isto o score é opinião."""
    cfg = config_mod.load()
    with Database(args.db) as db:
        row = db.conn.execute(
            "SELECT * FROM job_cluster WHERE cluster_id LIKE ?", (args.cluster_id + "%",)
        ).fetchone()
        if not row:
            print(f"Cluster {args.cluster_id!r} não encontrado.")
            return 1
        letra, acao = nota(row["score"], row["verdict"] == "BLOCKED")
        print(f"{row['title']}  —  {row['employer'] or '(sem empregador)'}")
        print(f"nota {letra}  ({acao})")
        print(f"{row['url']}\n")
        if row["verdict"] == "BLOCKED":
            print(f"BLOQUEADA: {row['blocked_reason']}")
            return 0
        if not row["dims_json"]:
            print("Ainda não pontuada. Rode `score`.")
            return 0
        dims = Dimensions(**json.loads(row["dims_json"]))
        breakdown = compute_score(
            dims, cfg.weights,
            class_pattern=cfg.class_pattern,
            english_level=cfg.english_level,
            ghost=bool(row["ghost_flag"]),
            ghost_penalty=cfg.ghost_penalty,
            multi_source=row["source_count"] or 1,
            version=cfg.score_version,
        )
        print(breakdown.explain())
        print(f"\nvista {row['sighting_count']}× em {row['source_count']} fonte(s), "
              f"{row['repost_count']} repostagem(ns)")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    from . import export
    cfg = config_mod.load()
    threshold = args.threshold if args.threshold is not None else cfg.queue_threshold
    with Database(args.db) as db:
        path = export.to_csv(db, args.csv, threshold, args.limit or 500)
        print(f"Planilha   : {path.resolve()}")
        pagina = export.to_html(db, args.html, threshold, args.limit or 3000)
        print(f"Navegador  : {pagina.resolve()}")
        # O cadastro de empregadores. Sai sempre: é barato e é o que
        # alimenta a aba Empresas do material.
        db.rebuild_employers()
        base = Path(args.csv).parent
        emp_csv = export.empregadores_to_csv(db, base / "empregadores.csv")
        emp_json = export.empregadores_to_json(db, base / "empregadores.json")
        print(f"Empresas   : {emp_csv.resolve()}")
        print(f"             {emp_json.resolve()}")
        if args.sheets:
            try:
                print("Sheets:", export.to_sheets(db, threshold, args.limit))
            except Exception as exc:  # noqa: BLE001
                print(f"Sheets falhou: {exc}", file=sys.stderr)
                return 1
    return 0


def cmd_onde(args: argparse.Namespace) -> int:
    """Onde está cada arquivo. Existe porque a pergunta é inevitável."""
    cfg_dir = config_mod.CONFIG_DIR
    proj = cfg_dir.parent
    itens = [
        ("Vagas encontradas (banco)", Path(args.db)),
        ("Relatório para abrir no navegador", proj / "exports" / "vagas.html"),
        ("Planilha para o Excel", proj / "exports" / "fila.csv"),
        ("Suas chaves", proj / ".env"),
        ("Seu perfil e os pesos", cfg_dir / "profile.yaml"),
        ("As fontes de coleta", cfg_dir / "sources.yaml"),
    ]
    largura = max(len(r) for r, _ in itens)
    print()
    for rotulo, caminho in itens:
        caminho = caminho.resolve()
        marca = "  " if caminho.exists() else " *"
        print(f"{marca}{rotulo:<{largura}}  {caminho}")
    print()
    if any(not c.resolve().exists() for _, c in itens):
        print("  * ainda não existe — é criado quando você roda `collect`")
        print()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    with Database(args.db) as db:
        s = db.stats()
        print(f"clusters   {s['clusters']}")
        print(f"sightings  {s['sightings']}")
        print(f"pontuadas  {s['scored']}")
        print(f"bloqueadas {s['blocked']}")
        print(f"fantasmas  {s['ghosts']}")
        if s["sources"]:
            print("\npor fonte:")
            for src, n in s["sources"]:
                print(f"  {src:<16} {n}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adelaide-jobs",
        description="Pipeline pessoal de descoberta de vagas em Adelaide, SA.",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--db", default=str(DEFAULT_DB), help=f"caminho do SQLite (padrão: {DEFAULT_DB})")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("doctor", help="checa chaves, pacotes e o que a rede alcança")
    d.add_argument("--offline", action="store_true", help="pula os testes de rede")
    d.set_defaults(func=cmd_doctor)

    c = sub.add_parser("collect", help="coleta das fontes ligadas e pontua")
    c.add_argument("--source", action="append", help="limita a esta fonte (pode repetir)")
    c.add_argument("--no-export", action="store_true", help="não gerar CSV nem HTML no fim")
    c.set_defaults(func=cmd_collect)

    s = sub.add_parser("score", help="pontua o que está pendente")
    s.add_argument("--rescore", action="store_true", help="apaga e recalcula tudo")
    s.set_defaults(func=cmd_score)

    q = sub.add_parser("queue", help="mostra a fila de candidatura")
    q.add_argument("--threshold", type=int, default=None)
    q.add_argument("--limit", type=int, default=40)
    q.set_defaults(func=cmd_queue)

    w = sub.add_parser("why", help="abre a conta do score de uma vaga")
    w.add_argument("cluster_id")
    w.set_defaults(func=cmd_why)

    o = sub.add_parser("onde", help="mostra onde ficam os arquivos")
    o.set_defaults(func=cmd_onde)

    e = sub.add_parser("export", help="exporta a fila")
    e.add_argument("--csv", default="exports/fila.csv")
    e.add_argument("--html", default="exports/vagas.html")
    e.add_argument("--sheets", action="store_true", help="também escreve no Google Sheets")
    e.add_argument("--threshold", type=int, default=None)
    # Sem valor, cada saída usa o limite que faz sentido para ela:
    # a planilha é fila de trabalho (500 cabe numa manhã), o HTML é
    # o relatório inteiro para navegar (3.000).
    #
    # Com default=500 aqui, o ATUALIZAR-VAGAS.bat truncava o
    # relatório todo dia sem avisar: `collect` escrevia 3.000 linhas
    # e o `export` logo depois sobrescrevia com 500. Ele abria o
    # relatório e via 500 de 7.819.
    e.add_argument("--limit", type=int, default=None)
    e.set_defaults(func=cmd_export)

    st = sub.add_parser("stats", help="estado do banco")
    st.set_defaults(func=cmd_stats)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("\ninterrompido", file=sys.stderr)
        return 130
    except FileNotFoundError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
