"""Azeita as nomenclaturas: fronteira de palavra + listas medidas no real.

TRÊS ERROS ENCONTRADOS, todos medidos em 01/09/2026 sobre os 6.895
anúncios reais de Adelaide que já estão no banco.

ERRO 1 — OS TERMOS CASAVAM DENTRO DE OUTRAS PALAVRAS.
    O extrator junta os termos num regex só, sem fronteira de palavra.
    Consequência, contada:

      "unity"  casa dentro de comm(unity)  → 70 vagas de Community
               Support Worker ganharam bônus de "ponte para dados"
      "excel"  casa dentro de (excel)lent  → 633 anúncios, porque
               "excellent communication skills" está em quase todo
               anúncio australiano
      "mis"    casa dentro de com(mis)sion, per(mis)são, ...
      "stock"  casa em "Stockroom Manager", "Stock Supervisor"

    Isso não é ruído: career_bridge vale 4 pontos e english_load vale
    20. Uma vaga de apoio comunitário estava sendo pontuada como se
    fosse ponte para trabalho com dados.

ERRO 2 — METADE DAS PALAVRAS NÃO EXISTE NA AUSTRÁLIA.
    13 dos 49 boh_keywords e 35 dos 80 career_keywords não aparecem
    UMA VEZ em 6.895 títulos nem em 8.361 descrições. São britânicas
    ("pot wash", "glass collector", "shelf stacker", "kitchen porter")
    ou de um perfil que Adelaide não anuncia ("figma", "unreal",
    "looker", "qlik", "dax", "power query").

ERRO 3 — career_keywords TINHA 12 ENTRADAS REPETIDAS.
    A lista foi editada duas vezes e as duas versões ficaram grudadas.

E O QUE FALTAVA: os cargos de escritório que Adelaide realmente
anuncia — receptionist (118), administration officer (65), customer
service officer (38), administration assistant (28), accounts payable
(25), payroll officer (24) — não estavam em lista nenhuma. Ele achava
essas vagas por acidente, pela varredura de categoria, e elas não
ganhavam o bônus de ponte de carreira que merecem.

Todo termo que entra aqui foi contado no corpus antes. O número entre
parênteses é quantos títulos reais o contêm.

RODAR
    python nomenclatura.py
"""
import pathlib
import re
import shutil

AQUI = pathlib.Path(__file__).resolve().parent
PROJ = AQUI / "adelaide-jobs"
PROFILE = PROJ / "config" / "profile.yaml"
SOURCES = PROJ / "config" / "sources.yaml"
EXTRACT = PROJ / "src" / "adelaide_jobs" / "extract.py"


def troca(s: str, velho: str, novo: str, rotulo: str) -> str:
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    return s.replace(velho, novo, 1)


# ══════════════════════════════════════════════════════════════════════
# 1. extract.py — fronteira de palavra
# ══════════════════════════════════════════════════════════════════════
COMPILAR_VELHO = '''    @staticmethod
    def _compilar(termos: list[str] | None) -> re.Pattern[str] | None:
        if not termos:
            return None
        return re.compile("|".join(re.escape(t) for t in termos), re.I)'''

COMPILAR_NOVO = '''    @staticmethod
    def _compilar(termos: list[str] | None) -> re.Pattern[str] | None:
        """Junta os termos num regex só, com FRONTEIRA DE PALAVRA.

        A fronteira não é detalhe de estilo. Sem ela, medido em
        01/09/2026 sobre 6.895 anúncios reais de Adelaide:

            "unity"  casava dentro de comm(unity)  → 70 vagas de
                     Community Support Worker ganhavam o bônus de
                     "ponte para trabalho com dados"
            "excel"  casava dentro de (excel)lent → 633 anúncios,
                     porque "excellent communication skills" está em
                     quase todo anúncio australiano
            "mis"    casava dentro de com(mis)sion
            "stock"  casava em "Stockroom Manager"

        career_bridge vale 4 pontos e english_load vale 20. Um erro
        destes não é ruído: é a vaga errada no topo da fila.

        (?<!\\w) e (?!\\w) em vez de \\b porque há termos com "&" e "/"
        nas pontas, e \\b se comporta de outro jeito ao lado deles.
        """
        if not termos:
            return None
        partes = []
        for t in termos:
            t = str(t)
            if not t:
                continue
            esq = r"(?<!\\w)" if t[0].isalnum() else ""
            dir_ = r"(?!\\w)" if t[-1].isalnum() else ""
            partes.append(esq + re.escape(t) + dir_)
        if not partes:
            return None
        return re.compile("|".join(partes), re.I)'''


