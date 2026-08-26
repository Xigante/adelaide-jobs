"""Score 0–100, calculado em Python.

A decisão de arquitetura mais importante do projeto: o LLM (quando entrar)
NÃO emite o número. Ele classifica dimensões; a aritmética mora aqui.

Motivo prático: quando você recalibrar os pesos com dados reais das suas
candidaturas, isso vira um `git commit` — e reprocessar 2.000 vagas
históricas vira um loop de 200 ms, em vez de 2.000 chamadas de API.

Cada dimensão devolve 0.0–1.0. O peso vem do profile.yaml.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import Dimensions


@dataclass(slots=True)
class ScoreBreakdown:
    """Nota final mais a conta aberta — sem isso não dá para depurar."""

    total: int
    parts: dict[str, float]
    weighted: dict[str, float]
    penalties: dict[str, float]
    version: str

    def explain(self) -> str:
        lines = [f"score {self.total}  (pesos {self.version})"]
        for k, v in sorted(self.weighted.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:<24} {self.parts[k]:.2f} × peso = {v:5.1f}")
        for k, v in self.penalties.items():
            lines.append(f"  {k:<24} {'':>13} {-v:5.1f}")
        return "\n".join(lines)


# ── uma função por dimensão, cada uma devolvendo 0.0–1.0 ────────────

def _experience_barrier(d: Dimensions) -> float:
    return {
        "NONE_REQUIRED": 1.0,     # "full training provided" é ouro
        "NOT_STATED": 0.7,        # silêncio costuma significar entry-level
        "SOME_PREFERRED": 0.55,
        "SOME_REQUIRED": 0.2,
        "YEARS_REQUIRED": 0.0,
    }.get(d.exp_req, 0.5)


def _english_load(d: Dimensions) -> float:
    return {
        "BOH_MINIMAL": 1.0,   # kitchen hand com A2 funciona
        "LOW": 0.8,
        "UNKNOWN": 0.5,
        "MEDIUM": 0.3,
        "HIGH": 0.0,          # barista com A2 não funciona
    }.get(d.eng_contact, 0.5)


def _visa_hours_fit(d: Dimensions) -> float:
    emp = {
        "CASUAL": 1.0, "PART_TIME": 0.85, "MIXED": 0.6,
        "NOT_STATED": 0.5, "FULL_TIME": 0.0, "CONTRACT": 0.4,
    }.get(d.emp_type, 0.5)
    hours = {
        "FLEXIBLE_LOW": 1.0,      # 8–25h/semana é o ponto ideal
        "MODERATE": 0.6,
        "NOT_STATED": 0.6,
        "NEAR_FULL_TIME": 0.1,    # "casual, up to 38 hours" é armadilha
    }.get(d.hours_pattern, 0.6)
    return 0.6 * emp + 0.4 * hours


def _commute(d: Dimensions) -> float:
    if d.distance_km is None:
        return 0.5           # desconhecido não é ruim, é desconhecido
    km = d.distance_km
    if km <= 2:
        return 1.0           # dá para ir a pé da escola
    if km <= 5:
        return 0.9
    if km <= 10:
        return 0.7
    if km <= 15:
        return 0.45
    if km <= 20:
        return 0.25
    return 0.1


def _shift_fit(d: Dimensions, class_pattern: str = "UNKNOWN") -> float:
    """Turno noturno paga penalty e não conflita com aula de manhã.

    Mas cobra o custo do transporte de volta: um night fill que termina às
    2h em Elizabeth paga bem e é inalcançável sem carro. Desconto aplicado
    quando o turno é noturno E a vaga é longe.
    """
    base = {
        "OVERNIGHT": 1.0, "EVENING": 0.9, "WEEKEND": 0.85,
        "EARLY_MORNING": 0.6, "ROTATING": 0.6, "NOT_STATED": 0.5,
        "DAYTIME": 0.3,
    }.get(d.shift_window, 0.5)

    # Turma da tarde derruba turno da noite; turma da manhã derruba o dia.
    if class_pattern == "PM" and d.shift_window in {"EVENING", "OVERNIGHT"}:
        base *= 0.4
    elif class_pattern == "AM" and d.shift_window in {"DAYTIME", "EARLY_MORNING"}:
        base *= 0.4

    # Custo do transporte noturno de volta ao CBD.
    if d.shift_window == "OVERNIGHT" and d.distance_km is not None and d.distance_km > 8:
        base *= 0.6
    return base


def _certification_barrier(d: Dimensions) -> float:
    """Penaliza pelo atrito de obter, não pela existência do requisito."""
    score = 1.0
    if d.rsa == "ESSENTIAL":
        score -= 0.45          # curso regulado pela CBS, dias de espera
    elif d.rsa == "DESIRABLE":
        score -= 0.1
    if d.white_card == "ESSENTIAL":
        score -= 0.3           # um dia de curso num RTO
    if d.food_handling == "ESSENTIAL":
        score -= 0.15          # online, barato, algumas horas
    return max(0.0, score)


def _employer_pattern(d: Dimensions) -> float:
    return {
        "LARGE_CHAIN": 1.0,    # contrata em volume, processo padronizado,
                               # acostumada com visto de estudante
        "INSTITUTION": 0.7,
        "AGENCY": 0.5,
        "INDEPENDENT": 0.6,
        "UNKNOWN": 0.4,
    }.get(d.employer_kind, 0.5)


def _career_bridge(d: Dimensions) -> float:
    return 1.0 if d.career_bridge else 0.0


def _round_half_up(value: float) -> int:
    """Arredondamento previsível, limitado a 0–100.

    `round()` do Python usa banker's rounding: round(80.5) == 80 mas
    round(65.5) == 66. Num score isso faz duas vagas equivalentes
    aparecerem com notas diferentes por um ponto, sem motivo visível.
    """
    return max(0, min(100, math.floor(value + 0.5)))


DEFAULT_WEIGHTS: dict[str, int] = {
    "experience_barrier": 25,
    "english_load": 20,
    "visa_hours_fit": 15,
    "commute": 12,
    "shift_fit": 10,
    "certification_barrier": 8,
    "employer_pattern": 6,
    "career_bridge": 4,
}


def score(
    dims: Dimensions,
    weights: dict[str, int] | None = None,
    *,
    class_pattern: str = "UNKNOWN",
    ghost: bool = False,
    ghost_penalty: float = 15.0,
    multi_source: int = 1,
    version: str = "w1",
) -> ScoreBreakdown:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}

    parts = {
        "experience_barrier": _experience_barrier(dims),
        "english_load": _english_load(dims),
        "visa_hours_fit": _visa_hours_fit(dims),
        "commute": _commute(dims),
        "shift_fit": _shift_fit(dims, class_pattern),
        "certification_barrier": _certification_barrier(dims),
        "employer_pattern": _employer_pattern(dims),
        "career_bridge": _career_bridge(dims),
    }
    weighted = {k: parts[k] * w.get(k, 0) for k in parts}
    total = sum(weighted.values())

    penalties: dict[str, float] = {}
    if ghost:
        # Anúncio repostado sem mudar: banco de currículos disfarçado.
        penalties["ghost_flag"] = ghost_penalty
        total -= ghost_penalty
    if multi_source >= 3:
        # Empregador gastando em divulgação em 3+ fontes provavelmente
        # está contratando de verdade. Sinal positivo fraco.
        penalties["multi_source_bonus"] = -3.0
        total += 3.0

    return ScoreBreakdown(
        total=_round_half_up(total),
        parts=parts,
        weighted=weighted,
        penalties=penalties,
        version=version,
    )
