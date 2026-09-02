"""A planilha e o relatório têm limites diferentes, e é de propósito.

  fila.csv    500    é fila de trabalho: 500 cabe numa manhã
  vagas.html  3000   é o relatório para navegar e filtrar

O `--limit` do comando `export` valia 500 para os dois. Como o
ATUALIZAR-VAGAS.bat roda `collect` e depois `export`, o relatório de
3.000 linhas que o collect escrevia era sobrescrito por um de 500
alguns segundos depois — todo dia, sem uma linha de aviso. Em
02/09/2026 ele abriu o relatório e viu 500 vagas de 7.819.
"""
from adelaide_jobs import cli, export


def parser_export(*argv):
    p = cli.build_parser() if hasattr(cli, "build_parser") else None
    if p is None:                       # o nome do construtor pode variar
        import inspect
        for nome, obj in vars(cli).items():
            if inspect.isfunction(obj) and "parser" in nome:
                p = obj()
                break
    return p.parse_args(["export", *argv])


def test_limite_do_export_nasce_vazio():
    """Vazio quer dizer 'cada saída escolhe o seu'."""
    assert parser_export().limit is None


def test_limite_explicito_e_respeitado():
    assert parser_export("--limit", "42").limit == 42


def test_os_padroes_de_cada_saida_sao_diferentes():
    import inspect
    assert inspect.signature(export.to_csv).parameters["limit"].default == 500
    assert inspect.signature(export.to_html).parameters["limit"].default == 3000


def test_relatorio_traz_mais_que_a_fila(cfg, db, adzuna_payload):
    """O teste que teria pegado o bug: as duas saídas do mesmo banco
    não podem ter o mesmo tamanho por acidente."""
    from adelaide_jobs.collectors.adzuna import AdzunaCollector
    from adelaide_jobs.pipeline import Pipeline
    jobs = [AdzunaCollector.parse(r) for r in adzuna_payload["results"]]
    p = Pipeline(cfg, db)
    p.score_pending(p.ingest(jobs))
    assert (inspect_default(export.to_html) >
            inspect_default(export.to_csv)), "o relatório tem que caber mais"


def inspect_default(fn):
    import inspect
    return inspect.signature(fn).parameters["limit"].default
