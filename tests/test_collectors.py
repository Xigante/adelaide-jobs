"""Parsing dos coletores, contra fixture em disco — sem tocar na rede.

Os coletores separam `collect` (rede) de `parse` (puro) exatamente para
que esta camada seja testável sem depender de nenhum serviço externo.
"""

from adelaide_jobs.collectors.adzuna import AdzunaCollector
from adelaide_jobs.collectors.seek_v5 import SeekV5Collector
from adelaide_jobs.models import EmploymentType, Legitimacy


def test_adzuna_parses_all_results(adzuna_payload):
    jobs = [AdzunaCollector.parse(r) for r in adzuna_payload["results"]]
    assert len(jobs) == 3
    assert all(j.source == "adzuna" for j in jobs)
    assert all(j.legitimacy is Legitimacy.OFFICIAL_API for j in jobs)


def test_adzuna_extracts_location_and_coords(adzuna_payload):
    kitchen = AdzunaCollector.parse(adzuna_payload["results"][0])
    assert kitchen.suburb == "Adelaide"
    assert kitchen.state == "South Australia"
    assert kitchen.lat is not None


def test_adzuna_never_invents_currency(adzuna_payload):
    """Vaga sem salário não pode ganhar moeda inventada — é o defeito do
    JobSpy, que devolve 'USD' para tudo, inclusive na Austrália."""
    no_salary = AdzunaCollector.parse(adzuna_payload["results"][1])
    assert no_salary.salary_currency is None
    assert no_salary.salary_period is None

    with_salary = AdzunaCollector.parse(adzuna_payload["results"][0])
    assert with_salary.salary_currency == "AUD"
    assert with_salary.salary_period == "yearly"


def test_adzuna_parses_date(adzuna_payload):
    job = AdzunaCollector.parse(adzuna_payload["results"][0])
    assert job.posted_at is not None and job.posted_at.year == 2026


def test_adzuna_content_hash_is_stable(adzuna_payload):
    a = AdzunaCollector.parse(adzuna_payload["results"][0])
    b = AdzunaCollector.parse(adzuna_payload["results"][0])
    assert a.content_hash() == b.content_hash()


def test_seek_parses_casual(seek_payload):
    jobs = [SeekV5Collector.parse(i) for i in seek_payload["data"]]
    assert jobs[0].employment_type is EmploymentType.CASUAL
    assert jobs[0].suburb == "Adelaide"
    assert jobs[0].url.endswith("/84120001")


def test_seek_marks_legitimacy_against_tos(seek_payload):
    """A origem fica gravada em cada vaga: você sempre sabe de onde veio."""
    job = SeekV5Collector.parse(seek_payload["data"][0])
    assert job.legitimacy is Legitimacy.AGAINST_TOS


def test_seek_collector_refuses_when_disabled():
    collector = SeekV5Collector({"enabled": False})
    assert collector.safe_collect() == []
    assert any("desligado" in e for e in collector.errors)


def test_adzuna_collector_reports_missing_key(monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    collector = AdzunaCollector({})
    assert collector.safe_collect() == []
    assert any("ADZUNA_APP_ID" in e for e in collector.errors)