# ══════════════════════════════════════════════════════════════════════
# 2. profile.yaml — as duas listas, refeitas
# ══════════════════════════════════════════════════════════════════════
CAREER = """# Termos que fazem a vaga contar como "ponte de carreira" — trabalho
# de escritório e de dados, que é a formação dele.
#
# TODA palavra desta lista foi contada nos 6.895 anúncios reais de
# Adelaide antes de entrar. O número é quantos títulos a contêm.
# As 35 que não apareciam nenhuma vez saíram, e as 12 repetidas também.
#
# Sobre games: a lista antiga tinha 12 termos de jogos e design
# (unreal, figma, ux designer, liveops, qa tester...). Nenhum aparece
# em Adelaide. A pesquisa em docs/FONTES.md achou UMA vaga de games na
# cidade inteira. Ficaram só dois, para o caso de aparecer.
career_keywords:
  # ── O que Adelaide de fato anuncia como cargo de escritório ────────
  # Isto é a ponte de verdade: emprego de escritório, experiência local.
  - receptionist              # 118 títulos
  - administration officer    # 65
  - customer service officer  # 38
  - administration assistant  # 28
  - accounts payable          # 25
  - payroll officer           # 24
  - finance officer           # 17
  - rostering                 # 15
  - business support          # 14
  - project officer           # 13
  - administrative officer    # 12
  - office administrator      # 12
  - scheduling                # 11
  - accounts receivable       # 10
  - data entry                # 8
  - admin assistant           # 7
  - admin officer             # 5
  - office assistant          # 5
  - records officer           # 5
  - records management        # só na descrição
  - claims officer            # 1
  - data officer              # 2
  - data capture              # 1

  # ── Análise de dados ───────────────────────────────────────────────
  - business analyst          # 20
  - data analyst              # 17
  - reporting                 # 16 no título, 375 nas descrições
  - analytics                 # 12
  - business intelligence     # 7
  - sap                       # 6
  - insights                  # 4
  - workday                   # 4
  - automation                # 4
  - salesforce                # 3
  - python                    # 3
  - data analytics            # 2
  - data governance           # 2
  - power bi                  # 1
  - sql                       # 1
  - excel                     # 0 no título, 17 nas descrições.
                              # Antes casava 633 vezes por causa de
                              # "excellent" — ver extract._compilar
  - spreadsheet               # só na descrição
  - data quality              # só na descrição
  - process improvement       # só na descrição
  - crm                       # só na descrição
  - etl                       # só na descrição
  - tableau                   # só na descrição

  # ── Games e design: Adelaide tem 1 vaga, medida ────────────────────
  - graphic designer          # 4
  - unity                     # 0 no título. Antes casava 70 vezes
                              # dentro de "community"

"""

BOH = """# Termos que marcam a vaga como back-of-house — trabalho em que o
# inglês baixo funciona, porque não há contato com cliente.
#
# ISTO VALE 20 PONTOS. É a segunda dimensão mais pesada do cálculo:
# um título que casa aqui vira english_load = BOH_MINIMAL, cuja
# mediana de nota é 74. Quem não casa nada cai em UNKNOWN, mediana 64.
# Dez pontos de diferença por uma palavra faltando na lista.
#
# Cada termo foi contado nos 6.895 títulos reais antes de entrar.
# Saíram 13 que não aparecem uma única vez em Adelaide — são
# britânicos: pot wash, potwasher, dish hand, dishy, kitchen porter,
# glass collector, glassie, night fill, night filler, shelf stacker,
# houseperson, accommodation cleaner, linen attendant.
#
# Saiu também "stock", que casava em "Stockroom Manager" e "Stock
# Supervisor". E saíram as formas longas que a fronteira de palavra já
# cobre: "pick packer" e "order picker" casam por "picker" e "packer";
# "warehouse operator" casa por "warehouse"; "kitchen steward" casa
# por "steward".
#
# NÃO estão aqui, de propósito: barista, sales assistant, team member,
# food and beverage attendant, crew member. São de frente de loja, e
# com inglês A2 isso é uma barreira de verdade — marcá-los como
# "inglês mínimo" seria mentir para si mesmo. O extrator já os
# classifica como MEDIUM pela regra de contato com cliente.
boh_keywords:
  # ── Cozinha ────────────────────────────────────────────────────────
  - food services assistant   # 18 títulos
  - kitchen hand              # 15
  - commis                    # 12
  - steward                   # 9  (pega "stewarding" não, ver abaixo)
  - stewarding                # 4
  - catering assistant        # 7
  - kitchenhand               # 5
  - food production           # 4
  - kitchen assistant         # 2
  - kitchen attendant         # 2
  - dishwasher                # 1
  - food service assistant    # 1
  - back of house             # 1

  # ── Supermercado ───────────────────────────────────────────────────
  - nightfill                 # 4  (uma palavra só; "night fill" não existe)
  - trolley                   # 3
  - replenishment             # 2
  - grocery                   # 2

  # ── Armazém e fábrica ──────────────────────────────────────────────
  - storeperson               # 82
  - warehouse                 # 81
  - forklift                  # 42
  - packer                    # 20
  - store person              # 13
  - picker                    # 10
  - process worker            # 9
  - yard hand                 # 8
  - production operator       # 7
  - production worker         # 5
  - machine operator          # 5
  - assembler                 # 5
  - factory hand              # 5
  - loader                    # 4
  - dispatch                  # 3
  - freight handler           # 3

  # ── Limpeza e hotel ────────────────────────────────────────────────
  - cleaner                   # 120
  - housekeeping              # 33
  - cleaning                  # 30
  - housekeeper               # 27
  - room attendant            # 7
  - laundry                   # 6
  - support services          # 6  (Support Services Attendant, SA Health)
  - porter                    # 5
  - valet                     # 5
  - hygiene                   # 4
  - public area               # 1
"""


