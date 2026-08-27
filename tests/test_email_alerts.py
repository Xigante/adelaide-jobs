"""O parser de alertas de e-mail.

O jeito de quebrar isto é o layout do remetente mudar, então os
fixtures aqui imitam a forma REAL dos alertas: link de rastreio por
fora, id da vaga por dentro, e um monte de âncora de rodapé que não é
vaga nenhuma.
"""

from email.message import EmailMessage

import pytest

from adelaide_jobs.collectors.email_alerts import (
    desembrulhar, identificar, parse_email,
)


def montar(assunto: str, remetente: str, html: str, texto: str = "") -> bytes:
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = "vagas.adelaide@example.com"
    msg["Date"] = "Wed, 26 Aug 2026 22:05:11 +0930"
    msg.set_content(texto or "Veja as vagas no navegador.")
    msg.add_alternative(html, subtype="html")
    return msg.as_bytes()


# ── SEEK ────────────────────────────────────────────────────────────

SEEK_HTML = """
<html><body>
<table>
 <tr><td><a href="https://click.seek.com.au/f/a/xyz/AAQ/abc/h/https%3A%2F%2Fwww.seek.com.au%2Fjob%2F84213977">
   Kitchen Hand - Casual</a></td></tr>
 <tr><td>Fasta Pasta &middot; Adelaide SA</td></tr>
 <tr><td><a href="https://click.seek.com.au/f/a/xyz/AAQ/abc/h/https%3A%2F%2Fwww.seek.com.au%2Fjob%2F84213977">
   Candidatar-se</a></td></tr>

 <tr><td><a href="https://www.seek.com.au/job/84300112?type=standout">
   Housekeeping Room Attendant</a></td></tr>

 <tr><td><a href="https://www.seek.com.au/my-activity/saved-searches">Ver todas as vagas</a></td></tr>
 <tr><td><a href="https://www.seek.com.au/unsubscribe?token=zzz">Descadastrar</a></td></tr>
</body></html>
"""


def test_seek_acha_as_vagas_e_ignora_o_rodape():
    vagas = parse_email(montar("2 novas vagas", "jobmail@seek.com.au", SEEK_HTML))
    ids = sorted(v.source_id for v in vagas)
    assert ids == ["84213977", "84300112"]


def test_seek_desembrulha_o_rastreador_sem_seguir_redirect():
    """O link do e-mail é click.seek.com.au. O que vai para o banco tem
    que ser a URL limpa — senão o botão Candidatar-se some quando o
    rastreador expira."""
    vagas = parse_email(montar("x", "jobmail@seek.com.au", SEEK_HTML))
    kh = next(v for v in vagas if v.source_id == "84213977")
    assert kh.url == "https://www.seek.com.au/job/84213977"
    assert "click.seek" not in kh.url


def test_seek_pega_o_titulo_e_nao_o_botao():
    """A mesma vaga aparece duas vezes: no título e no 'Candidatar-se'.
    O título tem que ganhar."""
    vagas = parse_email(montar("x", "jobmail@seek.com.au", SEEK_HTML))
    kh = next(v for v in vagas if v.source_id == "84213977")
    assert kh.title == "Kitchen Hand - Casual"


def test_seek_query_string_nao_vira_id_diferente():
    """?type=standout no link não pode criar uma vaga duplicada."""
    vagas = parse_email(montar("x", "jobmail@seek.com.au", SEEK_HTML))
    assert len([v for v in vagas if v.source_id == "84300112"]) == 1


# ── LinkedIn ────────────────────────────────────────────────────────

LINKEDIN_HTML = """
<html><body>
<a href="https://www.linkedin.com/comm/jobs/view/4102938471?midToken=AQF&amp;trk=eml-jymbii-organic-job-card">
  Storeperson / Warehouse Assistant</a>
<p>Drakes Supermarkets &middot; Adelaide, South Australia</p>
<a href="https://www.linkedin.com/comm/jobs/search?keywords=x&amp;trk=eml-footer">See all jobs</a>
<a href="https://www.linkedin.com/psettings/email">Settings</a>
</body></html>
"""


