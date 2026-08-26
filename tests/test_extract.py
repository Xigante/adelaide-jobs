"""O extrator é o que separa 'exige' de 'seria bom'."""

import pytest

from adelaide_jobs.extract import RuleExtractor, title_is_senior
from adelaide_jobs.models import Job

BOH = ["kitchen hand", "kitchenhand", "dishwasher", "night fill", "cleaner", "warehouse"]


def make(title="Kitchen Hand", desc="", employer=None, suburb=None):
    return Job(source="t", source_id="1", title=title, url="u",
               employer=employer, description=desc, suburb=suburb)


@pytest.fixture
def ex():
    return RuleExtractor(BOH)


# ── a armadilha do full-time ────────────────────────────────────────

def test_mixed_ad_is_not_full_time(ex):
    """Uma fração enorme dos anúncios entry-level australianos diz isto.

    Bloquear como full-time destrói o pipeline — é o erro nº 1 da lista.
    """
    d = ex.extract(make(desc="Casual, part-time and full-time positions available."))
    assert d.emp_type == "MIXED"


def test_genuine_full_time_detected(ex):
    d = ex.extract(make(desc="Full time role, 38 hours per week, Monday to Friday."))
    assert d.emp_type == "FULL_TIME"


def test_casual_only(ex):
    assert ex.extract(make(desc="Casual position, a few shifts per week.")).emp_type == "CASUAL"


# ── essential vs desirable ──────────────────────────────────────────

def test_desirable_certificate_is_not_essential(ex):
    d = ex.extract(make(desc="Food handling certificate desirable but not essential."))
    assert d.food_handling == "DESIRABLE"


def test_essential_licence_detected(ex):
    d = ex.extract(make(desc="A current Australian driver's licence is essential for this role."))
    assert d.au_licence == "ESSENTIAL"


def test_preferred_transport_is_not_essential(ex):
    """"Own transport preferred" aparece em muita vaga de limpeza.
    Tratar como essencial derruba vaga boa."""
    d = ex.extract(make(desc="Own transport preferred but not required."))
    assert d.au_licence == "DESIRABLE"


def test_ambiguous_requirement_defaults_to_soft(ex):
    d = ex.extract(make(desc="RSA."))
    assert d.rsa == "DESIRABLE"


# ── experiência ─────────────────────────────────────────────────────

def test_no_experience_needed(ex):
    d = ex.extract(make(desc="No experience necessary, full training provided."))
    assert d.exp_req == "NONE_REQUIRED"


def test_years_required(ex):
    d = ex.extract(make(desc="Minimum 5 years experience is essential."))
    assert d.exp_req == "YEARS_REQUIRED"
    assert d.exp_years == 5


def test_years_only_preferred(ex):
    d = ex.extract(make(desc="2 years experience desirable."))
    assert d.exp_req == "SOME_PREFERRED"


# ── inglês e turno ──────────────────────────────────────────────────

def test_boh_title_means_minimal_english(ex):
    assert ex.extract(make(title="Kitchen Hand")).eng_contact == "BOH_MINIMAL"


def test_customer_facing_raises_english_load(ex):
    d = ex.extract(make(title="Front Counter", desc="Serving customers and taking orders."))
    assert d.eng_contact == "MEDIUM"


def test_fluent_english_is_high(ex):
    d = ex.extract(make(title="Receptionist", desc="Excellent verbal communication required."))
    assert d.eng_contact == "HIGH"


def test_overnight_shift(ex):
    assert ex.extract(make(desc="Shifts start at 10pm.")).shift_window == "OVERNIGHT"


# ── senior só no título ─────────────────────────────────────────────

def test_senior_in_body_does_not_count():
    """"Senior Living facility" é vaga de aged care, não cargo sênior."""
    assert not title_is_senior("Cleaner - Aged Care")


def test_senior_in_title_counts():
    assert title_is_senior("Senior Restaurant Manager")


# ── direito de trabalho ─────────────────────────────────────────────

def test_full_rights_required_detected(ex):
    d = ex.extract(make(desc="Applicants must have full working rights in Australia."))
    assert d.work_rights == "FULL_RIGHTS_REQUIRED"


def test_student_visa_welcome(ex):
    d = ex.extract(make(desc="Student visa holders welcome to apply."))
    assert d.work_rights == "STUDENT_OK"


# ── geo ─────────────────────────────────────────────────────────────

def test_distance_from_suburb_name(ex):
    d = ex.extract(make(suburb="Elizabeth"))
    assert d.distance_km is not None and d.distance_km > 20


def test_cbd_is_close(ex):
    d = ex.extract(make(suburb="Adelaide"))
    assert d.distance_km is not None and d.distance_km < 2
