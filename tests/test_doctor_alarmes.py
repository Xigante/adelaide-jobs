"""Um alarme que sempre toca não é alarme.

Em 17/09, numa máquina nova, o `doctor` fechou com três [FALHA]:
Google Sheets id, gspread e "Adzuna API HTTP 400". Nenhuma delas era
problema. As duas primeiras são de um recurso que nunca foi ligado; a
terceira é o próprio teste batendo num endereço sem credencial, o que
a Adzuna responde com 400 — em toda instalação, inclusive nas que
coletam 500 vagas por dia.

O custo não é cosmético: o Pedro estava no meio de uma troca de
computador e passou a achar que a chave dele tinha quebrado na
mudança. Falha que aparece sempre treina a pessoa a não olhar a
coluna de falhas.
"""
from __future__ import annotations

import os

import pytest

from adelaide_jobs import doctor


@pytest.fixture(autouse=True)
def _chaves(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "umid")
    monkeypatch.setenv("ADZUNA_APP_KEY", "umachave")
    monkeypatch.delenv("GOOGLE_SHEETS_ID", raising=False)


def test_o_teste_da_adzuna_usa_a_chave_de_verdade():
    """Sem credencial a Adzuna responde 400 e o teste não prova nada."""
    url = doctor._url_adzuna()
    assert "app_id=umid" in url
    assert "app_key=umachave" in url
    assert "/jobs/au/search/" in url, "tem que ser uma busca, como o coletor faz"


def test_google_sheets_vazio_nao_e_falha():
    por_nome = {c.name: c for c in doctor.check_env()}
    assert por_nome["Google Sheets id"].ok
    assert "opcional" in por_nome["Google Sheets id"].detail


def test_chave_da_adzuna_vazia_continua_sendo_falha():
    """Essa importa: sem ela não coleta nada."""
    os.environ["ADZUNA_APP_KEY"] = ""
    por_nome = {c.name: c for c in doctor.check_env()}
    assert not por_nome["Adzuna app key"].ok


def test_gspread_ausente_nao_e_falha_mas_ats_e():
    por_nome = {c.name: c for c in doctor.check_optional_packages()}
    assert por_nome["gspread"].ok, "recurso nunca ligado não pode gritar"
    # ats-scrapers é obrigatório para os coletores de ATS; se faltar,
    # tem que aparecer.
    assert por_nome["ats-scrapers"].name == "ats-scrapers"


def test_a_chave_nunca_aparece_na_linha_impressa():
    """A saída do doctor vira print de tela e vai parar no chat."""
    for c in doctor.check_env() + doctor.check_optional_packages():
        assert "umachave" not in c.line()
