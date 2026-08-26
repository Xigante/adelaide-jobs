"""Modelo normalizado de vaga.

Todo coletor devolve `Job`. Nada além de `Job` entra no banco. Isso é o
contrato que impede o pipeline de virar espaguete quando a sexta fonte
chegar com um formato diferente das cinco anteriores.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from typing import Any


class Legitimacy(str, Enum):
    """Como a fonte foi obtida. Fica gravado em cada vaga."""

    OFFICIAL_API = "official_api"       # API documentada, com chave
    PUBLIC_ENDPOINT = "public_endpoint"  # endpoint público sem auth
    OWN_DATA = "own_data"                # seus próprios e-mails
    OPEN_ROBOTS = "open_robots"          # site cujo robots.txt permite
    AGAINST_TOS = "against_tos"          # contra os termos de uso


class EmploymentType(str, Enum):
    CASUAL = "casual"
    PART_TIME = "part_time"
    FULL_TIME = "full_time"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class Job:
    """Uma vaga, como qualquer coletor a devolve."""

    source: str
    source_id: str
    title: str
    url: str
    employer: str | None = None
    description: str = ""
    suburb: str | None = None
    state: str | None = None
    postcode: str | None = None
    lat: float | None = None
    lon: float | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None   # hourly | daily | weekly | yearly
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    posted_at: date | None = None
    legitimacy: Legitimacy = Legitimacy.PUBLIC_ENDPOINT
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ── derivados ────────────────────────────────────────────────────

    @property
    def location_text(self) -> str:
        parts = [p for p in (self.suburb, self.state, self.postcode) if p]
        return ", ".join(parts)

    @property
    def searchable_text(self) -> str:
        """Título + descrição, para os filtros de regex."""
        return f"{self.title}\n{self.description}"

    def content_hash(self) -> str:
        """Muda quando o anúncio é editado. Base do cache L0."""
        blob = f"{self.title}|{self.employer}|{self.description}".lower()
        return hashlib.blake2b(blob.encode("utf-8"), digest_size=12).hexdigest()

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("raw", None)
        d["employment_type"] = self.employment_type.value
        d["legitimacy"] = self.legitimacy.value
        d["posted_at"] = self.posted_at.isoformat() if self.posted_at else None
        return d


@dataclass(slots=True)
class Dimensions:
    """O que um extrator produz a partir do texto da vaga.

    Hoje quem preenche isso é `extract.RuleExtractor` (regex). Depois vai
    ser o Gemini. O scorer não muda quando a troca acontecer — é para isso
    que esta camada existe.
    """

    # experiência exigida
    exp_req: str = "NOT_STATED"      # NONE_REQUIRED|NOT_STATED|SOME_PREFERRED|SOME_REQUIRED|YEARS_REQUIRED
    exp_years: int | None = None
    # inglês
    eng_contact: str = "UNKNOWN"     # BOH_MINIMAL|LOW|MEDIUM|HIGH|UNKNOWN
    # vínculo e horas
    emp_type: str = "NOT_STATED"     # CASUAL|PART_TIME|FULL_TIME|MIXED|NOT_STATED
    hours_pattern: str = "NOT_STATED"  # FLEXIBLE_LOW|MODERATE|NEAR_FULL_TIME|NOT_STATED
    # turno
    shift_window: str = "NOT_STATED"  # EARLY_MORNING|DAYTIME|EVENING|OVERNIGHT|WEEKEND|ROTATING|NOT_STATED
    # requisitos de três estados: NOT_MENTIONED | DESIRABLE | ESSENTIAL
    au_licence: str = "NOT_MENTIONED"
    rsa: str = "NOT_MENTIONED"
    white_card: str = "NOT_MENTIONED"
    food_handling: str = "NOT_MENTIONED"
    # direito de trabalho
    work_rights: str = "NOT_STATED"  # STUDENT_OK|FULL_RIGHTS_REQUIRED|NOT_STATED
    # empregador
    employer_kind: str = "UNKNOWN"   # LARGE_CHAIN|AGENCY|INDEPENDENT|INSTITUTION|UNKNOWN
    # ponte de carreira
    career_bridge: bool = False
    # distância calculada (km); None = desconhecida
    distance_km: float | None = None
    # de onde vieram estas dimensões
    extractor: str = "rules"

    def to_row(self) -> dict[str, Any]:
        return asdict(self)
