"""Manda a fila de vagas por e-mail, para você mesmo.

POR QUE ISTO EXISTE
    A partir de 24/09/2026 a coleta roda na nuvem, sem PC ligado. Só que
    o relatório de vagas é justamente o que este projeto decidiu NÃO
    publicar na internet: ele traz o seu nome, o seu visto e uma nota
    por empregador. Um gerente de Adelaide não deveria achar isso.

    E-mail resolve os dois lados: chega no celular, e não fica público.

O QUE VAI NO CORPO
    Duas seções, nesta ordem, porque é assim que se lê de manhã:
      1. NOVAS desde a última coleta — é o que muda de um dia para o
         outro, e é por isso que vale abrir o e-mail.
      2. As melhores da fila — o pano de fundo, caso não tenha novidade.
    Mais o fila.csv anexado, para abrir no notebook.

CREDENCIAL
    Usa IMAP_USER e IMAP_PASSWORD, os mesmos que já leem os alertas —
    a senha de app do Gmail serve para ler (IMAP) e enviar (SMTP), então
    não é credencial nova. O destino é EMAIL_DESTINO, ou o próprio
    IMAP_USER se você não definir.

RODAR
    python enviar_por_email.py --db caminho/do/jobs.db
"""
from __future__ import annotations

import argparse
import html
import os
import pathlib
import smtplib
import ssl
import sys
from datetime import date, datetime, timedelta
from email.message import EmailMessage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from adelaide_jobs import config as config_mod  # noqa: E402
from adelaide_jobs.db import DEFAULT_DB, Database  # noqa: E402

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

# A mesma escala do resto do projeto. Repetir aqui seria criar uma
# segunda verdade; importo do cli para nao divergir.
try:
    from adelaide_jobs.cli import nota as _nota
except Exception:  # pragma: no cover - so se o cli mudar de forma
    def _nota(score):  # type: ignore[misc]
        return ("?", "")


def _e_nova(row, desde: datetime) -> bool:
    """first_seen mais recente que `desde`. Formato do banco varia, entao
    comparo por prefixo de data em vez de confiar num parser."""
    bruto = row["first_seen"]
    if not bruto:
        return False
    try:
        return datetime.fromisoformat(str(bruto)[:19]) >= desde
    except ValueError:
        return False


def _linha(row) -> str:
    letra, _ = _nota(row["score"])
    titulo = html.escape(row["title"] or "sem titulo")
    empresa = html.escape(row["employer"] or "empregador nao informado")
    local = html.escape(row["suburb"] or "")
    fonte = html.escape(row["melhor_fonte"] or "")
    url = row["melhor_url"] or ""
    fantasma = (
        ' <span style="color:#b45309;font-size:13px">· repostada muitas vezes,'
        ' pode nao existir</span>'
        if row["ghost_flag"] else ""
    )
    alvo = (
        f'<a href="{html.escape(url, quote=True)}"'
        f' style="color:#1f4e79;text-decoration:none">{titulo}</a>'
        if url else titulo
    )
    return f"""
    <tr>
      <td style="padding:14px 10px 14px 0;vertical-align:top;white-space:nowrap">
        <span style="display:inline-block;min-width:34px;text-align:center;
                     background:#1f4e79;color:#fff;border-radius:5px;
                     padding:4px 7px;font-weight:700;font-size:14px">{letra}</span>
      </td>
      <td style="padding:14px 0;border-bottom:1px solid #e5e5e5">
        <div style="font-size:16px;line-height:1.35;margin-bottom:3px">{alvo}</div>
        <div style="font-size:14px;color:#555">{empresa}</div>
        <div style="font-size:13px;color:#777">{local} · {fonte}{fantasma}</div>
      </td>
    </tr>"""


def _secao(titulo: str, subtitulo: str, linhas: list[str]) -> str:
    if not linhas:
        return ""
    return f"""
    <h2 style="font-size:17px;color:#1f4e79;margin:28px 0 2px">{titulo}</h2>
    <p style="font-size:13px;color:#777;margin:0 0 6px">{subtitulo}</p>
    <table style="width:100%;border-collapse:collapse">{''.join(linhas)}</table>"""


