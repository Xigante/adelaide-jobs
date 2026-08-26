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
from .scoring import score as compute_score


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_doctor(args: argparse.Namespace) -> int:
    from . import doctor
    config_mod.load()          # carrega o .env
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
    return 0 if all_ok else 1


def cmd_collect(args: argparse.Namespace) -> int:
    from .pipeline import Pipeline
    cfg = config_mod.load()
    with Database(args.db) as db:
        report = Pipeline(cfg, db).run(sources=args.source or None)
        print(report.summary())
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
        print(f"{'score':>5}  {'vaga':<44} {'empregador':<22} {'local':<16} id")
        print("─" * 118)
        for r in rows:
            ghost = " 👻" if r["ghost_flag"] else ""
            print(f"{r['score']:>5}  {(r['title'] or '')[:44]:<44} "
                  f"{(r['employer'] or '')[:22]:<22} {(r['suburb'] or '')[:16]:<16} "
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
        print(f"{row['title']}  —  {row['employer'] or '(sem empregador)'}")
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
        path = export.to_csv(db, args.csv, threshold, args.limit)
        print(f"CSV: {path}")
        if args.sheets:
            try:
                print("Sheets:", export.to_sheets(db, threshold, args.limit))
            except Exception as exc:  # noqa: BLE001
                print(f"Sheets falhou: {exc}", file=sys.stderr)
                return 1
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

    e = sub.add_parser("export", help="exporta a fila")
    e.add_argument("--csv", default="exports/fila.csv")
    e.add_argument("--sheets", action="store_true", help="também escreve no Google Sheets")
    e.add_argument("--threshold", type=int, default=None)
    e.add_argument("--limit", type=int, default=500)
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
