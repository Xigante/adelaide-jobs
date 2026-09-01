"""Os formatos de URL que cada plataforma usa no e-mail de alerta.

Cada caso aqui foi escrito a partir da forma real que o link tem dentro
do e-mail — inclusive os rastreadores, que são o motivo de o
`desembrulhar()` existir:

  SEEK      embrulha em click.email.seek.com.au/?url=<url percent-encoded>
  LinkedIn  usa /comm/jobs/view/<id> no e-mail e /jobs/view/<id> no site
  Indeed    usa /rc/clk?jk=<id> no e-mail e /viewjob?jk=<id> no site

Se um deles mudar de formato, os alertas param de render vaga em
silêncio: o coletor conecta, lê, e devolve zero. Estes testes são o que
transforma esse silêncio em falha visível.
"""
import collections
import email.message
import email.utils

import pytest

from adelaide_jobs.collectors.email_alerts import identificar, parse_email


def alerta(remetente: str, assunto: str, html: str) -> bytes:
    m = email.message.EmailMessage()
    m["From"] = remetente
    m["Subject"] = assunto
    m["Date"] = email.utils.formatdate()
    m.set_content("versao texto")
    m.add_alternative(html, subtype="html")
    return m.as_bytes()


CASOS = [
    ("seek", "jobmail@seek.com.au",
     '<a href="https://www.seek.com.au/job/85412399?type=standout">Kitchen Hand</a>',
     "https://www.seek.com.au/job/85412399"),
    # o mesmo anúncio, embrulhado no rastreador do SEEK
    ("seek", "jobmail@seek.com.au",
     '<a href="https://click.email.seek.com.au/?qs=a&amp;'
     'url=https%3A%2F%2Fwww.seek.com.au%2Fjob%2F85412400">Cleaner</a>',
     "https://www.seek.com.au/job/85412400"),
    ("linkedin", "jobalerts-noreply@linkedin.com",
     '<a href="https://www.linkedin.com/comm/jobs/view/4021998877/?trackingId=x">'
     'Data Entry Officer</a>',
     "https://www.linkedin.com/jobs/view/4021998877"),
    ("indeed", "alert@indeed.com",
     '<a href="https://au.indeed.com/rc/clk?jk=a1b2c3d4e5f60718&amp;from=ja">'
     'Storeperson</a>',
     "https://au.indeed.com/viewjob?jk=a1b2c3d4e5f60718"),
    ("jora", "noreply@jora.com",
     '<a href="https://au.jora.com/job/Casual-Cleaner-4f3a2b1c9d8e7f60?sp=email">'
     'Casual Cleaner</a>',
     "https://au.jora.com/job/x-4f3a2b1c9d8e7f60"),
    ("iworkfor", "noreply@iworkfor.sa.gov.au",
     '<a href="https://www.iworkfor.sa.gov.au/?jobID=889231&amp;src=alert">'
     'ASO2 Administrative Officer</a>',
     "https://www.iworkfor.sa.gov.au/?jobID=889231"),
    ("gumtree", "noreply@gumtree.com.au",
     '<a href="https://www.gumtree.com.au/s-ad/adelaide-cbd/cleaning/'
     'office-cleaner/1327884411">Office Cleaner</a>',
     "https://www.gumtree.com.au/s-ad/1327884411"),
]


@pytest.mark.parametrize("plataforma,remetente,html,url_canonica", CASOS)
def test_extrai_a_vaga_do_alerta(plataforma, remetente, html, url_canonica):
    vagas = parse_email(alerta(remetente, "Job alert", html))
    assert len(vagas) == 1, f"{plataforma}: esperava 1 vaga, veio {len(vagas)}"
    (vaga,) = vagas
    assert vaga.url == url_canonica
    assert vaga.source == f"email:{plataforma}"
    assert vaga.title


def test_ignora_link_que_nao_e_vaga():
    """Todo alerta traz descadastrar, preferências e ver-todas."""
    html = ('<a href="https://www.seek.com.au/my-activity/email-preferences">'
            'Unsubscribe</a>'
            '<a href="https://www.linkedin.com/psettings/email">Settings</a>'
            '<a href="https://www.seek.com.au/jobs?keywords=cleaner">Ver todas</a>')
    assert parse_email(alerta("jobmail@seek.com.au", "alerta", html)) == []


def test_o_mesmo_anuncio_duas_vezes_no_email_vira_uma_vaga():
    """Alerta repete o link no título e no botão. Não são duas vagas."""
    html = ('<a href="https://www.seek.com.au/job/85412399">Kitchen Hand</a>'
            '<a href="https://www.seek.com.au/job/85412399?ref=btn">Ver vaga</a>')
    assert len(parse_email(alerta("jobmail@seek.com.au", "a", html))) == 1


def test_um_email_com_varias_plataformas():
    html = "".join(h for _, _, h, _ in CASOS)
    vagas = parse_email(alerta("x@y.com", "misto", html))
    por_fonte = collections.Counter(v.source for v in vagas)
    assert por_fonte["email:seek"] == 2
    assert set(por_fonte) == {f"email:{p}" for p, _, _, _ in CASOS}


def test_identificar_devolve_none_para_url_qualquer():
    assert identificar("https://www.google.com/search?q=jobs") is None
    assert identificar("https://www.seek.com.au/companies/acme") is None
