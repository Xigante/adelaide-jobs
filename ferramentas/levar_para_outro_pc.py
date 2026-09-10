# -*- coding: utf-8 -*-
"""Empacota o que o GitHub não leva, para a mudança de computador.

O repositório carrega o programa inteiro. Duas coisas ficam de fora, e
são justamente as que doem:

  .env      está no .gitignore de propósito — tem a chave da Adzuna e a
            senha de app do Gmail. Sem ele o programa instala e não
            coleta nada.

  jobs.db   mora em %USERPROFILE%\\.adelaide-jobs\\, fora da pasta do
            projeto. É o histórico: quando cada vaga apareceu pela
            primeira vez, quantas vezes cada empregador repostou, os
            3.500+ empregadores. Sem ele o programa funciona, mas
            começa do zero e o "quem está sempre contratando" só volta
            a fazer sentido depois de semanas.

O banco é copiado pela API de backup do SQLite, não com cópia de
arquivo. Copiar .db a frio já corrompeu este banco duas vezes: se a
coleta estiver rodando, ou se sobrar um -wal, o arquivo copiado sai
inconsistente. O backup do SQLite resolve isso e ainda funciona com o
banco aberto.

RODAR
    Duplo clique no LEVAR-PARA-OUTRO-PC.bat
"""
from __future__ import annotations

import datetime
import pathlib
import sqlite3
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import caminhos  # noqa: E402

LEIAME = """COMO CONTINUAR NO COMPUTADOR NOVO
=================================

1. Instale o Git:            https://git-scm.com/download/win
   e o Python 3.11+:         https://www.python.org/downloads/
   No Python, MARQUE "Add Python to PATH" na primeira tela.

2. Baixe o projeto. Numa pasta qualquer, abra o Prompt de Comando e:

       git clone https://github.com/Xigante/adelaide-jobs.git

3. Entre na pasta e dê dois cliques em  INSTALAR.bat
   Ele cria o ambiente e pede a chave da Adzuna — pode deixar em
   branco, o passo 4 resolve.

4. Copie os dois arquivos deste zip:

       .env      -> para dentro da pasta adelaide-jobs\\
       jobs.db   -> para  %USERPROFILE%\\.adelaide-jobs\\jobs.db
                    (crie a pasta .adelaide-jobs se não existir;
                     para chegar nela, digite %USERPROFILE% na barra
                     do Explorador de Arquivos)

5. Confira antes de coletar:

       ferramentas\\TESTAR-EMAIL.bat     tem que aceitar o login
       ferramentas\\ATUALIZAR-VAGAS.bat  tem que achar o histórico

   Se o relatório vier com poucas vagas e todas "vistas hoje", o banco
   não foi para o lugar certo — refaça o passo 4.

O QUE TEM NESTE ZIP
===================

  .env      chave da Adzuna e senha de app do Gmail.
            NÃO mande por e-mail, WhatsApp nem chat. Pen drive, ou
            um serviço de arquivo com senha.

  jobs.db   o histórico inteiro da coleta.

Gerado em {quando} · {vagas} vagas, {empresas} empregadores.
"""


def diz(m: str = "") -> None:
    print(m, flush=True)


def main() -> int:
    env = caminhos.RAIZ / ".env"
    banco = caminhos.BANCO
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    # NÃO na pasta do projeto: ela vive dentro do "OneDrive - FLOW".
    # Um zip com a senha de app do Gmail dele sincronizando para a
    # nuvem do empregador é exatamente o que não pode acontecer.
    # A home do usuário no Windows não é sincronizada por padrão.
    destino = pathlib.Path.home() / f"adelaide-jobs-mudanca-{hoje}.zip"

    diz()
    diz("  Levar para outro computador")
    diz("  " + "=" * 60)
    diz()

    faltando = [str(p) for p in (env, banco) if not p.exists()]
    if faltando:
        diz("  [ERRO] Não achei:")
        for f in faltando:
            diz(f"      {f}")
        diz()
        diz("  Sem os dois não adianta empacotar. Rode o")
        diz("  ATUALIZAR-VAGAS.bat uma vez e tente de novo.")
        return 1

    # Backup do SQLite: consistente mesmo com o banco aberto.
    temp = caminhos.RAIZ / "_banco_para_levar.db"
    diz("  [..] Copiando o banco pela API de backup do SQLite...")
    origem = sqlite3.connect(f"file:{banco}?mode=ro", uri=True)
    try:
        copia = sqlite3.connect(temp)
        try:
            origem.backup(copia)
            vagas = copia.execute("SELECT COUNT(*) FROM job_cluster").fetchone()[0]
            empresas = copia.execute("SELECT COUNT(*) FROM employer").fetchone()[0]
            integro = copia.execute("PRAGMA integrity_check(1)").fetchone()[0]
        finally:
            copia.close()
    finally:
        origem.close()

    if integro != "ok":
        temp.unlink(missing_ok=True)
        diz(f"  [ERRO] A cópia saiu com problema: {integro}")
        diz("  Rode o REPARAR-BANCO.bat antes de levar.")
        return 1

    diz(f"  [ok] {vagas} vagas, {empresas} empregadores · íntegro")
    diz()
    diz("  [..] Montando o zip...")
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(env, ".env")
        z.write(temp, "jobs.db")
        z.writestr("LEIA-ME-PRIMEIRO.txt", LEIAME.format(
            quando=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            vagas=vagas, empresas=empresas))
    temp.unlink(missing_ok=True)

    mb = destino.stat().st_size / (1024 * 1024)
    diz()
    diz("  " + "=" * 60)
    diz(f"  Pronto: {destino.name}  ({mb:.1f} MB)")
    diz(f"  Em: {destino.parent}")
    diz()
    diz("  Dentro tem o .env, o jobs.db e um LEIA-ME com o passo a")
    diz("  passo do computador novo.")
    diz()
    diz("  Ficou fora da pasta do projeto de propósito: ela sincroniza")
    diz("  para o OneDrive da FLOW, e senha não vai para a nuvem do")
    diz("  empregador.")
    diz()
    diz("  ATENÇÃO: o .env tem a chave da Adzuna e a senha de app do")
    diz("  Gmail. Leve em pen drive. Não mande por e-mail nem chat, e")
    diz("  apague o zip do computador velho depois que terminar.")
    diz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
