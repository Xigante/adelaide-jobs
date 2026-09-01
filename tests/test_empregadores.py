"""O cadastro de empregadores.

A vaga é volátil — sai do ar em duas semanas. A empresa não: ela
continua existindo e continua contratando o mesmo tipo de gente. Esta
tabela é a lista de portas em que vale a pena bater com currículo na
mão, e a regra que ela tem que cumprir é uma só: nunca perder um nome.
"""
import json

from adelaide_jobs import export
from adelaide_jobs.dedup import canon_employer
from adelaide_jobs.models import Job, Legitimacy


def vaga(titulo: str, empresa: str, bairro: str = "Adelaide",
         ident: str = "1") -> Job:
    return Job(source="adzuna", source_id=ident, title=titulo,
               employer=empresa, suburb=bairro, postcode="5000",
               url=f"https://x/{ident}", description="",
               legitimacy=Legitimacy.PUBLIC_ENDPOINT)


def test_registra_a_empresa_e_o_que_ela_pede(db):
    j = vaga("Warehouse Handler", "FedEx")
    db.upsert_employer(j, canon_employer(j.employer), novo_cluster=True)
    db.upsert_employer(vaga("Casual Cleaner", "FedEx", ident="2"),
                       canon_employer("FedEx"), novo_cluster=True)
    (e,) = db.empregadores()
    assert e["employer"] == "FedEx"
    assert e["total_vagas"] == 2
    assert set(json.loads(e["cargos"])) == {"Warehouse Handler", "Casual Cleaner"}


def test_a_mesma_vaga_vista_de_novo_nao_conta_duas(db):
    j = vaga("Warehouse Handler", "FedEx")
    db.upsert_employer(j, canon_employer(j.employer), novo_cluster=True)
    db.upsert_employer(j, canon_employer(j.employer), novo_cluster=False)
    (e,) = db.empregadores()
    assert e["total_vagas"] == 1


def test_empresa_sem_vaga_no_ar_continua_no_cadastro(db):
    """O ponto inteiro da tabela. Se isto quebrar, o cadastro é inútil."""
    j = vaga("Casual Cleaner", "Empresa Que Sumiu")
    db.upsert_employer(j, canon_employer(j.employer), novo_cluster=True)
    db.conn.execute("DELETE FROM job_cluster")     # anúncio saiu do ar
    db.conn.commit()
    db.rebuild_employers()                          # o rebuild é MERGE
    nomes = [e["employer"] for e in db.empregadores()]
    assert "Empresa Que Sumiu" in nomes


def test_rebuild_reconstroi_a_partir_dos_clusters(db):
    db.upsert_cluster("c1", {"employer": "Drakes", "employer_canon": "drakes",
                             "title": "Casual Store Assistant",
                             "suburb": "Prospect", "url": "https://d/1",
                             "source": "adzuna"})
    db.conn.commit()
    assert db.rebuild_employers() == 1
    (e,) = db.empregadores()
    assert e["employer"] == "Drakes"
    assert json.loads(e["suburbs"]) == {"Prospect": 1}


def test_setor_sai_dos_cargos():
    """Um rótulo só mentiria. A função devolve até dois, e isso é o ponto:
    um hospital que também anuncia administrativo é as duas coisas, e
    tem que aparecer nos dois filtros."""
    hospital = {"Registered Nurse": 3, "Clinical Coordinator": 2,
                "Administrative Support Officer": 4, "Admin Assistant": 2}
    assert set(export._setores(hospital)) == {"saúde", "escritório"}

    # Quando não há ambiguidade, o primeiro tem que ser o óbvio.
    assert _primeiro({"Casual Cleaner": 5, "Hospital Cleaners": 2}) == "limpeza"
    assert _primeiro({"Data Analyst": 2, "Power BI Developer": 1}) == "dados"
    assert _primeiro({"Forklift Operator": 1, "Pick Packer": 3}) == "armazém"
    assert _primeiro({"Zookeeper": 1}) == "outros"


def _primeiro(cargos):
    return export._setores(cargos)[0]


def test_json_do_material_e_compacto_e_sem_caractere_invisivel(db, tmp_path):
    db.upsert_employer(vaga("Livreiro", "﻿Dymocks Australia"),
                       "dymocks", novo_cluster=True)
    caminho = export.empregadores_to_json(db, tmp_path / "e.json")
    d = json.loads(caminho.read_text(encoding="utf-8"))
    (e,) = d["empresas"]
    assert e["n"] == "Dymocks Australia"        # BOM removido
    assert "nome" not in e                       # chaves curtas, é de propósito
    assert d["total"] == 1


def test_csv_traz_tudo_por_extenso(db, tmp_path):
    db.upsert_employer(vaga("Casual Cleaner", "ISS"), "iss", novo_cluster=True)
    caminho = export.empregadores_to_csv(db, tmp_path / "e.csv")
    texto = caminho.read_text(encoding="utf-8-sig")
    assert "nome,vagas,setor" in texto
    assert "ISS" in texto and "Casual Cleaner" in texto
