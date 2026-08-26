"""SEEK v5 — DESLIGADO POR PADRÃO. Leia antes de ligar.

═══════════════════════════════════════════════════════════════════════
 O QUE ISTO É
 A API interna do SEEK, sem autenticação, que alimenta o site deles.
 Aceita `where=All Adelaide SA` e filtro por classificação — ou seja,
 busca direcionada de kitchen hand em Adelaide, em JSON, sem browser.

 O endpoint v4 (`/api/chalice-search/v4/search`) MORREU: devolve 403.
 É o que quase todo repo antigo e todo tutorial de blog usa, e é a razão
 pela qual esse nicho inteiro no GitHub parece abandonado.

 O RISCO
 Usar isto viola os Termos de Uso do SEEK, que proíbem acesso automatizado.
 Não é crime — é inadimplemento contratual. Mas a consequência prática é
 bloqueio de IP ou da conta, e a sua conta do SEEK vai ser o canal
 principal de emprego da cidade onde você mora. A assimetria é ruim:
 o ganho é conveniência, a perda é acesso.

 A ALTERNATIVA SEM RISCO
 Alertas de e-mail nativos do SEEK numa caixa dedicada, parseados por
 IMAP. Mesma informação, entregue pela própria plataforma, nos seus dados.

 SE DECIDIR LIGAR
 - rate limit conservador (o padrão aqui é 8s entre requisições)
 - uma requisição por vez, nunca em paralelo
 - nunca do mesmo IP/sessão em que você navega logado
═══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..models import EmploymentType, Job, Legitimacy
from .base import USER_AGENT, BaseCollector, CollectorError, register

SEARCH_URL = "https://www.seek.com.au/api/jobsearch/v5/search"
JOB_URL = "https://www.seek.com.au/job/{job_id}"
MAX_PAGE_SIZE = 100  # acima disso a API devolve HTML em vez de JSON


@register
class SeekV5Collector(BaseCollector):
    name = "seek_v5"
    legitimacy = Legitimacy.AGAINST_TOS
    min_interval = 8.0

    def collect(self) -> list[Job]:
        if not self.config.get("enabled"):
            raise CollectorError(
                "seek_v5 está desligado em config/sources.yaml. "
                "Leia o cabeçalho de collectors/seek_v5.py antes de ligar."
            )

        where = self.config.get("where", "All Adelaide SA")
        classification = str(self.config.get("classification") or "")
        page_size = min(int(self.config.get("page_size", 20)), MAX_PAGE_SIZE)
        max_pages = int(self.config.get("max_pages", 3))

        jobs: list[Job] = []
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        with httpx.Client(timeout=30.0, headers=headers) as client:
            for page in range(1, max_pages + 1):
                self.throttle()
                params: dict[str, Any] = {
                    "siteKey": "AU-Main",
                    "sourcesystem": "houston",
                    "where": where,
                    "page": page,
                    "pageSize": page_size,
                    "locale": "en-AU",
                    "sortmode": "ListedDate",
                }
                if classification:
                    params["classification"] = classification

                try:
                    resp = client.get(SEARCH_URL, params=params)
                except httpx.HTTPError as exc:
                    self.note_error(f"rede na página {page}: {exc}")
                    break

                if resp.status_code == 403:
                    self.note_error(
                        "403 — Cloudflare bloqueou. Comum em IP de datacenter ou "
                        "fora da Austrália. Use os alertas de e-mail."
                    )
                    break
                if resp.status_code == 429:
                    self.note_error("429 — rate limit. Parando (não insista).")
                    break
                if resp.status_code != 200:
                    self.note_error(f"HTTP {resp.status_code} na página {page}")
                    break
                if "application/json" not in resp.headers.get("content-type", ""):
                    self.note_error("resposta não é JSON — pageSize alto ou endpoint mudou")
                    break

                data = resp.json().get("data") or []
                jobs.extend(self.parse(item) for item in data)
                if len(data) < page_size:
                    break
        return jobs

    @classmethod
    def parse(cls, item: dict[str, Any]) -> Job:
        job_id = str(item.get("id", ""))
        loc = item.get("location") or {}
        area = item.get("area") or {}

        advertiser = item.get("advertiser") or {}
        employer = (item.get("companyName") or advertiser.get("description") or "").strip() or None

        posted = None
        if raw_date := item.get("listingDate"):
            try:
                posted = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).date()
            except ValueError:
                pass

        work_type = ""
        wts = item.get("workTypes") or []
        if isinstance(wts, list) and wts:
            work_type = str(wts[0]).lower()
        emp = {
            "casual": EmploymentType.CASUAL,
            "casual/vacation": EmploymentType.CASUAL,
            "part time": EmploymentType.PART_TIME,
            "full time": EmploymentType.FULL_TIME,
            "contract/temp": EmploymentType.CONTRACT,
        }.get(work_type, EmploymentType.UNKNOWN)

        # `teaser` é o resumo curto do card. A descrição completa exige o
        # GraphQL — deixado de fora de propósito: mais requisições, mais
        # exposição, e o teaser já basta para triagem.
        return Job(
            source=cls.name,
            source_id=job_id,
            title=(item.get("title") or "").strip(),
            url=JOB_URL.format(job_id=job_id),
            employer=employer,
            description=item.get("teaser") or "",
            suburb=(loc.get("label") if isinstance(loc, dict) else None) or str(loc or "") or None,
            state=(area.get("label") if isinstance(area, dict) else None),
            employment_type=emp,
            posted_at=posted,
            legitimacy=cls.legitimacy,
            raw={"salaryLabel": item.get("salaryLabel")},
        )
