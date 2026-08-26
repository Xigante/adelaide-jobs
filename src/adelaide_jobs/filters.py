"""Knockouts — o que sai da fila antes de qualquer pontuação.

Princípio de calibração, e ele é assimétrico de propósito:

    manter uma vaga ruim custa alguns tokens.
    descartar por engano uma vaga boa custa uma oportunidade de emprego.

Por isso todo knockout aqui é de precisão alta e recall baixo. Na dúvida,
deixa passar. Cada descarte grava o motivo, para você conseguir auditar
depois quais regras estão te custando vaga.
"""

from __future__ import annotations

from dataclasses import dataclass

from .extract import title_is_senior, RE_SPONSORSHIP, RE_TRADE
from .models import Dimensions, Job


@dataclass(slots=True)
class Knockout:
    code: str
    reason: str


def check(job: Job, dims: Dimensions, max_commute_km: float = 25.0) -> Knockout | None:
    """Primeiro knockout que se aplica, ou None."""

    # Full-time é incompatível com 48h/quinzena — são 76h.
    # MIXED (casual E full-time no mesmo anúncio) NÃO bloqueia.
    if dims.emp_type == "FULL_TIME":
        return Knockout("FULL_TIME_ONLY", "Só full-time — 76h/quinzena contra o teto de 48h")

    if dims.exp_req == "YEARS_REQUIRED" and (dims.exp_years or 0) >= 2:
        return Knockout(
            "MIN_EXPERIENCE_2Y_PLUS",
            f"Exige {dims.exp_years}+ anos de experiência como requisito duro",
        )

    if dims.au_licence == "ESSENTIAL":
        return Knockout("AU_LICENCE_ESSENTIAL", "Carta australiana e/ou carro próprio essenciais")

    if dims.work_rights == "FULL_RIGHTS_REQUIRED":
        return Knockout("NO_WORK_RIGHTS", "Exige direito de trabalho irrestrito, cidadania ou PR")

    if title_is_senior(job.title):
        return Knockout("SENIOR_ROLE", f"Título indica cargo sênior ou de chefia: {job.title!r}")

    if RE_SPONSORSHIP.search(job.searchable_text):
        return Knockout("SPONSORSHIP", "Vaga de sponsorship (482/186/494)")

    if RE_TRADE.search(job.searchable_text) and dims.exp_req in {"SOME_REQUIRED", "YEARS_REQUIRED"}:
        return Knockout("TRADE_REQUIRED", "Exige certificado de ofício ou licença regulada")

    if dims.distance_km is not None and dims.distance_km > max_commute_km:
        return Knockout(
            "OUT_OF_RANGE",
            f"{dims.distance_km:.0f} km do ILSC — acima do limite de {max_commute_km:.0f} km",
        )

    return None
