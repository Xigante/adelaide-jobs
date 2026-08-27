"""PageUp clássico — o ATS de quase todo empregador público de Adelaide.

Por que isto existe: o SA Health sozinho tem ~625 vagas ativas, quase
todas na Grande Adelaide, e hospital emprega muito back of house —
Hotel Services Assistant, Food Services Assistant, Cleaner, Ward
Assistant. Era a maior fonte que faltava, e o link já é o do empregador.

DUAS LIMITAÇÕES, ambas medidas no navegador em 27/08/2026, não supostas:

1. A LISTAGEM é HTML puro e pagina com `?page=N`, 24 linhas por página.
   Mas as PÁGINAS DE DETALHE respondem 202 com corpo vazio para cliente
   sem desafio resolvido — proteção anti-bot. Ou seja: dá para saber o
   título, o número, o local e o prazo; não dá para ler a descrição.

   A consequência é honesta e visível: sem descrição o extrator marca
   quase tudo como UNKNOWN e a vaga pontua no meio da tabela. É melhor
   que não vê-la. O botão "Candidatar-se" leva à página real, e é lá
   que você lê o anúncio.

2. `?search-keyword=` NÃO filtra (devolve zero). Só a varredura por
   página funciona. Por isso `max_pages` existe: 26 páginas cobrem o
   SA Health inteiro a 1,5 s por página, cerca de 40 segundos.

Se um dia a listagem também passar a exigir desafio, o coletor não
devolve zero em silêncio — ele reclama, com o código HTTP.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from ..models import EmploymentType, Job, Legitimacy
from .base import BaseCollector, CollectorError, USER_AGENT, register

#: Localidade que conta como Adelaide. O PageUp do SA Health escreve
#: "Adelaide Metro Southern", "Adelaide CBD", "Adelaide Hills".
RE_METRO = re.compile(r"\badelaide\b|\bmetro\b|\bcbd\b", re.I)

#: "13 Sep" — o ano fica implícito, o que é um problema em dezembro.
RE_FECHA = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]{3})", re.I)

_MESES = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), start=1)}


def _prazo(texto: str, hoje: date | None = None) -> date | None:
    """Converte "13 Sep" na próxima data que cai nesse dia.

    Sem ano no HTML, "02 Jan" visto em dezembro é do ano que vem. Assumir
    o ano corrente marcaria a vaga como vencida e ela sumiria da fila.
    """
    m = RE_FECHA.match(texto or "")
    if not m:
        return None
    hoje = hoje or date.today()
    mes = _MESES.get(m.group(2).lower())
    if not mes:
        return None
    try:
        d = date(hoje.year, mes, int(m.group(1)))
    except ValueError:
        return None
    return d.replace(year=hoje.year + 1) if (hoje - d).days > 180 else d


@register
class PageUpCollector(BaseCollector):
    """Varre a listagem de um ou mais career sites PageUp clássicos."""

    name = "pageup"
    legitimacy = Legitimacy.OPEN_ROBOTS
    min_interval = 1.5

    def collect(self) -> list[Job]:
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError as exc:  # pragma: no cover
            raise CollectorError(
                'Faltam dependências. Rode: pip install -e ".[ats]"'
            ) from exc

        alvos: list[dict[str, Any]] = self.config.get("targets") or []
        max_pages = int(self.config.get("max_pages", 30))
        so_metro = bool(self.config.get("only_metro", True))
        vagas: list[Job] = []

        with httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            timeout=25.0, follow_redirects=True,
        ) as client:
            for alvo in alvos:
                rotulo = alvo.get("name", "?")
                base = str(alvo.get("url", "")).rstrip("/")
                if not base:
                    self.note_error(f"{rotulo}: sem url")
                    continue
                vistos: set[str] = set()
                for pagina in range(1, max_pages + 1):
                    self.throttle()
                    try:
                        r = client.get(base, params={"page": pagina})
                    except Exception as exc:  # noqa: BLE001
                        self.note_error(f"{rotulo} p{pagina}: {type(exc).__name__}: {exc}")
                        break
                    linhas = self.parse(r.text, base, rotulo)
                    if not linhas:
                        if pagina == 1:
                            # Zero na primeira página não é "não há vagas",
                            # é quase sempre desafio anti-bot. Diga qual.
                            self.note_error(
                                f"{rotulo}: nenhuma vaga na página 1 "
                                f"(HTTP {r.status_code}, {len(r.text)} bytes). "
                                "Se o corpo veio vazio, o site exige navegador."
                            )
                        break
                    novas = [j for j in linhas if j.source_id not in vistos]
                    if not novas:
                        break          # a paginação circulou
                    vistos.update(j.source_id for j in novas)
                    vagas.extend(
                        j for j in novas
                        if not so_metro or RE_METRO.search(j.suburb or "")
                    )
        return vagas

    @classmethod
    def parse(cls, html: str, base_url: str, empregador: str) -> list[Job]:
        """HTML → Jobs. Função pura: é o que os testes exercitam.

        Colunas medidas no SA Health: Position | Job No. | Location | Closes.
        Ler por posição de coluna é frágil, então lemos por âncora
        (`a.job-link`) e pegamos as irmãs — se o site inserir uma coluna,
        continua funcionando.
        """
        from bs4 import BeautifulSoup

        origem = re.match(r"https?://[^/]+", base_url)
        origem = origem.group(0) if origem else ""
        sopa = BeautifulSoup(html, "html.parser")
        vagas: list[Job] = []

        for link in sopa.select("a.job-link"):
            titulo = link.get_text(" ", strip=True)
            href = str(link.get("href") or "")
            if not titulo or not href:
                continue
            linha = link.find_parent("tr")
            celulas = (
                [c.get_text(" ", strip=True) for c in linha.find_all("td")]
                if linha else []
            )
            # A coluna do próprio título é a primeira; as outras vêm depois.
            resto = [c for c in celulas if c and c != titulo]
            numero = next((c for c in resto if c.isdigit()), "")
            fecha = next((c for c in resto if RE_FECHA.match(c)), "")
            local = next(
                (c for c in resto if c not in (numero, fecha) and not c.isdigit()), ""
            )
            # /caw/en/job/937691/slug  →  937691
            m = re.search(r"/job/(\d+)", href)
            ident = numero or (m.group(1) if m else href)

            vagas.append(Job(
                source="pageup",
                source_id=f"{empregador}:{ident}",
                title=titulo,
                url=href if href.startswith("http") else origem + href,
                employer=empregador,
                description="",     # detalhe é bloqueado; ver docstring
                suburb=local or None,
                state="SA",
                employment_type=EmploymentType.UNKNOWN,
                posted_at=None,
                legitimacy=cls.legitimacy,
                raw={"job_no": numero, "closes": fecha},
            ))
        return vagas
