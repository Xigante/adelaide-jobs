"""Arruma a pasta australia. Move, nunca apaga.

Eram 47 arquivos soltos na mesma pasta: tradução juramentada de
extrato bancário ao lado de .bat, cinco versões do mesmo documento da
escola, e o material do projeto misturado com coisa que o repositório
já substituiu.

REGRAS
  1. Nada é apagado. Tudo é movido, e mover se desfaz.
  2. Ficam na raiz só o que você usa: os dois .bat e a pasta do projeto.
     Os .bat têm que ficar — é para eles que o atalho da sua área de
     trabalho aponta.
  3. Nenhum arquivo é escolhido por você. As cinco versões do GS vão
     todas para a mesma pasta; qual é a boa, quem sabe é você.
  4. Se aparecer um arquivo que não está previsto aqui, o script PARA e
     mostra. Prefiro não adivinhar onde guardar documento seu.

RODAR
    python arrumar-pasta.py
"""
import pathlib
import shutil
import sys

AQUI = pathlib.Path(__file__).resolve().parent

FICA_NA_RAIZ = {
    "ATUALIZAR-VAGAS.bat",      # o atalho da área de trabalho aponta para cá
    "ENVIAR-PARA-GITHUB.bat",
    "arrumar-pasta.py",
    "LEIA-ME.txt",
    "adelaide-jobs",
}

PLANO: dict[str, tuple[str, list[str]]] = {
    "1-visto-e-documentos": (
        "Traduções juramentadas e comprovantes do processo do visto.\n"
        "Documento pessoal e financeiro, seu e de familiares.",
        [
            "CCMEI_Traducao_EN_Pedro_MEI.pdf",
            "CTPS_Traducao_EN_Barbara.pdf",
            "Caixinhas_Nubank_RDB_EN_Pedro.pdf",
            "Caixinhas_Nubank_RDB_PT_Pedro.pdf",
            "Extrato_Bancario_Traducao_EN_Patrocinadora.pdf",
            "Holerite_Traducao_EN_Barbara.pdf",
            "JUCESP_SantosEQueiroz_Traducao_EN.pdf",
            "NFSe_Originais_PT_Pedro_MEI.pdf",
            "NFSe_Traducao_EN_Pedro_MEI.pdf",
            "Nubank_Extratos_Originais_PT_Pedro.pdf",
            "Nubank_Extratos_Traducao_EN_Pedro.pdf",
            "Bloco_Esposa_Sogra.zip",
        ],
    ),
    "2-curriculo": (
        "O currículo em uso e os diplomas traduzidos.",
        [
            "CV_Pedro_Hospitality_Adelaide.docx",
            "CV_Pedro_Hospitality_Adelaide.pdf",
            "Certificado_Alura_Pedro_EN.pdf",
            "Certificado_ESPM_UX_Pedro_EN.pdf",
            "Diploma_Pedro_JogosDigitais_EN.pdf",
        ],
    ),
    "3-escola-ILSC": (
        "O Genuine Student statement, em cinco versões.\n"
        "Não escolhi qual é a boa — só juntei. FINAL e FINAL2 são do\n"
        "mesmo dia (14/06) e têm tamanhos diferentes.",
        [
            "GS_Pedro_ILSC_Adelaide.docx",
            "GS_Pedro_ILSC_Adelaide_v2.docx",
            "GS_Pedro_ILSC_Adelaide_v3.docx",
            "GS_Pedro_ILSC_Adelaide_FINAL.docx",
            "GS_Pedro_ILSC_Adelaide_FINAL2.docx",
        ],
    ),
    "4-pesquisa-de-mercado": (
        "Os levantamentos por setor, de agosto/2026. Foi deles que saiu\n"
        "o Diretório do material. As versões PDF e XLSX do consolidado\n"
        "estão aqui; a versão HTML, que é a viva, mora em\n"
        "adelaide-jobs/material/.",
        [
            "Cafeterias_Adelaide_CBD_Ago2026.pdf",
            "Cafeterias_Adelaide_CBD_Ago2026.xlsx",
            "Cafeterias_Adelaide_CBD_chances.xlsx",
            "Escritorio_Adelaide_Ago2026.pdf",
            "Escritorio_Adelaide_Ago2026.xlsx",
            "Redes_Restaurantes_Adelaide_Ago2026.pdf",
            "Redes_Restaurantes_Adelaide_Ago2026.xlsx",
            "Supermercados_Varejo_Adelaide_Ago2026.pdf",
            "Supermercados_Varejo_Adelaide_Ago2026.xlsx",
            "Trabalho_Adelaide_CONSOLIDADO_Ago2026.pdf",
            "Trabalho_Adelaide_CONSOLIDADO_Ago2026.xlsx",
        ],
    ),
    "5-planejamento": (
        "Custo de vida, cronograma e o manual da mudança.",
        [
            "Planejamento_Adelaide.xlsx",
            "Planilha_Australia_Adelaide.xlsx",
            "Manual_Australia_Adelaide.docx",
            "planejamento-financeiro-adelaide.html",
        ],
    ),
    "6-arquivo": (
        "O que já foi substituído. Nada aqui é usado hoje — está\n"
        "guardado porque explica como o projeto chegou onde chegou.\n\n"
        "  adelaide-jobs.zip        o projeto antes de virar repositório\n"
        "  subir-no-github.ps1      substituído pelo ENVIAR-PARA-GITHUB.bat\n"
        "  COMO-SUBIR.md            idem\n"
        "  Vagas_Adelaide.html      cópia velha do relatório; o de verdade\n"
        "                           é adelaide-jobs/exports/vagas.html\n"
        "  os dois Estudo/Repos     a pesquisa de fontes, hoje em\n"
        "                           adelaide-jobs/docs/FONTES.md",
        [
            "adelaide-jobs.zip",
            "subir-no-github.ps1",
            "COMO-SUBIR.md",
            "Estudo_Pipeline_Vagas_Adelaide_Ago2026.html",
            "Repos_Coleta_Vagas_Adelaide_Ago2026.html",
            "Vagas_Adelaide.html",
            "Vagas_Adelaide_EXEMPLO.html",
            "relatorio-praticas-13ago2026_10.html",
        ],
    ),
}

