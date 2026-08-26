"""Adzuna — a única API oficial e gratuita do conjunto.

Registro instantâneo em https://developer.adzuna.com/. Limites publicados
nos termos: 25/min, 250/dia, 1.000/semana, 2.500/mês, e atribuição
"Jobs by Adzuna" obrigatória se você exibir os dados em público.

Na Austrália a Adzuna agrega SEEK, Indeed e outros — ou seja, você alcança
Adelaide indiretamente sem violar termo de ninguém. É a base defensável do
pipeline, e é por onde começar.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import httpx

from ..models import EmploymentType, Job, Legitimacy
from .base import USER_AGENT, BaseCollector, CollectorError, register

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"


@register
class AdzunaCollector(BaseCollector):
    name = "adzuna"
    legitimacy = Legitimacy.OFFICIAL_API
    min_interval = 3.0

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.app_id = os.getenv("ADZUNA_APP_ID", "")
        self.app_key = os.getenv("ADZUNA_APP_KEY", "")

    def collect(self) -> list[Job]:
        if not self.app_id or not self.app_key:
            raise CollectorError(
                "ADZUNA_APP_ID / ADZUNA_APP_KEY não definidos. "
                "Pegue a chave grátis em https://developer.adzuna.com/ e copie "
                ".env.example para .env"
            )

        country = self.config.get("country", "au")
        where = self.config.get("where", "Adelaide")
        distance = self.config.get("distance_km", 25)
        per_page = int(self.config.get("results_per_page", 50))
        max_pages = int(self.config.get("max_pages", 2))
        queries: list[str] = self.config.get("queries") or [""]

        jobs: list[Job] = []
        with httpx.Client(timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
            for query in queries:
                for page in range(1, max_pages + 1):
                    self.throttle()
                    params = {
                        "app_id": self.app_id,
                        "app_key": self.app_key,
                        "results_per_page": per_page,
                        "what": query,
                        "where": where,
                        "distance": distance,
                        "content-type": "application/json",
                    }
                    url = BASE_URL.format(country=country, page=page)
                    try:
                        resp = client.get(url, params=params)
                    except httpx.HTTPError as exc:
                        self.note_error(f"rede em {query!r} p{page}: {exc}")
                        break
                    if resp.status_code == 429:
                        self.note_error("429 — limite da Adzuna atingido, parando")
                        return jobs
                    if resp.status_code != 200:
                        self.note_error(f"HTTP {resp.status_code} em {query!r} p{page}")
                        break

                    payload = resp.json()
                    results = payload.get("results") or []
                    jobs.extend(self.parse(r, query) for r in results)
                    if len(results) < per_page:
                        break
        return jobs

    # Separado de `collect` de propósito: é isto que os testes exercitam,
    # com fixture salva em disco, sem tocar na rede.
    @classmethod
    def parse(cls, item: dict[str, Any], query: str = "") -> Job:
        loc = item.get("location") or {}
        areas = loc.get("area") or []
        suburb = areas[-1] if areas else None
        state = areas[1] if len(areas) > 1 else None

        contract = (item.get("contract_time") or "").lower()
        emp = {
            "part_time": EmploymentType.PART_TIME,
            "full_time": EmploymentType.FULL_TIME,
        }.get(contract, EmploymentType.UNKNOWN)
        if (item.get("contract_type") or "").lower() == "contract":
            emp = EmploymentType.CONTRACT

        posted = None
        if raw_date := item.get("created"):
            try:
                posted = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date()
            except ValueError:
                pass

        smin, smax = item.get("salary_min"), item.get("salary_max")
        return Job(
            source=cls.name,
            source_id=str(item.get("id", "")),
            title=(item.get("title") or "").strip(),
            url=item.get("redirect_url", ""),
            employer=((item.get("company") or {}).get("display_name") or None),
            description=item.get("description") or "",
            suburb=suburb,
            state=state,
            lat=item.get("latitude"),
            lon=item.get("longitude"),
            salary_min=smin,
            salary_max=smax,
            # A Adzuna devolve salário ANUALIZADO. Não invente moeda nem
            # período quando não há valor.
            salary_currency="AUD" if (smin or smax) else None,
            salary_period="yearly" if (smin or smax) else None,
            employment_type=emp,
            posted_at=posted,
            legitimacy=cls.legitimacy,
            raw={"query": query},
        )
