"""Empregadores diretos, pelos endpoints públicos dos ATS deles.

Esta é a via mais limpa que existe: são os próprios empregadores
publicando, sem intermediário e sem termo violado.

Usa `ats-scrapers` (MIT) quando instalado — 70+ ATS numa interface só,
com canário noturno que detecta endpoint quebrado em 24h. Instale com:

    pip install "adelaide-jobs[ats]"

Quatro dos alvos de Adelaide caem em Workday ou SuccessFactors, ambos já
implementados lá: Bunnings, Hungry Jack's, Flinders, Coles e Woolworths.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import EmploymentType, Job, Legitimacy
from .base import BaseCollector, CollectorError, register


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


@register
class AtsCollector(BaseCollector):
    name = "ats"
    legitimacy = Legitimacy.PUBLIC_ENDPOINT
    min_interval = 1.5

    def collect(self) -> list[Job]:
        try:
            from ats_scrapers.scrapers.smartrecruiters import SmartRecruitersScraper
            from ats_scrapers.scrapers.workday import WorkdayScraper
        except ImportError as exc:
            raise CollectorError(
                'ats-scrapers não instalado. Rode: pip install "adelaide-jobs[ats]"'
            ) from exc

        targets: list[dict[str, Any]] = self.config.get("targets") or []
        loc_filter = [s.lower() for s in (self.config.get("location_filter") or [])]
        jobs: list[Job] = []

        for target in targets:
            kind = target.get("kind")
            label = target.get("name", "?")
            self.throttle()
            try:
                if kind == "workday":
                    scraper = WorkdayScraper.from_url(target["url"])
                elif kind == "smartrecruiters":
                    scraper = SmartRecruitersScraper(target["slug"])
                else:
                    self.note_error(f"{label}: tipo de ATS desconhecido {kind!r}")
                    continue
                raw_jobs = scraper.fetch()
            except Exception as exc:  # noqa: BLE001
                self.note_error(f"{label}: {type(exc).__name__}: {exc}")
                continue

            kept = 0
            for rj in raw_jobs:
                job = self.parse(rj, label, kind)
                if loc_filter and not self._matches_location(job, loc_filter):
                    continue
                jobs.append(job)
                kept += 1
            self.note_info(f"{label}: {kept}/{len(raw_jobs)} vagas em SA")
        return jobs

    def note_info(self, msg: str) -> None:
        import logging
        logging.getLogger(__name__).info("[%s] %s", self.name, msg)

    @staticmethod
    def _matches_location(job: Job, needles: list[str]) -> bool:
        haystack = f" {job.suburb or ''} {job.state or ''} {job.location_text} ".lower()
        return any(n in haystack for n in needles)

    @classmethod
    def parse(cls, raw: Any, employer_label: str, kind: str) -> Job:
        """Converte o `Job` do ats-scrapers para o nosso.

        Recebe o objeto do jeito que vier — acesso defensivo por getattr,
        porque o schema deles pode mudar entre versões e a falha não pode
        derrubar o run.
        """
        get = lambda k, d=None: getattr(raw, k, d)  # noqa: E731
        location = get("location") or ""
        suburb = get("city") or (location.split(",")[0].strip() if location else None)

        return Job(
            source=f"ats:{kind}",
            source_id=str(get("id") or get("global_id") or get("url") or ""),
            title=str(get("title") or "").strip(),
            url=str(get("url") or get("apply_url") or ""),
            employer=str(get("company_name") or employer_label),
            description=str(get("description") or ""),
            suburb=suburb,
            state=get("region") or get("state"),
            postcode=get("postal_code"),
            lat=get("lat"),
            lon=get("lon"),
            employment_type=EmploymentType.UNKNOWN,
            posted_at=_as_date(get("posted_at") or get("published_at")),
            legitimacy=cls.legitimacy,
            raw={"ats": kind},
        )
