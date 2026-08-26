"""Deduplicação em cascata.

A mesma vaga aparece na Adzuna, no alerta do SEEK, no Gumtree e na página
do empregador, com títulos diferentes. Sem isto você se candidata duas
vezes na mesma vaga — que é ativamente prejudicial.

    estágio 1  chave canônica exata   ~70% das duplicatas, custo zero
    estágio 2  blocking + fuzzy       mais ~20%
    estágio 3  embeddings             só no resíduo ambíguo (v2)

Estágio 3 fica de fora de propósito: embedding sozinho não distingue
"mesma vaga" de "mesmo tipo de vaga". Dois kitchen hands em restaurantes
DIFERENTES do CBD são semanticamente quase idênticos, e fundi-los é pior
que deixar a duplicata passar.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from rapidfuzz import fuzz

# Sufixos societários e ruído de marketing: não identificam a vaga.
LEGAL_RE = re.compile(
    r"\b(pty\.?\s*ltd\.?|pty|ltd\.?|p/l|inc\.?|limited|group|holdings|"
    r"australia|australian|au|the)\b", re.I,
)
NOISE_RE = re.compile(
    r"\b(urgent|urgently|immediate start|immediately|hiring now|apply now|now hiring|"
    r"casual|part[\s-]?time|full[\s-]?time|permanent|temporary|temp|"
    r"wanted|required|needed|new|multiple positions|multiple roles|no experience|"
    r"start today|weekend|weekday|\d{4})\b", re.I,
)

# Sinônimos de papel — em duas camadas, e a ordem importa.
#
# "Night Fill Team Member" contém "team member". Se a busca fosse só pelo
# match mais longo, essa vaga viraria `team_member` e sairia do radar de
# back-of-house. Papéis ESPECÍFICOS ganham sempre de papéis genéricos;
# dentro de cada camada, a frase mais longa ganha.
SPECIFIC_ROLES: dict[str, str] = {
    "kitchen hand": "kitchen_hand",
    "kitchenhand": "kitchen_hand",
    "kitchen attendant": "kitchen_hand",
    "kitchen assistant": "kitchen_hand",
    "kitchen steward": "kitchen_hand",
    "dishwasher": "kitchen_hand",
    "dish hand": "kitchen_hand",
    "dishie": "kitchen_hand",
    "night fill": "night_fill",
    "nightfill": "night_fill",
    "night filler": "night_fill",
    "night filling": "night_fill",
    "grocery assistant": "night_fill",
    "shelf stacker": "night_fill",
    "cleaner": "cleaning",
    "cleaning": "cleaning",
    "housekeeper": "cleaning",
    "housekeeping": "cleaning",
    "room attendant": "cleaning",
    "janitor": "cleaning",
    "storeperson": "warehouse",
    "store person": "warehouse",
    "picker packer": "warehouse",
    "pick packer": "warehouse",
    "picker": "warehouse",
    "packer": "warehouse",
    "warehouse": "warehouse",
    "forklift": "warehouse",
    "process worker": "warehouse",
    "production worker": "warehouse",
    "barista": "barista",
    "food and beverage attendant": "food_beverage",
    "f b attendant": "food_beverage",
    "waiter": "food_beverage",
    "waitress": "food_beverage",
    "wait staff": "food_beverage",
    "waiting staff": "food_beverage",
    "chef": "chef",
    "cook": "cook",
}

GENERIC_ROLES: dict[str, str] = {
    "team member": "team_member",
    "crew member": "team_member",
    "team hand": "team_member",
    "retail assistant": "retail_assistant",
    "sales assistant": "retail_assistant",
    "customer service assistant": "retail_assistant",
    "customer service": "retail_assistant",
    "store assistant": "retail_assistant",
    "attendant": "attendant",
    "assistant": "assistant",
}

ROLE_SYNONYMS: dict[str, str] = {**SPECIFIC_ROLES, **GENERIC_ROLES}

_SPECIFIC_SORTED = sorted(SPECIFIC_ROLES.items(), key=lambda kv: -len(kv[0]))
_GENERIC_SORTED = sorted(GENERIC_ROLES.items(), key=lambda kv: -len(kv[0]))


def norm(s: str | None) -> str:
    """Minúsculas, sem acento, sem pontuação, espaço único."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def canon_employer(name: str | None) -> str:
    """Nome do empregador sem sufixo societário nem espaço."""
    return re.sub(r"\s+", "", LEGAL_RE.sub(" ", norm(name)))


def canon_role(title: str | None) -> str:
    """Título reduzido a um papel canônico.

    Duas passadas: papéis específicos primeiro, genéricos só se nada
    específico casar. Sem isso, "Night Fill Team Member" viraria
    `team_member` — e um turno noturno de supermercado é exatamente o
    que não pode escapar da fila.
    """
    t = re.sub(r"\s+", " ", NOISE_RE.sub(" ", norm(title))).strip()
    for table in (_SPECIFIC_SORTED, _GENERIC_SORTED):
        for phrase, canon in table:
            if phrase in t:
                return canon
    return re.sub(r"\s+", "_", t)[:40] or "unknown"


def canon_locality(suburb: str | None, postcode: str | None) -> str:
    return f"{norm(suburb).replace(' ', '')}|{postcode or ''}"


def canon_key(employer: str | None, title: str | None,
              suburb: str | None, postcode: str | None) -> tuple[str, str]:
    """Chave canônica exata. Devolve (hash, texto legível)."""
    raw = f"{canon_employer(employer)}::{canon_role(title)}::{canon_locality(suburb, postcode)}"
    return hashlib.blake2b(raw.encode(), digest_size=12).hexdigest(), raw


def employer_is_anonymous(employer: str | None) -> bool:
    """Anúncio de agência sem nome de empregador.

    Este é o ponto de falha da chave exata: com empregador vazio, todos os
    kitchen hands anônimos do CBD colapsam na mesma chave. Quando isto é
    verdade, a chave exata não se aplica e vai direto para o fuzzy.
    """
    e = norm(employer)
    if not e:
        return True
    return e in {
        "private advertiser", "confidential", "our client", "client",
        "not disclosed", "undisclosed", "hidden", "n a", "unknown",
        "private company", "company confidential",
    }


def body_shingle(text: str, size: int = 400) -> str:
    """Miolo do anúncio, normalizado, para comparação fuzzy."""
    return norm(text)[:size]


def fuzzy_match_score(
    role_a: str, role_b: str,
    employer_a: str, employer_b: str,
    body_a: str, body_b: str,
    postcode_a: str | None, postcode_b: str | None,
    salary_a: tuple | None = None, salary_b: tuple | None = None,
) -> float:
    """0–100. Acima de 78 é a mesma vaga; 62–78 é zona cinzenta."""
    if role_a != role_b:
        return 0.0
    if postcode_a and postcode_b and postcode_a[:3] != postcode_b[:3]:
        return 0.0

    emp = fuzz.token_set_ratio(employer_a, employer_b) if (employer_a and employer_b) else 50.0
    body = fuzz.token_set_ratio(body_a, body_b) if (body_a and body_b) else 0.0
    bonus = 10.0 if (salary_a and salary_b and salary_a == salary_b) else 0.0
    return min(100.0, 0.45 * emp + 0.45 * body + bonus)


FUZZY_SAME = 78.0
FUZZY_GREY = 62.0
