"""Knockouts e score. A regra de calibração é assimétrica de propósito:
falso negativo em knockout custa tokens; falso positivo custa uma vaga."""

from adelaide_jobs import filters
from adelaide_jobs.models import Dimensions, Job
from adelaide_jobs.scoring import DEFAULT_WEIGHTS, score


def job(title="Kitchen Hand", desc=""):
    return Job(source="t", source_id="1", title=title, url="u", description=desc)


def dims(**kw):
    return Dimensions(**kw)


# ── knockouts ───────────────────────────────────────────────────────

def test_full_time_blocked():
    ko = filters.check(job(), dims(emp_type="FULL_TIME"))
    assert ko and ko.code == "FULL_TIME_ONLY"


def test_mixed_employment_not_blocked():
    assert filters.check(job(), dims(emp_type="MIXED")) is None


def test_two_years_required_blocked():
    ko = filters.check(job(), dims(exp_req="YEARS_REQUIRED", exp_years=3))
    assert ko and ko.code == "MIN_EXPERIENCE_2Y_PLUS"


def test_one_year_required_not_blocked():
    assert filters.check(job(), dims(exp_req="YEARS_REQUIRED", exp_years=1)) is None


def test_desirable_licence_not_blocked():
    assert filters.check(job(), dims(au_licence="DESIRABLE")) is None


def test_essential_licence_blocked():
    ko = filters.check(job(), dims(au_licence="ESSENTIAL"))
    assert ko and ko.code == "AU_LICENCE_ESSENTIAL"


def test_full_rights_blocked():
    ko = filters.check(job(), dims(work_rights="FULL_RIGHTS_REQUIRED"))
    assert ko and ko.code == "NO_WORK_RIGHTS"


def test_senior_title_blocked():
    ko = filters.check(job(title="Senior Data Analyst"), dims())
    assert ko and ko.code == "SENIOR_ROLE"


def test_aged_care_cleaner_not_blocked():
    """"Senior Living" no corpo não pode derrubar vaga de limpeza."""
    j = job(title="Cleaner", desc="Work at our Senior Living facility in Adelaide.")
    assert filters.check(j, dims()) is None


def test_out_of_range_blocked():
    ko = filters.check(job(), dims(distance_km=40.0), max_commute_km=25)
    assert ko and ko.code == "OUT_OF_RANGE"


def test_unknown_distance_not_blocked():
    """Distância desconhecida não é ruim, é desconhecida."""
    assert filters.check(job(), dims(distance_km=None)) is None


# ── score ───────────────────────────────────────────────────────────

def test_weights_sum_to_100():
    assert sum(DEFAULT_WEIGHTS.values()) == 100


def test_ideal_job_scores_high():
    d = dims(exp_req="NONE_REQUIRED", eng_contact="BOH_MINIMAL", emp_type="CASUAL",
             hours_pattern="FLEXIBLE_LOW", shift_window="OVERNIGHT",
             employer_kind="LARGE_CHAIN", distance_km=3.0)
    assert score(d).total >= 90


def test_bad_fit_scores_low():
    d = dims(exp_req="SOME_REQUIRED", eng_contact="HIGH", emp_type="NOT_STATED",
             hours_pattern="NEAR_FULL_TIME", shift_window="DAYTIME",
             employer_kind="UNKNOWN", distance_km=22.0, rsa="ESSENTIAL")
    assert score(d).total <= 35


def test_score_is_bounded():
    for d in (dims(), dims(distance_km=0.0, exp_req="NONE_REQUIRED")):
        assert 0 <= score(d).total <= 100


def test_ghost_penalty_applied():
    d = dims(exp_req="NONE_REQUIRED", eng_contact="BOH_MINIMAL", distance_km=2.0)
    clean = score(d).total
    haunted = score(d, ghost=True, ghost_penalty=15).total
    assert clean - haunted == 15


def test_multi_source_bonus():
    d = dims(exp_req="NOT_STATED", distance_km=10.0)
    assert score(d, multi_source=3).total > score(d, multi_source=1).total


def test_near_full_time_casual_is_a_trap():
    """"Casual, up to 38 hours" passa de 48h/quinzena."""
    good = dims(emp_type="CASUAL", hours_pattern="FLEXIBLE_LOW")
    trap = dims(emp_type="CASUAL", hours_pattern="NEAR_FULL_TIME")
    assert score(good).total > score(trap).total


def test_night_shift_far_away_is_penalised():
    """Night fill que termina às 2h em Elizabeth paga bem e é
    inalcançável sem carro."""
    near = dims(shift_window="OVERNIGHT", distance_km=3.0)
    far = dims(shift_window="OVERNIGHT", distance_km=20.0)
    assert score(near).parts["shift_fit"] > score(far).parts["shift_fit"]


def test_pm_class_kills_evening_shifts():
    d = dims(shift_window="EVENING", distance_km=3.0)
    assert score(d, class_pattern="PM").total < score(d, class_pattern="AM").total


def test_breakdown_explains_itself():
    text = score(dims(exp_req="NONE_REQUIRED")).explain()
    assert "experience_barrier" in text and "score" in text
