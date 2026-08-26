"""Extração de dimensões a partir do texto do anúncio.

Arquitetura deliberada: o extrator NÃO calcula score. Ele lê texto ambíguo
em inglês australiano e devolve categorias. O score sai daí, em Python.

Hoje quem preenche é `RuleExtractor` (regex). Quando o Gemini entrar, ele
implementa o mesmo protocolo e devolve o mesmo `Dimensions` — e o scorer
não muda uma linha. É por isso que esta camada existe separada.
"""

from __future__ import annotations

import re
from typing import Protocol

from .geo import distance_from_school, guess_coords
from .models import Dimensions, Job

# ── vocabulário de exigência ────────────────────────────────────────
# O anúncio australiano marca requisito duro com "essential", "must have",
# "required"; e requisito mole com "desirable", "preferred", "advantageous".
# Confundir os dois é o erro que mais custa vaga boa.
ESSENTIAL_WORDS = re.compile(
    r"\b(essential|mandatory|must have|must hold|must possess|required|require[sd]?|"
    r"you will need|you must|non[- ]negotiable)\b", re.I,
)
DESIRABLE_WORDS = re.compile(
    r"\b(desirable|preferred|preferable|advantageous|an advantage|a bonus|"
    r"would be great|nice to have|highly regarded|well regarded|ideally|"
    r"not essential|beneficial)\b", re.I,
)

WINDOW = 90  # caracteres em volta da menção


def _requirement_level(text: str, pattern: re.Pattern[str]) -> str:
    """NOT_MENTIONED | DESIRABLE | ESSENTIAL.

    Na dúvida devolve DESIRABLE — nunca ESSENTIAL. Falso negativo em
    knockout custa quase nada; falso positivo custa uma oportunidade.
    """
    m = pattern.search(text)
    if not m:
        return "NOT_MENTIONED"
    lo = max(0, m.start() - WINDOW)
    hi = min(len(text), m.end() + WINDOW)
    ctx = text[lo:hi]
    if DESIRABLE_WORDS.search(ctx):
        return "DESIRABLE"
    if ESSENTIAL_WORDS.search(ctx):
        return "ESSENTIAL"
    return "DESIRABLE"


# ── padrões por dimensão ────────────────────────────────────────────
RE_FULL_TIME = re.compile(r"\bfull[\s-]?time\b", re.I)
RE_PART_TIME = re.compile(r"\bpart[\s-]?time\b", re.I)
RE_CASUAL = re.compile(r"\bcasual\b", re.I)
RE_38_HOURS = re.compile(r"\b3[68]\s*(hours|hrs)\s*(per|a|/)\s*(week|wk)\b", re.I)
RE_MON_FRI_9_5 = re.compile(
    r"\bmonday\s*(?:to|-|–|through)\s*friday\b.{0,40}?\b(?:8|8:30|9)\s*(?:am)?\s*"
    r"(?:to|-|–)\s*(?:5|5:30|6)\s*(?:pm)?", re.I,
)
RE_YEARS = re.compile(
    r"\b(?:minimum(?:\s+of)?|min\.?|at least)?\s*(\d+)\s*\+?\s*(?:\+\s*)?years?\b"
    r"(?:\s+(?:of\s+)?(?:relevant\s+|previous\s+|proven\s+)?experience)?", re.I,
)
RE_NO_EXPERIENCE = re.compile(
    r"\b(no (?:prior |previous |formal )?experience (?:is )?(?:necessary|needed|required)|"
    r"full training (?:will be )?(?:provided|given)|training provided|we(?:'| wi)ll teach you|"
    r"entry[\s-]level|all backgrounds welcome|no experience\b)", re.I,
)
RE_EXPERIENCE_MENTION = re.compile(r"\bexperience\b", re.I)

RE_AU_LICENCE = re.compile(
    r"\b(?:current|valid|full|australian|aus)?\s*(?:driver'?s?|drivers)\s*licen[cs]e\b"
    r"|\bown\s+(?:reliable\s+)?(?:car|vehicle|transport)\b", re.I,
)
RE_RSA = re.compile(r"\b(rsa|responsible service of alcohol)\b", re.I)
RE_WHITE_CARD = re.compile(r"\b(white card|construction induction)\b", re.I)
RE_FOOD_HANDLING = re.compile(r"\b(food (?:safety|handling|handler)|food hygiene)\b", re.I)

