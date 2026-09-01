"""As palavras não podem casar dentro de outras palavras.

Medido em 01/09/2026 sobre os 6.895 anúncios reais que estavam no
banco. O extrator juntava os termos num regex sem fronteira, e o
resultado era:

    "unity"  casava em comm(unity)  → 70 vagas de Community Support
             Worker ganhavam bônus de "ponte para trabalho com dados"
    "excel"  casava em (excel)lent  → 633 anúncios, porque "excellent
             communication skills" está em quase todo anúncio daqui
    "mis"    casava em com(mis)sion
    "stock"  casava em "Stockroom Manager"

career_bridge vale 4 pontos e english_load vale 20. Não é ruído: é a
vaga errada no topo da fila.

E a fronteira sozinha estragou outra coisa: fechada com (?!\\w) puro,
"Cleaners and Utility Staff" deixava de casar "cleaner" e caía 18
pontos. Anúncio australiano é escrito no plural o tempo todo. Por isso
o lado direito aceita um "s" opcional.
"""
import pytest
import yaml

from adelaide_jobs.config import CONFIG_DIR
from adelaide_jobs.extract import RuleExtractor


@pytest.fixture(scope="module")
def perfil():
    return yaml.safe_load((CONFIG_DIR / "profile.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("termo,texto", [
    ("unity", "Community Support Worker"),
    ("unity", "Community Engagement Officer"),
    ("excel", "excellent communication skills"),
    ("excel", "a track record of excellence"),
    ("mis", "Commission-based Sales"),
    ("stock", "Stockroom Manager"),
    ("porter", "Transporter Driver"),
    ("picker", "Nitpicker"),
])
def test_nao_casa_dentro_de_outra_palavra(termo, texto):
    assert RuleExtractor._compilar([termo]).search(texto) is None


@pytest.mark.parametrize("termo,texto", [
    ("cleaner", "Cleaners and Utility Staff - North Adelaide CBD"),
    ("cleaner", "End-of-Lease Cleaner – Casual"),
    ("yard hand", "Yard Hands wanted"),
    ("storeperson", "Storepersons - night shift"),
    ("porter", "Porter/Valet - Part time"),
    ("packer", "Pick Packer"),
    ("picker", "Picker/Packer"),
    ("steward", "Kitchen Steward"),
    ("commis", "Commis Chef"),
    ("excel", "advanced Excel and Word"),
    ("housekeeper", "Cleaners & Housekeepers | Adelaide"),
])
def test_casa_a_palavra_e_o_plural(termo, texto):
    assert RuleExtractor._compilar([termo]).search(texto) is not None


def test_listas_do_perfil_nao_tem_repetido(perfil):
    for nome in ("boh_keywords", "career_keywords"):
        lista = perfil[nome]
        repetidos = {t for t in lista if lista.count(t) > 1}
        assert not repetidos, f"{nome} tem repetido: {sorted(repetidos)}"


def test_termos_britanicos_ficaram_fora(perfil):
    """Não aparecem uma vez em 6.895 anúncios de Adelaide."""
    for morto in ("pot wash", "glass collector", "shelf stacker",
                  "kitchen porter", "houseperson", "linen attendant",
                  "dishy", "night filler"):
        assert morto not in perfil["boh_keywords"], morto


def test_cargos_de_escritorio_de_adelaide_estao_na_ponte(perfil):
    """São os que Adelaide anuncia e que ele achava por acidente."""
    for vivo in ("receptionist", "administration officer", "accounts payable",
                 "payroll officer", "customer service officer", "data entry"):
        assert vivo in perfil["career_keywords"], vivo


def test_frente_de_loja_nao_conta_como_ingles_minimo(perfil):
    """Com A2, balcão é barreira de verdade. Marcar como BOH seria mentir."""
    for cliente in ("barista", "sales assistant", "team member",
                    "food and beverage attendant", "crew member"):
        assert cliente not in perfil["boh_keywords"], cliente
