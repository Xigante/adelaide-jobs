"""O parser do PageUp, contra o HTML real do SA Health.

O fragmento abaixo foi copiado da página em 27/08/2026, não inventado.
Se o SA Health mudar o layout, é este teste que avisa — e não um run
que devolve zero vaga sem explicar por quê.
"""

from adelaide_jobs.collectors.pageup import PageUpCollector, _prazo

from datetime import date

BASE = "https://careers.sahealth.sa.gov.au/caw/en/listing/"

# Estrutura medida: table > tbody > tr > td, âncora com class="job-link".
# Colunas: Position | Job No. | Location | Closes.
HTML = """
<table>
 <thead><tr><th>Position</th><th>Job No.</th><th>Location</th><th>Closes</th></tr></thead>
 <tbody>
  <tr>
   <td><a class="job-link" href="/caw/en/job/937691/emergency-medicine-registrar">
       Emergency Medicine Special Skills Registrar Positions</a></td>
   <td>937691</td><td>Adelaide Metro Southern</td><td>13 Sep</td>
  </tr>
  <tr>
   <td><a class="job-link" href="/caw/en/job/948350/hotel-services-assistant">
       Hotel Services Assistant</a></td>
   <td>948350</td><td>Adelaide CBD</td><td>02 Sep</td>
  </tr>
  <tr>
   <td><a class="job-link" href="/caw/en/job/940762/cleaner-whyalla">Cleaner</a></td>
   <td>940762</td><td>Whyalla</td><td>21 Sep</td>
  </tr>
 </tbody>
</table>
"""


def test_le_as_quatro_colunas():
    vagas = PageUpCollector.parse(HTML, BASE, "SA Health")
    assert len(vagas) == 3
    v = vagas[1]
    assert v.title == "Hotel Services Assistant"
    assert v.suburb == "Adelaide CBD"
    assert v.raw["job_no"] == "948350"
    assert v.raw["closes"] == "02 Sep"
    assert v.state == "SA"


def test_url_vira_absoluta():
    """href relativo no HTML; sem isto o botão Candidatar-se não abre."""
    v = PageUpCollector.parse(HTML, BASE, "SA Health")[0]
    assert v.url == (
        "https://careers.sahealth.sa.gov.au"
        "/caw/en/job/937691/emergency-medicine-registrar"
    )


def test_id_e_o_numero_da_vaga_nao_a_posicao():
    """Dedup entre runs depende disto: a linha muda de lugar, o número não."""
    ids = [v.source_id for v in PageUpCollector.parse(HTML, BASE, "SA Health")]
    assert ids == ["SA Health:937691", "SA Health:948350", "SA Health:940762"]


def test_titulo_multilinha_vira_uma_linha_so():
    """O HTML quebra o título em várias linhas; a tabela não pode herdar isso."""
    v = PageUpCollector.parse(HTML, BASE, "SA Health")[0]
    assert "\n" not in v.title
    assert "  " not in v.title


def test_descricao_vazia_e_intencional():
    """A página de detalhe responde 202 vazio. Fingir que temos texto
    faria o extrator inventar dimensões a partir do nada."""
    assert all(v.description == "" for v in PageUpCollector.parse(HTML, BASE, "SA Health"))


def test_prazo_sem_ano_nao_cai_no_passado():
    """'02 Jan' visto em dezembro é do ano que vem, não deste."""
    assert _prazo("13 Sep", hoje=date(2026, 8, 27)) == date(2026, 9, 13)
    assert _prazo("02 Jan", hoje=date(2026, 12, 20)) == date(2027, 1, 2)
    assert _prazo("", hoje=date(2026, 8, 27)) is None
    assert _prazo("29 Feb", hoje=date(2026, 1, 5)) is None   # 2026 não é bissexto