def test_linkedin_id_vem_do_path_apesar_do_midtoken():
    vagas = parse_email(montar("Vagas para você", "jobs-noreply@linkedin.com", LINKEDIN_HTML))
    assert len(vagas) == 1
    v = vagas[0]
    assert v.source_id == "4102938471"
    assert v.url == "https://www.linkedin.com/jobs/view/4102938471"
    assert v.title == "Storeperson / Warehouse Assistant"


def test_linkedin_busca_salva_nao_conta_como_vaga():
    """/jobs/search e /jobs/view/ moram no mesmo domínio. Só o segundo é vaga."""
    vagas = parse_email(montar("x", "jobs-noreply@linkedin.com", LINKEDIN_HTML))
    assert all("search" not in v.url for v in vagas)


# ── Indeed ──────────────────────────────────────────────────────────

INDEED_HTML = """
<html><body>
<a href="https://au.indeed.com/rc/clk?jk=744c7ca9fec5fde8&amp;bb=zz&amp;xkcb=yy">Cleaner - Night Shift</a>
<a href="https://au.indeed.com/pagead/clk?mo=r&amp;jk=1a2b3c4d5e6f7a8b&amp;ad=long">Nightfill Team Member</a>
</body></html>
"""


def test_indeed_id_vem_do_parametro_jk():
    vagas = parse_email(montar("x", "alert@indeed.com", INDEED_HTML))
    assert sorted(v.source_id for v in vagas) == ["1a2b3c4d5e6f7a8b", "744c7ca9fec5fde8"]
    assert all(v.url.startswith("https://au.indeed.com/viewjob?jk=") for v in vagas)


# ── Robustez ────────────────────────────────────────────────────────

def test_email_sem_vaga_nenhuma_devolve_lista_vazia():
    html = '<html><body><a href="https://example.com/promo">Promoção</a></body></html>'
    assert parse_email(montar("Novidades", "marketing@exemplo.com", html)) == []


def test_email_so_com_texto_puro_ainda_acha_o_link():
    """Nem todo alerta manda HTML. Mas sem título a vaga não entra —
    pontuar sem título produziria linha vazia na fila."""
    msg = EmailMessage()
    msg["Subject"] = "alerta"
    msg["From"] = "jobmail@seek.com.au"
    msg["Date"] = "Wed, 26 Aug 2026 22:05:11 +0930"
    msg.set_content("Kitchen Hand\nhttps://www.seek.com.au/job/999888\n")
    assert parse_email(msg.as_bytes()) == []


def test_data_do_email_vira_data_da_vaga():
    from datetime import date
    vagas = parse_email(montar("x", "jobmail@seek.com.au", SEEK_HTML))
    assert all(v.posted_at == date(2026, 8, 26) for v in vagas)


def test_a_fonte_diz_de_qual_plataforma_veio():
    """`email:seek` e `email:linkedin` são fontes distintas: a ordem de
    preferência de link no relatório depende disso."""
    seek = parse_email(montar("x", "jobmail@seek.com.au", SEEK_HTML))
    li = parse_email(montar("x", "jobs-noreply@linkedin.com", LINKEDIN_HTML))
    assert {v.source for v in seek} == {"email:seek"}
    assert {v.source for v in li} == {"email:linkedin"}
    assert all(v.legitimacy.value == "own_data" for v in seek + li)


@pytest.mark.parametrize("url,esperado", [
    ("https://t.exemplo.com/c/aHR0cHM6Ly93d3cuc2Vlay5jb20uYXUvam9iLzEyMzQ1",
     "https://www.seek.com.au/job/12345"),
    ("https://track.exemplo.com/r?url=https%3A%2F%2Fwww.seek.com.au%2Fjob%2F777",
     "https://www.seek.com.au/job/777"),
    ("https://www.seek.com.au/job/555", "https://www.seek.com.au/job/555"),
])
def test_desembrulhar_base64_e_query_string(url, esperado):
    assert desembrulhar(url) == esperado


def test_desembrulhar_nao_estraga_url_normal():
    """Segmento longo que não é base64 de URL tem que passar intacto."""
    u = "https://www.seek.com.au/kitchen-hand-jobs/in-All-Adelaide-SA"
    assert desembrulhar(u) == u


def test_identificar_devolve_none_para_link_que_nao_e_vaga():
    assert identificar("https://www.seek.com.au/career-advice/article/x") is None
    assert identificar("https://www.linkedin.com/feed/") is None