def montar(db: Database, limite: int, horas: int) -> tuple[str, int, int]:
    cfg = config_mod.load()
    fila = db.queue(cfg.queue_threshold, max(limite, 60))
    corte = datetime.now() - timedelta(hours=horas)

    novas = [r for r in fila if _e_nova(r, corte)]
    resto = [r for r in fila if not _e_nova(r, corte)][:limite]

    corpo = f"""<!doctype html><html><body style="margin:0;padding:18px;
      font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#1a1a1a">
      <p style="font-size:13px;color:#777;margin:0 0 4px">
        adelaide-jobs · {date.today().strftime('%d/%m/%Y')}</p>
      <h1 style="font-size:21px;margin:0 0 2px">Vagas em Adelaide</h1>
      <p style="font-size:14px;color:#555;margin:0">
        {len(novas)} novas nas ultimas {horas}h · nota minima {cfg.queue_threshold}</p>
      {_secao("Novas", "Apareceram desde a coleta anterior.", [_linha(r) for r in novas])}
      {_secao("Melhores da fila", "Ja estavam aqui, ainda valem.",
              [_linha(r) for r in resto])}
      <p style="font-size:12px;color:#999;margin-top:30px;border-top:1px solid #e5e5e5;
                padding-top:12px">
        Gerado pela coleta automatica. A nota mede o quanto a vaga cabe nas suas
        restricoes (visto, ingles, transporte) — nao mede a qualidade da vaga nem
        a sua chance de ser contratado. A fila completa vai no anexo.</p>
    </body></html>"""
    return corpo, len(novas), len(resto)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--limite", type=int, default=25, help="quantas vagas antigas listar")
    p.add_argument("--horas", type=int, default=26,
                   help="janela do que conta como 'nova' (26h cobre atraso do agendador)")
    p.add_argument("--anexo", default="exports/fila.csv")
    args = p.parse_args()

    usuario = os.getenv("IMAP_USER", "").strip()
    senha = os.getenv("IMAP_PASSWORD", "").strip()
    destino = os.getenv("EMAIL_DESTINO", "").strip() or usuario

    if not usuario or not senha:
        return _falta(
            "IMAP_USER e IMAP_PASSWORD precisam estar definidos.\n"
            "No GitHub: Settings -> Secrets and variables -> Actions."
        )
    # A senha de app do Gmail tem 16 letras minusculas, sem espaco. Se
    # tiver outra coisa aqui, quase sempre e a senha da conta — que o
    # Google recusa no SMTP e cuja falha nao diz isso com clareza.
    limpa = senha.replace(" ", "")
    if len(limpa) != 16 or not limpa.isalpha() or not limpa.islower():
        return _falta(
            "IMAP_PASSWORD nao parece uma senha de app do Gmail.\n"
            "Ela tem exatamente 16 letras minusculas, e e gerada em\n"
            "myaccount.google.com/apppasswords — nao e a senha da conta."
        )

    with Database(args.db) as db:
        corpo, n_novas, n_resto = montar(db, args.limite, args.horas)

    if n_novas == 0 and n_resto == 0:
        print("Fila vazia: nao mandei e-mail nenhum.")
        return 0

    msg = EmailMessage()
    msg["From"] = usuario
    msg["To"] = destino
    msg["Subject"] = (
        f"Vagas Adelaide · {n_novas} novas · {date.today().strftime('%d/%m')}"
        if n_novas else
        f"Vagas Adelaide · nada novo hoje · {date.today().strftime('%d/%m')}"
    )
    msg.set_content(
        "Este e-mail tem versao em HTML. Se voce esta lendo isto, seu "
        "programa de e-mail nao mostrou ela. A fila completa esta no anexo."
    )
    msg.add_alternative(corpo, subtype="html")

    anexo = pathlib.Path(args.anexo)
    if anexo.exists():
        msg.add_attachment(
            anexo.read_bytes(), maintype="text", subtype="csv", filename=anexo.name
        )

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context()) as s:
        s.login(usuario, limpa)
        s.send_message(msg)

    # Nunca imprimo a senha nem o corpo. O log do GitHub Actions e publico.
    print(f"enviado para {destino[:3]}...@{destino.split('@')[-1]}")
    print(f"novas: {n_novas} · outras na lista: {n_resto}")
    return 0


def _falta(texto: str) -> int:
    print(texto, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
