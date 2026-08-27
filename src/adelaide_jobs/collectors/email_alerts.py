"""Alertas de e-mail — a porta que o SEEK e o LinkedIn deixam aberta.

═══════════════════════════════════════════════════════════════════════
 POR QUE ESTE COLETOR EXISTE

 O SEEK é o maior mercado de trabalho de Adelaide e não tem API pública.
 O LinkedIn idem. Os dois respondem 403 para quem não é navegador e os
 dois proíbem acesso automatizado nos termos de uso. Raspar qualquer um
 dos dois arrisca justamente a conta que vai ser o seu canal principal
 de emprego na cidade onde você vai morar. A troca é ruim: ganha-se
 conveniência, perde-se acesso.

 Mas os dois mandam ALERTA POR E-MAIL. Você assina, eles entregam, e o
 e-mail é seu. Ler a sua própria caixa de entrada não viola termo
 nenhum — a plataforma está te entregando o dado de propósito, pelo
 canal que ela mesma construiu para isso.

 É a mesma informação, com um dia de atraso no pior caso.

 O QUE ELE EXTRAI

 Não parseia layout. Layout de e-mail de marketing é gerado por
 ferramenta e muda sem aviso — classe CSS aqui é areia. O que é estável
 é o PADRÃO DA URL da vaga, e é só isso que este coletor procura.

 Daí a consequência: sai título e link, não sai a descrição. A vaga
 pontua pelo título e o botão "Candidatar-se" leva ao anúncio. Quando o
 mesmo anúncio também vier da Adzuna ou de um ATS, a deduplicação junta
 os dois e a descrição vem do outro lado — que é exatamente o efeito
 que se quer de ter várias fontes.

 SE MESMO ASSIM VOCÊ QUISER O SEEK DIRETO
 O código está em collectors/seek_v5.py, funcionando, desligado, com o
 aviso no cabeçalho. A decisão é sua e o interruptor está em
 config/sources.yaml. Eu não ligo por você.
═══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import base64
import email
import imaplib
import os
import re
from datetime import date, datetime, timedelta
from email.message import Message
from typing import Any, Iterable

from ..models import EmploymentType, Job, Legitimacy
from .base import BaseCollector, CollectorError, register

# ── Padrões de URL de vaga, por plataforma ──────────────────────────
# Cada entrada: (regex com um grupo de captura = id, molde da URL
# canônica). O id é o que dedup usa; a URL canônica é a que abre.
#
# Todos verificados em 27/08/2026 contra a forma real que aparece nos
# alertas. Repare que quase nenhum link do e-mail é o link final: o
# SEEK e o LinkedIn embrulham em rastreador, mas em ambos o ID da vaga
# viaja legível dentro da própria URL — então dá para reconstruir o
# link limpo sem seguir o redirect, que é lento e às vezes bloqueado.
PADROES: dict[str, tuple[re.Pattern[str], str]] = {
    "seek": (
        re.compile(r"seek\.com(?:\.au)?/job/(\d+)", re.I),
        "https://www.seek.com.au/job/{}",
    ),
    "linkedin": (
        # /comm/jobs/view/ é a forma que aparece no e-mail; /jobs/view/
        # é a forma limpa. As duas casam, o id é o mesmo.
        re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", re.I),
        "https://www.linkedin.com/jobs/view/{}",
    ),
    "indeed": (
        re.compile(r"indeed\.com(?:\.au)?/[^\s\"'<>]*?[?&]jk=([0-9a-f]{8,20})", re.I),
        "https://au.indeed.com/viewjob?jk={}",
    ),
    "jora": (
        re.compile(r"jora\.com(?:\.au)?/job/[\w-]*?-([0-9a-f]{10,})", re.I),
        "https://au.jora.com/job/x-{}",
    ),
    "adzuna": (
        re.compile(r"adzuna\.com\.au/(?:land/ad|details)/(\d+)", re.I),
        "https://www.adzuna.com.au/details/{}",
    ),
    "iworkfor": (
        re.compile(r"iworkfor\.sa\.gov\.au/[^\s\"'<>]*?[?&]jobID=(\d+)", re.I),
        "https://www.iworkfor.sa.gov.au/?jobID={}",
    ),
    "gumtree": (
        re.compile(r"gumtree\.com\.au/s-ad/[^\s\"'<>]*?/(\d{8,})", re.I),
        "https://www.gumtree.com.au/s-ad/{}",
    ),
}

RE_URL = re.compile(r"https?://[^\s\"'<>)\]]+")

#: Parâmetros em que rastreadores costumam esconder a URL de destino.
PARAMS_DESTINO = ("url", "u", "redirect", "redirect_url", "target", "destination", "r")

#: Texto de âncora que nunca é título de vaga.
RUIDO = re.compile(
    r"^(ver (todas|mais)|see all|view (job|all)|apply|candidatar|unsubscribe|"
    r"cancelar|descadastrar|configurações|settings|privacy|política|"
    r"mais vagas|more jobs|\d+\s*(novas?|new)|clique aqui|click here)\b",
    re.I,
)


def desembrulhar(url: str) -> str:
    """Devolve a URL real de dentro de um link de rastreio, sem segui-lo.

    Seguir redirect custa uma requisição por vaga, é lento e alguns
    rastreadores bloqueiam cliente que não é navegador. Felizmente
    quase todos carregam o destino na própria URL, de dois jeitos: num
    parâmetro da query string, ou como base64url num segmento do path.
    """
    from urllib.parse import parse_qs, unquote, urlparse

    try:
        partes = urlparse(url)
    except ValueError:
        return url

    valores = parse_qs(partes.query)
    for chave in PARAMS_DESTINO:
        if chave in valores and valores[chave]:
            candidato = unquote(valores[chave][0])
            if candidato.startswith("http"):
                return candidato

    # O SEEK embute o destino percent-encoded no PATH, não na query:
    #   click.seek.com.au/f/a/…/h/https%3A%2F%2Fwww.seek.com.au%2Fjob%2F842…
    # Decodificar a URL inteira e pegar o último "http" que aparecer
    # resolve essa família toda de uma vez.
    decodificada = unquote(url)
    if decodificada != url:
        ocorrencias = list(re.finditer(r"https?://", decodificada))
        if len(ocorrencias) > 1:
            return decodificada[ocorrencias[-1].start():]

    for segmento in partes.path.split("/"):
        if len(segmento) < 16 or not re.fullmatch(r"[A-Za-z0-9_-]+", segmento):
            continue
        try:
            texto = base64.urlsafe_b64decode(
                segmento + "=" * (-len(segmento) % 4)
            ).decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001 — lixo em base64 é normal aqui
            continue
        if texto.startswith("http"):
            return texto
    return url


def identificar(url: str) -> tuple[str, str, str] | None:
    """(plataforma, id, url canônica) para uma URL, ou None se não for vaga."""
    for plataforma, (padrao, molde) in PADROES.items():
        m = padrao.search(url)
        if m:
            return plataforma, m.group(1), molde.format(m.group(1))
    return None


def _partes(msg: Message) -> tuple[str, str]:
    """(texto puro, html) de uma mensagem, decodificados."""
    texto, html = "", ""
    for parte in msg.walk() if msg.is_multipart() else [msg]:
        tipo = parte.get_content_type()
        if tipo not in ("text/plain", "text/html"):
            continue
        try:
            corpo = parte.get_payload(decode=True) or b""
            conteudo = corpo.decode(parte.get_content_charset() or "utf-8", "replace")
        except Exception:  # noqa: BLE001
            continue
        if tipo == "text/plain":
            texto += conteudo
        else:
            html += conteudo
    return texto, html


def _data_do_email(msg: Message) -> date | None:
    bruto = msg.get("Date")
    if not bruto:
        return None
    try:
        return email.utils.parsedate_to_datetime(bruto).date()
    except Exception:  # noqa: BLE001
        return None


def parse_email(bruto: bytes) -> list[Job]:
    """Um e-mail de alerta → as vagas dentro dele. Função pura.

    Duas camadas, nesta ordem, porque a primeira é mais limpa:

    1. A parte `text/plain` do e-mail. Vem sem CSS, sem pixel de
       rastreio e com as URLs menos ofuscadas.
    2. As âncoras do HTML, que é de onde sai o TÍTULO da vaga — o
       texto puro raramente separa título de resto.
    """
    from bs4 import BeautifulSoup

    msg = email.message_from_bytes(bruto)
    texto, html = _partes(msg)
    quando = _data_do_email(msg)
    remetente = (msg.get("From") or "").strip()

    #: id → título, preenchido pelo HTML e consultado no fim.
    titulos: dict[tuple[str, str], str] = {}
    achados: dict[tuple[str, str], str] = {}   # (plataforma, id) → url canônica

    def registrar(url_bruta: str, titulo: str = "") -> None:
        alvo = identificar(desembrulhar(url_bruta)) or identificar(url_bruta)
        if not alvo:
            return
        plataforma, ident, canonica = alvo
        chave = (plataforma, ident)
        achados[chave] = canonica
        titulo = " ".join(titulo.split())
        if titulo and not RUIDO.match(titulo) and len(titulo) > 3:
            # O primeiro título decente ganha: nos alertas o link do
            # título vem antes do "Candidatar-se" da mesma vaga.
            titulos.setdefault(chave, titulo[:200])

    for url in RE_URL.findall(texto):
        registrar(url)

    if html:
        sopa = BeautifulSoup(html, "html.parser")
        for ancora in sopa.find_all("a", href=True):
            registrar(str(ancora["href"]), ancora.get_text(" ", strip=True))

    vagas: list[Job] = []
    for (plataforma, ident), canonica in achados.items():
        titulo = titulos.get((plataforma, ident), "")
        if not titulo:
            # Sem título não dá para pontuar nem para deduplicar por
            # conteúdo. Guardar isso poluiria a fila com linhas vazias.
            continue
        vagas.append(Job(
            source=f"email:{plataforma}",
            source_id=ident,
            title=titulo,
            url=canonica,
            employer=None,
            description="",
            suburb=None,
            state="SA",
            employment_type=EmploymentType.UNKNOWN,
            posted_at=quando,
            legitimacy=Legitimacy.OWN_DATA,
            raw={"alerta_de": remetente, "plataforma": plataforma},
        ))
    return vagas


@register
class EmailAlertsCollector(BaseCollector):
    """Lê uma pasta IMAP e extrai as vagas dos alertas que estão lá."""

    name = "email_alerts"
    legitimacy = Legitimacy.OWN_DATA
    min_interval = 0.0        # é a sua própria caixa; não há quem incomodar

    def collect(self) -> list[Job]:
        host = os.getenv("IMAP_HOST", "imap.gmail.com")
        porta = int(os.getenv("IMAP_PORT", "993"))
        usuario = os.getenv("IMAP_USER", "")
        senha = os.getenv("IMAP_PASSWORD", "")
        pasta = os.getenv("IMAP_FOLDER", "") or self.config.get("folder", "INBOX")

        if not usuario or not senha:
            raise CollectorError(
                "IMAP_USER e IMAP_PASSWORD vazios no .env. Veja o passo a "
                "passo em docs/FONTES.md — no Gmail é 'senha de app', não a "
                "senha da conta."
            )

        dias = int(self.config.get("since_days", 3))
        desde = (datetime.now() - timedelta(days=dias)).strftime("%d-%b-%Y")
        remetentes: list[str] = self.config.get("senders") or []
        vagas: list[Job] = []

        try:
            caixa = imaplib.IMAP4_SSL(host, porta)
        except Exception as exc:  # noqa: BLE001
            raise CollectorError(f"não conectou em {host}:{porta} — {exc}") from exc

        try:
            try:
                caixa.login(usuario, senha)
            except imaplib.IMAP4.error as exc:
                raise CollectorError(
                    f"login recusado para {usuario}. No Gmail isto quase sempre "
                    f"é senha de app faltando ou verificação em duas etapas "
                    f"desligada. Erro do servidor: {exc}"
                ) from exc

            ok, _ = caixa.select(f'"{pasta}"', readonly=True)
            if ok != "OK":
                raise CollectorError(
                    f"pasta {pasta!r} não existe na caixa. No Gmail, um rótulo "
                    f"aninhado vira pasta com barra: 'Vagas/SEEK'."
                )

            uids = self._procurar(caixa, desde, remetentes)
            self.note_info(f"{len(uids)} e-mail(s) desde {desde} em {pasta!r}")

            for uid in uids:
                ok, dados = caixa.fetch(uid, "(RFC822)")
                if ok != "OK" or not dados or not isinstance(dados[0], tuple):
                    self.note_error(f"não li o e-mail {uid.decode()}")
                    continue
                try:
                    achadas = parse_email(dados[0][1])
                except Exception as exc:  # noqa: BLE001
                    # Um e-mail estranho não pode derrubar os outros 40.
                    self.note_error(f"e-mail {uid.decode()}: {type(exc).__name__}: {exc}")
                    continue
                if not achadas:
                    # Sinal de que um template mudou. Vale saber.
                    self.note_error(
                        f"e-mail {uid.decode()} não rendeu nenhuma vaga "
                        "— o layout do remetente pode ter mudado"
                    )
                vagas.extend(achadas)
        finally:
            try:
                caixa.logout()
            except Exception:  # noqa: BLE001
                pass

        return vagas

    def _procurar(self, caixa: Any, desde: str, remetentes: list[str]) -> list[bytes]:
        """UIDs a buscar. Um SEARCH por remetente, porque OR do IMAP é
        aninhado e ilegível a partir de três termos."""
        uids: list[bytes] = []
        vistos: set[bytes] = set()
        criterios = (
            [["SINCE", desde, "FROM", r] for r in remetentes]
            if remetentes else [["SINCE", desde]]
        )
        for criterio in criterios:
            ok, resposta = caixa.search(None, *criterio)
            if ok != "OK":
                continue
            for uid in resposta[0].split():
                if uid not in vistos:
                    vistos.add(uid)
                    uids.append(uid)
        return uids

    def note_info(self, msg: str) -> None:
        import logging
        logging.getLogger(__name__).info("[%s] %s", self.name, msg)
