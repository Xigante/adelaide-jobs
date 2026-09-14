"""Repetir quando a Adzuna tropeça, sem torrar a cota.

Em 14/09 uma coleta voltou com 44 erros, quase todos HTTP 502 — a
Adzuna caindo do lado dela. Sem repetição, um 502 na PÁGINA 1 matava a
categoria inteira: admin-jobs, accounting-finance, consultancy e hr
voltaram vazias no mesmo dia, e são justamente as de escritório.

Repetir custa cota (250 chamadas por dia, a coleta já usa 173), então
o que estes testes protegem é o equilíbrio: repete o suficiente para
sobreviver a um soluço, e para de repetir antes de comer o orçamento.
"""
from __future__ import annotations

import sys
import types

import httpx
import pytest

from adelaide_jobs.collectors.adzuna import AdzunaCollector


class RespostaFake:
    def __init__(self, status: int) -> None:
        self.status_code = status


class ClienteFake:
    """Devolve os status da lista, em ordem, e conta as chamadas."""

    def __init__(self, *status: int | type) -> None:
        self.roteiro = list(status)
        self.chamadas = 0

    def get(self, url, params=None):          # noqa: D102, ANN001
        self.chamadas += 1
        item = self.roteiro[min(self.chamadas - 1, len(self.roteiro) - 1)]
        if isinstance(item, type) and issubclass(item, Exception):
            raise item("caiu")
        return RespostaFake(item)


@pytest.fixture()
def coletor(monkeypatch):
    c = AdzunaCollector.__new__(AdzunaCollector)
    c.erros = []
    c.note_error = c.erros.append
    c._orcamento_retry = AdzunaCollector.RETRY_MAX
    monkeypatch.setattr("adelaide_jobs.collectors.adzuna.time.sleep",
                        lambda *_: None)
    return c


def _pedir(c, cliente):
    return c._pedir(cliente, "http://x", {}, "cat:admin-jobs", 1)


def test_de_primeira_nao_repete(coletor):
    cli = ClienteFake(200)
    resp, motivo = _pedir(coletor, cli)
    assert resp is not None and motivo == ""
    assert cli.chamadas == 1
    assert coletor.erros == []


def test_502_e_depois_200_sobrevive(coletor):
    """O caso de 14/09: um soluço no meio não pode matar a categoria."""
    cli = ClienteFake(502, 200)
    resp, motivo = _pedir(coletor, cli)
    assert resp is not None and motivo == ""
    assert cli.chamadas == 2
    assert coletor.erros == [], "acertou na 2a: não é erro para reportar"


def test_502_sempre_desiste_e_avisa_uma_vez_so(coletor):
    cli = ClienteFake(502)
    resp, motivo = _pedir(coletor, cli)
    assert resp is None and motivo == "transitorio"
    assert cli.chamadas == AdzunaCollector.TENTATIVAS
    assert len(coletor.erros) == 1
    assert "desisti" in coletor.erros[0]
    assert "cat:admin-jobs" in coletor.erros[0]


def test_erro_de_rede_tambem_repete(coletor):
    cli = ClienteFake(httpx.ConnectError, 200)
    resp, _ = _pedir(coletor, cli)
    assert resp is not None
    assert cli.chamadas == 2


def test_429_para_na_hora_sem_repetir(coletor):
    """Repetir depois do limite diário só queima o que não existe."""
    cli = ClienteFake(429)
    resp, motivo = _pedir(coletor, cli)
    assert resp is None and motivo == "cota"
    assert cli.chamadas == 1


def test_404_nao_repete(coletor):
    """Pedido errado não melhora na segunda tentativa."""
    cli = ClienteFake(404)
    resp, motivo = _pedir(coletor, cli)
    assert resp is None and motivo == "permanente"
    assert cli.chamadas == 1
    assert "HTTP 404" in coletor.erros[0]


def test_orcamento_esgotado_para_de_repetir(coletor):
    """Um dia ruim da Adzuna não pode gastar a cota inteira em repetição."""
    coletor._orcamento_retry = 0
    cli = ClienteFake(502)
    resp, _ = _pedir(coletor, cli)
    assert resp is None
    assert cli.chamadas == 1, "sem orçamento, tenta uma vez e desiste"


def test_o_orcamento_e_por_rodada_nao_por_pedido(coletor):
    """Duas páginas ruins consomem do mesmo bolso."""
    antes = coletor._orcamento_retry
    _pedir(coletor, ClienteFake(502))
    meio = coletor._orcamento_retry
    _pedir(coletor, ClienteFake(502))
    assert meio < antes
    assert coletor._orcamento_retry < meio