LEIA_ME = """A PASTA AUSTRALIA
=================

adelaide-jobs\\          O programa. Tudo que roda mora aqui dentro.
                        Comece pelo COMECAR-AQUI.md.

ATUALIZAR-VAGAS.bat     Os dois botões. São atalhos de duas linhas para
ENVIAR-PARA-GITHUB.bat  os arquivos de verdade, em
                        adelaide-jobs\\ferramentas\\.
                        NÃO MOVA E NÃO RENOMEIE ESTES DOIS: é para eles
                        que o atalho da sua área de trabalho aponta.

1-visto-e-documentos\\   Traduções juramentadas e comprovantes.
2-curriculo\\            O CV e os diplomas.
3-escola-ILSC\\          O Genuine Student statement.
4-pesquisa-de-mercado\\  Os levantamentos por setor de agosto/2026.
5-planejamento\\         Custo de vida, cronograma, manual da mudança.
6-arquivo\\              O que já foi substituído. Guardado, não usado.

Cada pasta tem um LEIA-ME.txt dizendo o que é.

Nada foi apagado nesta arrumação — só movido.
"""


def main() -> int:
    previstos = set(FICA_NA_RAIZ)
    for _, arquivos in PLANO.values():
        previstos.update(arquivos)

    presentes = {p.name for p in AQUI.iterdir()}
    surpresas = sorted(presentes - previstos)
    if surpresas:
        print("  [PAREI] Achei arquivo que não está no plano:")
        for s in surpresas:
            print(f"     {s}")
        print()
        print("  Não vou adivinhar onde guardar documento seu. Me diga")
        print("  onde cada um vai, ou acrescente no PLANO deste arquivo.")
        return 1

    movidos = 0
    for pasta, (descricao, arquivos) in PLANO.items():
        destino = AQUI / pasta
        destino.mkdir(exist_ok=True)
        (destino / "LEIA-ME.txt").write_text(
            f"{pasta}\n{'=' * len(pasta)}\n\n{descricao}\n", encoding="utf-8")
        n = 0
        for nome in arquivos:
            origem = AQUI / nome
            if not origem.exists():
                continue
            shutil.move(str(origem), str(destino / nome))
            n += 1
            movidos += 1
        print(f"  {pasta:24s} {n:2d} arquivo(s)")

    (AQUI / "LEIA-ME.txt").write_text(LEIA_ME, encoding="utf-8")
    print()
    print(f"  {movidos} arquivos movidos. Nenhum apagado.")
    print("  A raiz agora tem só: adelaide-jobs, os dois .bat e o LEIA-ME.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
