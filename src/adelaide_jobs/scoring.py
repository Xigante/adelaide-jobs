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
from dataclasses import dataclass, field

from .models import Dimensions


# Nome interno da dimensão -> como ela se chama na tela, em português.
ROTULOS = {
    "experience_barrier":    "experiência exigida",
    "english_load":          "quanto inglês precisa",
    "visa_hours_fit":        "cabe no visto (48h/quinzena)",
    "commute":               "distância da escola",
    "shift_fit":             "horário do turno",
    "certification_barrier": "certificados exigidos",
    "employer_pattern":      "tipo de empregador",
    "career_bridge":         "ponte para dados/admin",
    "ghost_flag":            "anúncio repostado demais",
    "multi_source_bonus":    "aparece em várias fontes",
}


@dataclass(slots=True)
class ScoreBreakdown:
    """Nota final mais a conta aberta — sem isso não dá para depurar."""

    total: int
    parts: dict[str, float]
    weighted: dict[str, float]
    penalties: dict[str, float]
    version: str
    #: peso máximo de cada dimensão. Guardado, e não deduzido de
    #: weighted/parts — quando a nota é 0 essa divisão não existe.
    weights: dict[str, int] = field(default_factory=dict)

    def explain(self) -> str:
        """A conta aberta, em português.

        Cada linha é: o que foi avaliado, a nota de 0 a 1 que a dimensão
        tirou, quanto ela vale no máximo, e quantos pontos sobraram.
        Sem isto o score seria opinião.
        """
        L = [
            f"score {self.total} de 100      (versão dos pesos: {self.version})",
            "",
            f"  {'o que foi avaliado':<30}{'nota':>6}{'vale até':>10}{'pontos':>9}",
            "  " + "\u2500" * 55,
        ]
        for k, v in sorted(self.weighted.items(), key=lambda kv: -kv[1]):
            peso = self.weights.get(k, 0)
            L.append(f"  {ROTULOS.get(k, k):<30}{self.parts[k]:>6.2f}{peso:>10}{v:>9.1f}")
        for k, v in self.penalties.items():
            L.append(f"  {ROTULOS.get(k, k):<30}{'':>6}{'':>10}{-v:>9.1f}")
        L.append("  " + "\u2500" * 55)
        L.append(f"  {'TOTAL':<30}{'':>6}{'':>10}{self.total:>9}")
        return "\n".join(L)


# ── uma função por dimensão, cada uma devolvendo 0.0–1.0 ────────────

def _experience_barrier(d: Dimensions) -> float:
    return {
        "NONE_REQUIRED": 1.0,     # "full training provided" é ouro
        "NOT_STATED": 0.7,        # silêncio costuma significar entry-level
        "SOME_PREFERRED": 0.55,
        "SOME_REQUIRED": 0.2,
        "YEARS_REQUIRED": 0.0,
    }.get(d.exp_req, 0.5)


def _english_load(d: Dimensions, nivel: str = "A2") -> float:
    """Quanto o inglês da vaga pesa contra o inglês que ele tem hoje.

    Back-of-house sempre vale 1.0 — lavar louça é lavar louça em qualquer
    idioma. O que muda com o nível é o custo de atender cliente.
    """
    _, medio, alto = NIVEIS_INGLES.get(nivel.upper(), NIVEIS_INGLES["A2"])
    return {
        "BOH_MINIMAL": 1.0,
        "LOW": 0.85,
        "UNKNOWN": 0.5,
        "MEDIUM": medio,
        "HIGH": alto,
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


# Faixas de nota. score -> (letra, o que fazer)
FAIXAS: list[tuple[int, str, str]] = [
    (89, "A+", "candidate-se hoje"),
    (78, "A",  "muito boa"),
    (70, "A-", "boa"),
    (62, "B+", "vale olhar"),
    (55, "B",  "talvez"),
    (40, "C",  "só se estiver seco"),
    (0,  "D",  "provavelmente não"),
]


def nota(score: int | None, bloqueada: bool = False) -> tuple[str, str]:
    """Devolve (letra, o que fazer). Bloqueada é 'X'."""
    if bloqueada:
        return "X", "descartada"
    if score is None:
        return "?", "ainda não avaliada"
    for corte, letra, acao in FAIXAS:
        if score >= corte:
            return letra, acao
    return "D", "provavelmente não"


# ── Nível de inglês ─────────────────────────────────────────────────
# O inglês dele é a variável que MAIS muda ao longo do curso, e era a
# única que o sistema tratava como fixa. Conforme sobe, duas coisas
# acontecem: vaga com atendimento deixa de ser penalizada, e o peso da
# dimensão de inglês cai — porque ela para de ser o gargalo.
#
# tabela: nível -> (multiplicador do peso, nota para MEDIUM, nota para HIGH)
NIVEIS_INGLES: dict[str, tuple[float, float, float]] = {
    "A1": (1.15, 0.15, 0.00),
    "A2": (1.00, 0.30, 0.00),   # chegada
    "B1": (0.75, 0.60, 0.20),
    "B2": (0.50, 0.85, 0.50),
    "C1": (0.30, 1.00, 0.80),
    "C2": (0.20, 1.00, 0.95),
}


def pesos_para_ingles(weights: dict[str, int], nivel: str) -> dict[str, int]:
    """Reduz o peso do inglês conforme ele melhora, e redistribui o resto.

    Mantém a soma em 100 — senão as notas de meses diferentes deixariam
    de ser comparáveis, e o histórico de calibração perderia o sentido.
    """
    mult = NIVEIS_INGLES.get(nivel.upper(), NIVEIS_INGLES["A2"])[0]
    if mult == 1.0:
        return dict(weights)

    w = dict(weights)
    original = w.get("english_load", 0)
    novo = original * mult
    sobra = original - novo
    outros = {k: v for k, v in w.items() if k != "english_load" and v > 0}
    total_outros = sum(outros.values()) or 1

    ajustado = {"english_load": novo}
    for k, v in outros.items():
        ajustado[k] = v + sobra * (v / total_outros)
    # Arredonda mantendo a soma exata em 100.
    saida = {k: int(round(v)) for k, v in ajustado.items()}
    diff = 100 - sum(saida.values())
    if diff:
        maior = max(saida, key=lambda k: saida[k])
        saida[maior] += diff
    return saida


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
    english_level: str = "A2",
    ghost: bool = False,
    ghost_penalty: float = 15.0,
    multi_source: int = 1,
    version: str = "w1",
) -> ScoreBreakdown:
    w = pesos_para_ingles({**DEFAULT_WEIGHTS, **(weights or {})}, english_level)

    parts = {
        "experience_barrier": _experience_barrier(dims),
        "english_load": _english_load(dims, english_level),
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
        weights=w,
        total=_round_half_up(total),
        parts=parts,
        weighted=weighted,
        penalties=penalties,
        version=version,
    )
