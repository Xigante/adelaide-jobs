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
