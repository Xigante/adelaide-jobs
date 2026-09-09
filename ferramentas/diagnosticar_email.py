# -*- coding: utf-8 -*-
"""Mostra o FORMATO dos links dentro dos alertas, para consertar o leitor.

POR QUE EXISTE
    O TESTAR-EMAIL.bat responde "conectei e não extraí nada". Isso diz
    que quebrou, não ONDE. Cada plataforma muda o embrulho dos links de
    tempos em tempos — o SEEK põe o destino no caminho, o Indeed às
    vezes em base64, o Adzuna troca /details/ por outra coisa — e o
    regex que casava mês passado para de casar sem aviso.

    Isto aqui abre os e-mails, extrai as URLs e mostra a FORMA delas
    junto com o veredito do identificador. Com isso dá para corrigir o
    padrão em dois minutos em vez de adivinhar.

O QUE ELE NÃO MOSTRA
    O corpo dos e-mails, nomes, nada pessoal. Só remetente, assunto e
    as URLs — que são links públicos de vaga. E nunca a senha.

RODAR
    Duplo clique no DIAGNOSTICAR-EMAIL.bat
"""
from __future__ import annotations

import collections
import email
import imaplib
import pathlib
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import caminhos  # noqa: E402

sys.path.insert(0, str(caminhos.RAIZ / "src"))
from adelaide_jobs.collectors.email_alerts import (  # noqa: E402
    RE_URL, _partes, desembrulhar, identificar,
)

QUANTOS = 12


def diz(m: str = "") -> None:
    print(m, flush=True)


def ler_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for linha in (caminhos.RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def forma(url: str) -> str:
    """A URL sem o que é único dela: só o desenho, para agrupar iguais."""
    p = urlparse(url)
    caminho = re.sub(r"/[0-9a-f]{16,}", "/<hash>", p.path)
    caminho = re.sub(r"/\d{5,}", "/<id>", caminho)
    caminho = re.sub(r"/[A-Za-z0-9_-]{24,}", "/<blob>", caminho)
    chaves = sorted({c.split("=")[0] for c in p.query.split("&") if c})
    q = ("?" + "&".join(k + "=…" for k in chaves[:6])) if chaves else ""
    return f"{p.netloc}{caminho}{q}"


def main() -> int:
    env = ler_env()
    usuario, senha = env.get("IMAP_USER", ""), env.get("IMAP_PASSWORD", "")
    pasta = env.get("IMAP_FOLDER") or "INBOX"
    if not usuario or not senha:
        diz("  [ERRO] .env sem IMAP_USER/IMAP_PASSWORD. "
            "Rode o CONFIGURAR-EMAIL.bat.")
        return 1

    diz()
    diz("  Diagnóstico dos alertas")
    diz("  " + "=" * 64)
    caixa = imaplib.IMAP4_SSL(env.get("IMAP_HOST") or "imap.gmail.com",
                              int(env.get("IMAP_PORT") or 993))
    try:
        caixa.login(usuario, senha)
    except imaplib.IMAP4.error as exc:
        diz(f"  [ERRO] login recusado: {exc}")
        diz("  Crie outra senha de app e rode o CONFIGURAR-EMAIL.bat.")
        return 1
    caixa.select(f'"{pasta}"', readonly=True)
    _, dados = caixa.search(None, "ALL")
    uids = (dados[0].split() or [])[-QUANTOS:]
    diz(f"  {len(uids)} e-mail(s) mais recentes de {pasta!r}")
    diz()

    total_ok = 0
    nao_casou: collections.Counter[str] = collections.Counter()

    for uid in reversed(uids):
        ok, d = caixa.fetch(uid, "(RFC822)")
        if ok != "OK" or not d or not isinstance(d[0], tuple):
            continue
        msg = email.message_from_bytes(d[0][1])
        de = str(msg.get("From", ""))[:52]
        assunto = str(email.header.make_header(
            email.header.decode_header(msg.get("Subject", ""))))[:58]

        texto, htm = _partes(msg)
        urls = {desembrulhar(u) for u in RE_URL.findall(texto + " " + htm)}
        casadas = [u for u in urls if identificar(u)]
        plats = collections.Counter(identificar(u)[0] for u in casadas)
        total_ok += len(casadas)

        diz(f"  ── {assunto}")
        diz(f"     de: {de}")
        diz(f"     {len(urls)} link(s) · {len(casadas)} reconhecido(s) "
            f"{dict(plats) if plats else ''}")
        if not casadas:
            # As formas mais repetidas são as candidatas a virar padrão.
            comuns = collections.Counter(forma(u) for u in urls).most_common(6)
            for f, n in comuns:
                diz(f"       {n:3}x  {f[:88]}")
                nao_casou[f] += n
        diz()

    caixa.logout()
    diz("  " + "=" * 64)
    diz(f"  Vagas reconhecidas ao todo: {total_ok}")
    if nao_casou:
        diz()
        diz("  FORMAS QUE NINGUÉM RECONHECEU (as candidatas a padrão novo):")
        for f, n in nao_casou.most_common(12):
            diz(f"    {n:3}x  {f[:92]}")
        diz()
        diz("  Copie este bloco e me mande. Com a forma na mão eu acerto")
        diz("  o padrão em dois minutos.")
    diz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
