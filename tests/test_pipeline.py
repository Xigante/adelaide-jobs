"""Integração: fixture → dedup → knockout → score → fila → CSV.

Sem rede. É o teste que prova que as peças se encaixam.
"""

from adelaide_jobs.collectors.adzuna import AdzunaCollector
from adelaide_jobs.collectors.seek_v5 import SeekV5Collector
from adelaide_jobs.pipeline import Pipeline


def test_end_to_end(cfg, db, adzuna_payload, seek_payload):
    jobs = [AdzunaCollector.parse(r) for r in adzuna_payload["results"]]
    jobs += [SeekV5Collector.parse(i) for i in seek_payload["data"]]

    pipe = Pipeline(cfg, db)
    report = pipe.ingest(jobs)
    assert report.collected == 5
    assert report.new_clusters == 5

    report = pipe.score_pending(report)
    # O "Senior Restaurant Manager" tem que ser bloqueado.
    assert report.blocked >= 1
    assert "SENIOR_ROLE" in report.knockouts or "FULL_TIME_ONLY" in report.knockouts
    assert report.scored == 5 - report.blocked

    queue = db.queue(threshold=50, limit=50)
    assert queue, "a fila não pode sair vazia com estas fixtures"
    titles = [r["title"] for r in queue]
    assert any("Kitchen" in t or "Night Fill" in t for t in titles)
    # ordenada por score, melhor primeiro
    scores = [r["score"] for r in queue]
    assert scores == sorted(scores, reverse=True)


def test_reingest_is_idempotent(cfg, db, adzuna_payload):
    jobs = [AdzunaCollector.parse(r) for r in adzuna_payload["results"]]
    pipe = Pipeline(cfg, db)
    pipe.ingest(jobs)
    first = db.stats()["clusters"]

    second_report = pipe.ingest(jobs)
    assert second_report.already_seen == len(jobs)
    assert db.stats()["clusters"] == first, "reingestão não pode duplicar cluster"


def test_same_job_from_two_sources_merges(cfg, db, adzuna_payload):
    """A mesma vaga no Adzuna e no SEEK tem que virar UM cluster —
    senão você se candidata duas vezes."""
    base = AdzunaCollector.parse(adzuna_payload["results"][1])   # Coles night fill
    twin = AdzunaCollector.parse(adzuna_payload["results"][1])
    twin.source = "seek_v5"
    twin.source_id = "99999"
    twin.title = "Nightfill Team Member - URGENT"
    twin.url = "https://www.seek.com.au/job/99999"

    pipe = Pipeline(cfg, db)
    pipe.ingest([base, twin])
    assert db.stats()["clusters"] == 1
    assert db.stats()["sightings"] == 2

    row = db.conn.execute("SELECT source_count FROM job_cluster").fetchone()
    assert row["source_count"] == 2


def test_blocked_jobs_keep_their_reason(cfg, db, adzuna_payload):
    senior = AdzunaCollector.parse(adzuna_payload["results"][2])
    pipe = Pipeline(cfg, db)
    pipe.ingest([senior])
    pipe.score_pending()
    row = db.conn.execute(
        "SELECT verdict, blocked_reason FROM job_cluster"
    ).fetchone()
    assert row["verdict"] == "BLOCKED"
    assert row["blocked_reason"]


def test_csv_export(cfg, db, adzuna_payload, tmp_path):
    from adelaide_jobs import export
    pipe = Pipeline(cfg, db)
    pipe.ingest([AdzunaCollector.parse(r) for r in adzuna_payload["results"]])
    pipe.score_pending()
    path = export.to_csv(db, tmp_path / "fila.csv", threshold=40)
    content = path.read_text(encoding="utf-8-sig")
    assert "score" in content.splitlines()[0]
    assert len(content.splitlines()) >= 2


# ── O bug de 30/08/2026 ─────────────────────────────────────────────
# `score_pending` chamava `db.unscored()` uma vez só, e `unscored`
# devolve no máximo 500 linhas. Com 7 vagas no banco nenhum teste
# pegava. Na primeira coleta real vieram 6.970 vagas, 5.526 clusters, e
# 5.026 ficaram sem nota — fora do relatório, sem erro nenhum.
#
# Este teste enche o banco com MAIS que um lote de propósito.

def test_pontua_alem_de_um_lote(tmp_path):
    """Com 1.200 vagas, as 1.200 têm que sair com nota — não 500."""
    from adelaide_jobs import config as config_mod
    from adelaide_jobs.db import Database
    from adelaide_jobs.models import Job
    from adelaide_jobs.pipeline import Pipeline

    cfg = config_mod.load()
    with Database(tmp_path / "b.db") as db:
        vagas = [
            Job(source="adzuna", source_id=f"v{i}",
                title=f"Kitchen Hand {i}", url=f"https://x/{i}",
                employer=f"Empregador {i}", description="Casual kitchen work.",
                suburb="Adelaide", state="SA")
            for i in range(1200)
        ]
        Pipeline(cfg, db).run_offline(vagas) if hasattr(Pipeline, "run_offline") \
            else Pipeline(cfg, db).ingest(vagas)
        rel = Pipeline(cfg, db).score_pending()

        sem_nota = db.conn.execute(
            "SELECT COUNT(*) c FROM job_cluster WHERE verdict IS NULL"
        ).fetchone()["c"]
        assert sem_nota == 0, f"{sem_nota} vagas ficaram sem nota"
        assert rel.scored + rel.blocked == 1200


def test_unscored_devolve_um_lote_nao_tudo(tmp_path):
    """O teto de `unscored` é o tamanho do lote, e continua existindo —
    é ele que impede de carregar seis mil linhas de uma vez."""
    from adelaide_jobs import config as config_mod
    from adelaide_jobs.db import Database
    from adelaide_jobs.models import Job
    from adelaide_jobs.pipeline import Pipeline

    cfg = config_mod.load()
    with Database(tmp_path / "b.db") as db:
        Pipeline(cfg, db).ingest([
            Job(source="adzuna", source_id=f"v{i}", title=f"Cleaner {i}",
                url=f"https://x/{i}", employer=f"E{i}", description="Casual.",
                suburb="Adelaide", state="SA")
            for i in range(700)
        ])
        assert len(db.unscored()) == 500
        assert len(db.unscored(lote=50)) == 50