# ══════════════════════════════════════════════════════════════════════
# 3. sources.yaml — fora os termos que não achavam nada
# ══════════════════════════════════════════════════════════════════════
# Cada termo custa 2 requisições por dia das 250 da Adzuna. Estes dez
# custavam 20 por dia e não traziam uma vaga.
MORTOS = ["kitchen porter", "pot wash", "glass collector", "banquet attendant",
          "houseperson", "laundry attendant", "grocery team member",
          "game developer", "ux designer", "dashboard"]


def main() -> None:
    # ── extract.py ──────────────────────────────────────────────────
    s = EXTRACT.read_text(encoding="utf-8")
    if "FRONTEIRA DE PALAVRA" in s:
        print("extract.py: já tem a fronteira")
    else:
        shutil.copy(EXTRACT, EXTRACT.with_suffix(".py.bak"))
        s = troca(s, COMPILAR_VELHO, COMPILAR_NOVO, "_compilar")
        EXTRACT.write_text(s, encoding="utf-8")
        print("extract.py: fronteira de palavra instalada")

    # ── profile.yaml ────────────────────────────────────────────────
    p = PROFILE.read_text(encoding="utf-8")
    shutil.copy(PROFILE, PROFILE.with_suffix(".yaml.bak"))
    i = p.find("# Termos que fazem a vaga contar")
    j = p.find("# Termos que marcam a vaga como back-of-house")
    if i < 0 or j < 0 or j < i:
        raise SystemExit("ÂNCORA NÃO ENCONTRADA: blocos do profile.yaml")
    p = p[:i] + CAREER + BOH
    PROFILE.write_text(p, encoding="utf-8")

    import yaml
    novo = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    ck, bk = novo["career_keywords"], novo["boh_keywords"]
    assert len(ck) == len(set(ck)), "career_keywords ainda tem repetido"
    assert len(bk) == len(set(bk)), "boh_keywords ainda tem repetido"
    print(f"profile.yaml: career_keywords 80 → {len(ck)} · "
          f"boh_keywords 49 → {len(bk)} · nenhum repetido")

    # ── sources.yaml ────────────────────────────────────────────────
    t = SOURCES.read_text(encoding="utf-8")
    shutil.copy(SOURCES, SOURCES.with_suffix(".yaml.bak"))
    fora = 0
    for termo in MORTOS:
        for forma in (f'    - "{termo}"\n', f"    - {termo}\n",
                      f'  - "{termo}"\n', f"  - {termo}\n"):
            if forma in t:
                t = t.replace(forma, "", 1)
                fora += 1
                break
    SOURCES.write_text(t, encoding="utf-8")
    q = yaml.safe_load(t)["adzuna"]["queries"]
    print(f"sources.yaml: {fora} termos mortos removidos · "
          f"{len(q)} termos restantes · libera {fora*2} requisições/dia")
    for termo in MORTOS:
        if termo in q:
            print(f"   [!] não consegui remover {termo!r} — tire à mão")


if __name__ == "__main__":
    main()