RE_FULL_RIGHTS = re.compile(
    r"\b(full|unrestricted)\s+(?:australian\s+)?(?:working\s+)?rights\b"
    r"|\b(?:australian\s+)?citizens?\s+(?:or|and|/)\s+(?:permanent\s+residents?|pr)\b"
    r"|\bmust\s+(?:be\s+an?\s+)?(?:hold\s+)?(?:australian\s+)?(?:citizenship|permanent residency|"
    r"citizen|permanent resident)\b"
    r"|\b(?:baseline|nv1|nv2|negative vetting)\b", re.I,
)
RE_STUDENT_OK = re.compile(
    r"\b(student visa(?:s)? (?:welcome|accepted|ok)|working holiday|"
    r"visa holders welcome|all visa types|students welcome)\b", re.I,
)
RE_SPONSORSHIP = re.compile(r"\b(?:subclass\s*)?\b(482|186|494)\b|\bvisa sponsorship\b", re.I)
RE_TRADE = re.compile(
    r"\bcert(?:ificate)?\s*(?:iii|iv|3|4)\b|\b(?:forklift|lf|hr|mr|hc)\s+licen[cs]e\b"
    r"|\btrade[\s-]qualified\b|\bqualified\s+(?:chef|cook|electrician|plumber|carpenter)\b", re.I,
)
# "Senior" só conta no TÍTULO. No corpo casa com "Senior Living facility",
# "seniors discount", "senior school" — e derruba vaga boa de aged care.
RE_SENIOR_TITLE = re.compile(
    r"\b(senior|lead|principal|head of|chief|manager|supervisor|team leader|coordinator)\b", re.I,
)

RE_OVERNIGHT = re.compile(
    r"\b(overnight|night shift|nights|graveyard|10pm|11pm|midnight|"
    r"2am|3am|4am|5am|night fill|nightfill)\b", re.I,
)
RE_EVENING = re.compile(r"\b(evening|afternoon|arvo|dinner service|after school|5pm|6pm|7pm)\b", re.I)
RE_EARLY = re.compile(r"\b(early (?:morning|start)|4am|5am|6am|sunrise|bakery start)\b", re.I)
RE_WEEKEND = re.compile(r"\b(weekend|saturday|sunday|sat & sun|sat/sun)\b", re.I)

RE_HOURS_LOW = re.compile(
    r"\b(?:up to\s*)?(\d{1,2})\s*(?:-|to|–)\s*(\d{1,2})\s*(?:hours|hrs)\s*(?:per|a|/)\s*week", re.I,
)
RE_FEW_SHIFTS = re.compile(r"\b(a few shifts|\d\s*shifts? per week|flexible hours|as needed)\b", re.I)

CUSTOMER_FACING = re.compile(
    r"\b(customer service|serving customers|front of house|reception|receptionist|"
    r"answer(?:ing)? (?:the )?phone|phone calls|barista|upsell|point of sale|"
    r"take orders|greet(?:ing)? customers|customer facing|complaints)\b", re.I,
)
EXCELLENT_ENGLISH = re.compile(
    r"\b(excellent (?:written and )?(?:verbal |oral )?communication|fluent english|"
    r"strong communication skills|native english|excellent english)\b", re.I,
)

LARGE_CHAINS = (
    "coles", "woolworths", "woolies", "bunnings", "kmart", "target", "aldi", "iga",
    "foodland", "drakes", "big w", "mcdonald", "hungry jack", "kfc", "subway",
    "domino", "guzman", "grill'd", "nando", "sushi hub", "bakers delight",
    "chemist warehouse", "officeworks", "spotlight", "jb hi-fi", "dan murphy",
    "bws", "liquorland", "7-eleven", "compass group", "sodexo", "spotless",
)
AGENCY_WORDS = re.compile(
    r"\b(recruit(?:ment|ing)?|labour hire|staffing|workforce|personnel|"
    r"our client|talent|hays|randstad|adecco|programmed|chandler macleod)\b", re.I,
)
INSTITUTION_WORDS = re.compile(
    r"\b(university|council|health|hospital|school|tafe|government|department of|"
    r"aged care|community services)\b", re.I,
)

CAREER_BRIDGE = re.compile(
    r"\b(data|analyst|power bi|powerbi|sql|excel|reporting|dashboard|admin|"
    r"administration|office|clerical|business intelligence|automation)\b", re.I,
)


class Extractor(Protocol):
    """Contrato. O Gemini vai implementar isto e nada mais muda."""

    name: str

    def extract(self, job: Job) -> Dimensions: ...


