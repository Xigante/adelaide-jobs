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


# ── a mensagem quando o login é recusado ────────────────────────────
#
# Aconteceu em 09/09: senha de app certa, verificação em duas etapas
# ligada, e mesmo assim recusado — porque a senha DA CONTA tinha sido
# trocada no dia anterior. A mensagem antiga mandava conferir as duas
# coisas que já estavam certas, e não citava a única que importava.

def _colector():
    from adelaide_jobs.collectors.email_alerts import EmailAlertsCollector
    return EmailAlertsCollector


def test_formato_errado_diz_que_nao_e_senha_de_app():
    txt = _colector()._porque_recusou("a@gmail.com", "minha-senha-1", "E")
    assert "não é uma senha de app" in txt
    assert "13 caractere" in txt
    assert "CONFIGURAR-EMAIL.bat" in txt


def test_formato_certo_acusa_a_troca_de_senha_da_conta():
    txt = _colector()._porque_recusou("a@gmail.com", "abcdefghijklmnop", "E")
    assert "TROCOU A SENHA DA CONTA" in txt
    assert "revoga" in txt
    assert "não é erro de digitação" in txt


def test_a_senha_nunca_aparece_na_mensagem():
    """A mensagem vai para a tela e vira print no chat."""
    for senha in ("abcdefghijklmnop", "minha-senha-secreta"):
        txt = _colector()._porque_recusou("a@gmail.com", senha, "E")
        assert senha not in txt


def test_senha_vazia_nao_quebra():
    txt = _colector()._porque_recusou("a@gmail.com", "", "E")
    assert "0 caractere" in txt


# ── SEEK: o formato de link sem id ──────────────────────────────────
#
# Achado em 09/09 abrindo a caixa de alertas: o SEEK trocou
#     click.seek.com.au/f/a/…/h/https%3A%2F%2F…%2Fjob%2F842…
# por
#     email.s.seek.com.au/uni/ss/c/<91>/4tv/<22>/h0/<48>
# que não tem id nenhum dentro. Eram 10 alertas com ~179 vagas paradas
# na caixa, e o leitor extraía zero. A vaga passa a sair do TEXTO da
# âncora, que continua trazendo título, empregador, local e salário.

def _email_seek(corpo_html: str) -> bytes:
    return (
        "From: SEEK Job Alerts <jobmail@s.seek.com.au>\r\n"
        "Subject: 18 new jobs for Data Analyst in Adelaide SA 5000\r\n"
        "Date: Tue, 8 Sep 2026 21:54:00 +0930\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/html; charset=utf-8\r\n\r\n" + corpo_html
    ).encode()


def _ancora(destino: str, *linhas: str) -> str:
    blocos = "".join(f"<div>{l}</div>" for l in linhas)
    return f'<a href="https://email.s.seek.com.au/uni/ss/c/{destino}/4tv/x/h0/y">{blocos}</a>'


def test_formato_novo_do_seek_vira_vaga():
    from adelaide_jobs.collectors.email_alerts import parse_email
    html = "<html><body>" + _ancora(
        "AAA", "Applications and Data Analyst",
        "St Andrew&#39;s Hospital Inc", "Adelaide SA") + "</body></html>"
    vagas = parse_email(_email_seek(html))
    assert len(vagas) == 1
    v = vagas[0]
    assert v.source == "email:seek"
    assert v.title == "Applications and Data Analyst"
    assert v.employer == "St Andrew's Hospital Inc"
    assert v.suburb == "Adelaide SA"
    assert v.state == "SA"
    assert "email.s.seek.com.au" in v.url


def test_salario_entra_como_descricao():
    """É a única pista de dinheiro que o alerta traz."""
    from adelaide_jobs.collectors.email_alerts import parse_email
    html = "<html><body>" + _ancora(
        "BBB", "Inventory Analyst", "SA Power Networks",
        "Adelaide SA", "$141,234.95") + "</body></html>"
    v = parse_email(_email_seek(html))[0]
    assert v.description == "$141,234.95"


def test_ordem_dos_campos_extras_nao_importa():
    """Salário antes do local, que é como alguns anúncios vêm."""
    from adelaide_jobs.collectors.email_alerts import parse_email
    html = "<html><body>" + _ancora(
        "CCC", "Senior Cost Controller", "Enerven",
        "13% super + Flexi-time accrual", "Keswick, Adelaide SA") + "</body></html>"
    v = parse_email(_email_seek(html))[0]
    assert v.suburb == "Keswick, Adelaide SA"
    assert "super" in (v.description or "")


def test_botoes_e_rodape_nao_viram_vaga():
    from adelaide_jobs.collectors.email_alerts import parse_email
    html = ("<html><body>"
            + _ancora("DDD", "Apply now")
            + _ancora("EEE", "See all jobs")
            + '<a href="https://www.seek.com.au/my-activity">Unsubscribe</a>'
            + "</body></html>")
    assert parse_email(_email_seek(html)) == []


def test_a_mesma_vaga_duas_vezes_no_email_vira_uma():
    """O título e o botão da mesma vaga apontam para links diferentes."""
    from adelaide_jobs.collectors.email_alerts import parse_email
    linha = ("Data Engineer", "People First Bank", "Adelaide SA")
    html = ("<html><body>" + _ancora("FFF", *linha)
            + _ancora("GGG", *linha) + "</body></html>")
    assert len(parse_email(_email_seek(html))) == 1


def test_o_id_e_o_mesmo_em_coletas_diferentes():
    """Senão cada rodada cria a vaga de novo e a fila enche de repetido."""
    from adelaide_jobs.collectors.email_alerts import parse_email
    linha = ("Business Analyst", "Emanate Technology Pty Ltd", "Adelaide SA")
    a = parse_email(_email_seek("<html><body>" + _ancora("H1", *linha) + "</body></html>"))
    b = parse_email(_email_seek("<html><body>" + _ancora("H2", *linha) + "</body></html>"))
    assert a[0].source_id == b[0].source_id


def test_o_formato_antigo_continua_funcionando():
    """Não é troca, é acréscimo: o Jora e o resto usam o caminho velho."""
    from adelaide_jobs.collectors.email_alerts import parse_email
    html = ('<html><body><a href="https://au.jora.com/job/'
            'cleaner-abc123def4567890">Commercial Cleaner</a></body></html>')
    vagas = parse_email(_email_seek(html))
    assert len(vagas) == 1
    assert vagas[0].source == "email:jora"
