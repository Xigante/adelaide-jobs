"""`doctor` — o que a sua máquina consegue alcançar, de fato.

Existe porque o resto do projeto foi escrito sem conseguir testar rede:
o container e o shell da máquina bloqueiam saída. Esta é a verificação
que só você pode rodar, e ela responde a pergunta que decide o desenho —
a v5 do SEEK responde do seu IP?
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass

import httpx

from .collectors.base import USER_AGENT


@dataclass(slots=True)
class Check:
    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        mark = "OK  " if self.ok else "FALHA"
        return f"[{mark}] {self.name:<30} {self.detail}"


def _url_adzuna() -> str:
    """Um pedido de verdade, com as chaves dele.

    O teste antigo batia em /v1/api/version SEM credencial, e a Adzuna
    responde 400 a isso. Resultado: "[FALHA] Adzuna API HTTP 400" em
    toda instalacao, inclusive nas que coletam 500 vagas por dia. Um
    alarme que sempre toca nao e alarme — e o Pedro passou por uma
    mudanca de PC achando que a chave dele tinha quebrado.

    Agora o teste faz o mesmo que o coletor faz: uma busca de 1
    resultado. Se responder 200, a chave funciona. Se responder 401,
    a chave esta errada — e ai a falha quer dizer alguma coisa.
    """
    ident = os.getenv("ADZUNA_APP_ID", "")
    chave = os.getenv("ADZUNA_APP_KEY", "")
    return ("https://api.adzuna.com/v1/api/jobs/au/search/1"
            f"?app_id={ident}&app_key={chave}&results_per_page=1"
            "&where=Adelaide&content-type=application/json")


PROBES: list[tuple[str, str]] = [
    ("SmartRecruiters", "https://api.smartrecruiters.com/v1/companies/McDonaldsAustralia/postings?limit=1"),
    ("Greenhouse", "https://boards-api.greenhouse.io/v1/boards/gitlab/jobs"),
    ("McDonald's AU", "https://careers.mcdonalds.com.au/robots.txt"),
    ("Coles sitemap", "https://colescareers.com.au/au/en/sitemap.xml"),
    ("SEEK v5 (contra ToS)", "https://www.seek.com.au/api/jobsearch/v5/search"
                             "?siteKey=AU-Main&sourcesystem=houston"
                             "&where=All%20Adelaide%20SA&page=1&pageSize=5&locale=en-AU"),
]


def check_env() -> list[Check]:
    checks = []
    for var, label in [
        ("ADZUNA_APP_ID", "Adzuna app id"),
        ("ADZUNA_APP_KEY", "Adzuna app key"),
        ("GOOGLE_SHEETS_ID", "Google Sheets id"),
    ]:
        val = os.getenv(var, "")
        # O Google Sheets nunca foi ligado. Marcar como FALHA todo dia
        # treina a pessoa a ignorar a coluna de falhas — e ai a falha
        # que importa passa despercebida no meio.
        opcional = var.startswith("GOOGLE_SHEETS")
        checks.append(Check(
            label, bool(val) or opcional,
            "definido" if val else ("nao usado (opcional)" if opcional
                                    else f"{var} vazio no .env")))
    return checks


def check_optional_packages() -> list[Check]:
    checks = []
    for mod, label, extra in [
        ("ats_scrapers", "ats-scrapers", "[ats]"),
        ("gspread", "gspread", "[sheets]"),
    ]:
        try:
            __import__(mod)
            checks.append(Check(label, True, "instalado"))
        except ImportError:
            opcional = extra == "[sheets]"
            checks.append(Check(
                label, opcional,
                "nao usado (opcional)" if opcional
                else f'pip install "adelaide-jobs{extra}"'))
    return checks


def check_network(timeout: float = 15.0) -> list[Check]:
    checks = []
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json,*/*"}
    with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
        for name, url in [("Adzuna API", _url_adzuna()), *PROBES]:
            try:
                resp = client.get(url)
            except (httpx.HTTPError, socket.gaierror) as exc:
                checks.append(Check(name, False, f"{type(exc).__name__}"))
                continue
            ok = resp.status_code in (200, 401)   # 401 = alcançável, só falta chave
            detail = f"HTTP {resp.status_code}"
            if resp.status_code == 403:
                detail += " — bloqueado (Cloudflare / IP de datacenter)"
            elif resp.status_code == 200 and "json" in resp.headers.get("content-type", ""):
                detail += f", {len(resp.content)} bytes de JSON"
            checks.append(Check(name, ok, detail))
    return checks


def run(skip_network: bool = False) -> tuple[list[Check], bool]:
    checks = check_env() + check_optional_packages()
    if not skip_network:
        checks += check_network()
    return checks, all(c.ok for c in checks)
