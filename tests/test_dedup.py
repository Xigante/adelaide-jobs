"""O dedup é o que impede você de se candidatar duas vezes na mesma vaga."""

import pytest

from adelaide_jobs.dedup import (
    canon_employer, canon_key, canon_role, employer_is_anonymous, fuzzy_match_score,
)


@pytest.mark.parametrize("title,expected", [
    ("Kitchen Hand", "kitchen_hand"),
    ("Kitchenhand - URGENT", "kitchen_hand"),
    ("Dishwasher", "kitchen_hand"),
    ("Kitchen Attendant (Casual)", "kitchen_hand"),
    ("Dish Hand — immediate start", "kitchen_hand"),
    ("NIGHTFILL", "night_fill"),
    ("Night Filler | Coles Mile End", "night_fill"),
    ("Commercial Cleaner", "cleaning"),
    ("Room Attendant", "cleaning"),
    ("Pick Packer", "warehouse"),
    ("Storeperson", "warehouse"),
    ("Barista", "barista"),
])
def test_role_synonyms_collapse(title, expected):
    assert canon_role(title) == expected


def test_specific_role_beats_generic():
    """A armadilha: "team member" é mais longo que "night fill".

    Se a busca fosse pelo match mais longo, esta vaga viraria team_member
    e um turno noturno de supermercado sairia do radar de back-of-house.
    """
    assert canon_role("Night Fill Team Member") == "night_fill"
    assert canon_role("Team Member - Retail") == "team_member"


def test_employer_legal_suffixes_collapse():
    assert canon_employer("Coles Group Pty Ltd") == canon_employer("COLES GROUP LIMITED")
    assert canon_employer("Woolworths Group Australia") == "woolworths"


@pytest.mark.parametrize("employer", [
    None, "", "Private Advertiser", "Confidential", "Our Client", "Not Disclosed",
])
def test_anonymous_employers_detected(employer):
    """Com empregador anônimo a chave exata colapsaria todos os kitchen
    hands de agência do CBD numa vaga só."""
    assert employer_is_anonymous(employer)


def test_named_employer_not_anonymous():
    assert not employer_is_anonymous("Coles Supermarkets")


def test_same_job_different_wording_same_key():
    a, _ = canon_key("Coles Pty Ltd", "Night Fill Team Member", "Mile End", "5031")
    b, _ = canon_key("COLES GROUP", "NIGHTFILL - urgent", "mile end", "5031")
    assert a == b


def test_different_suburb_different_key():
    a, _ = canon_key("Coles", "Night Fill", "Mile End", "5031")
    b, _ = canon_key("Coles", "Night Fill", "Glenelg", "5045")
    assert a != b


def test_fuzzy_requires_same_role():
    assert fuzzy_match_score(
        "kitchen_hand", "cleaning", "acme", "acme", "same body", "same body", None, None
    ) == 0.0


def test_fuzzy_matches_same_job_across_sources():
    s = fuzzy_match_score(
        "kitchen_hand", "kitchen_hand",
        "adelaidebistro", "adelaide bistro group",
        "busy cbd venue casual kitchen hand no experience necessary",
        "busy cbd venue casual kitchen hand no experience necessary full training",
        "5000", "5000",
    )
    assert s >= 78.0


def test_fuzzy_rejects_different_postcode_area():
    assert fuzzy_match_score(
        "kitchen_hand", "kitchen_hand", "acme", "acme", "x", "x", "5000", "5112"
    ) == 0.0