class RuleExtractor:
    """Extrator determinístico. Sem LLM, sem chave, sem custo."""

    name = "rules"

    def __init__(self, boh_keywords: list[str] | None = None) -> None:
        kws = boh_keywords or []
        self._boh = re.compile(
            "|".join(re.escape(k) for k in kws), re.I
        ) if kws else None

    # ── dimensões individuais ────────────────────────────────────────

    def _employment(self, text: str) -> str:
        ft = bool(RE_FULL_TIME.search(text)) or bool(RE_38_HOURS.search(text)) \
            or bool(RE_MON_FRI_9_5.search(text))
        casual = bool(RE_CASUAL.search(text))
        pt = bool(RE_PART_TIME.search(text))
        if ft and (casual or pt):
            # "Casual, part-time and full-time positions available" — comum
            # em entry-level. Bloquear isto destrói o pipeline.
            return "MIXED"
        if ft:
            return "FULL_TIME"
        if casual:
            return "CASUAL"
        if pt:
            return "PART_TIME"
        return "NOT_STATED"

    def _experience(self, text: str) -> tuple[str, int | None]:
        if RE_NO_EXPERIENCE.search(text):
            return "NONE_REQUIRED", None
        m = RE_YEARS.search(text)
        if m:
            years = int(m.group(1))
            if 1 <= years <= 20:
                lo = max(0, m.start() - WINDOW)
                hi = min(len(text), m.end() + WINDOW)
                ctx = text[lo:hi]
                if DESIRABLE_WORDS.search(ctx):
                    return "SOME_PREFERRED", years
                return "YEARS_REQUIRED", years
        if RE_EXPERIENCE_MENTION.search(text):
            level = _requirement_level(text, RE_EXPERIENCE_MENTION)
            if level == "ESSENTIAL":
                return "SOME_REQUIRED", None
            if level == "DESIRABLE":
                return "SOME_PREFERRED", None
        return "NOT_STATED", None

    def _english(self, title: str, text: str) -> str:
        if self._boh and self._boh.search(title):
            return "BOH_MINIMAL"
        if EXCELLENT_ENGLISH.search(text):
            return "HIGH"
        if CUSTOMER_FACING.search(text):
            return "MEDIUM"
        if self._boh and self._boh.search(text):
            return "LOW"
        return "UNKNOWN"

    def _shift(self, text: str) -> str:
        if RE_OVERNIGHT.search(text):
            return "OVERNIGHT"
        if RE_EARLY.search(text):
            return "EARLY_MORNING"
        if RE_EVENING.search(text):
            return "EVENING"
        if RE_WEEKEND.search(text):
            return "WEEKEND"
        return "NOT_STATED"

    def _hours(self, text: str) -> str:
        m = RE_HOURS_LOW.search(text)
        if m:
            hi = int(m.group(2))
            if hi <= 25:
                return "FLEXIBLE_LOW"
            if hi <= 34:
                return "MODERATE"
            return "NEAR_FULL_TIME"
        if RE_38_HOURS.search(text):
            return "NEAR_FULL_TIME"
        if RE_FEW_SHIFTS.search(text):
            return "FLEXIBLE_LOW"
        return "NOT_STATED"

    def _work_rights(self, text: str) -> str:
        if RE_STUDENT_OK.search(text):
            return "STUDENT_OK"
        if RE_FULL_RIGHTS.search(text):
            return "FULL_RIGHTS_REQUIRED"
        return "NOT_STATED"

    def _employer_kind(self, employer: str | None, text: str) -> str:
        e = (employer or "").lower()
        if any(chain in e for chain in LARGE_CHAINS):
            return "LARGE_CHAIN"
        if AGENCY_WORDS.search(e) or AGENCY_WORDS.search(text[:600]):
            return "AGENCY"
        if INSTITUTION_WORDS.search(e):
            return "INSTITUTION"
        if e:
            return "INDEPENDENT"
        return "UNKNOWN"

    # ── entrada principal ────────────────────────────────────────────

    def extract(self, job: Job) -> Dimensions:
        text = job.searchable_text
        exp_req, exp_years = self._experience(text)

        lat, lon = job.lat, job.lon
        if lat is None or lon is None:
            guess = guess_coords(job.suburb)
            if guess:
                lat, lon = guess
        distance = distance_from_school(lat, lon)

        return Dimensions(
            exp_req=exp_req,
            exp_years=exp_years,
            eng_contact=self._english(job.title, text),
            emp_type=self._employment(text),
            hours_pattern=self._hours(text),
            shift_window=self._shift(text),
            au_licence=_requirement_level(text, RE_AU_LICENCE),
            rsa=_requirement_level(text, RE_RSA),
            white_card=_requirement_level(text, RE_WHITE_CARD),
            food_handling=_requirement_level(text, RE_FOOD_HANDLING),
            work_rights=self._work_rights(text),
            employer_kind=self._employer_kind(job.employer, text),
            career_bridge=bool(CAREER_BRIDGE.search(job.title)),
            distance_km=distance,
            extractor=self.name,
        )


def title_is_senior(title: str) -> bool:
    """Só o título conta — ver o comentário em RE_SENIOR_TITLE."""
    return bool(RE_SENIOR_TITLE.search(title))
