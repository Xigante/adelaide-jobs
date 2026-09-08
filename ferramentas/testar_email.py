"""Confere a caixa de alertas antes de ligar o coletor.

POR QUE EXISTE
    Ligar o `email_alerts` e rodar a coleta inteira só para descobrir
    que a senha está errada é caro: são dez minutos e um pedaço da cota
    da Adzuna. Isto aqui conecta, olha e sai — em dois segundos.

O QUE ELE RESPONDE
    1. A senha de app funciona?
    2. Que pastas existem nessa conta? (rótulo do Gmail = pasta do IMAP)
    3. Quantos e-mails tem na pasta escolhida?
    4. O que o programa consegue extrair dos mais recentes?

A SENHA NUNCA APARECE NA TELA. Só o número de caracteres, para você
conferir se colou os 16 da senha de app e não outra coisa.

RODAR
    Duplo clique no TESTAR-EMAIL.bat, ou:
    python testar_email.py
"""
from __future__ import annotations

import collections
import imaplib
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import caminhos  # noqa: E402

sys.path.insert(0, str(caminhos.RAIZ / "src"))


def diz(msg: str = "") -> None:
    print(msg, flush=True)


def ler_env() -> dict[str, str]:
    """Lê o .env sem depender do pacote estar instalado."""
    env: dict[str, str] = {}
    arq = caminhos.RAIZ / ".env"
    if not arq.exists():
        raise SystemExit(f"não achei o {arq}")
    for linha in arq.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        k, v = linha.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def main() -> int:
    env = ler_env()
    host = env.get("IMAP_HOST") or "imap.gmail.com"
    porta = int(env.get("IMAP_PORT") or 993)
    usuario = env.get("IMAP_USER", "")
    senha = env.get("IMAP_PASSWORD", "")
    pasta = env.get("IMAP_FOLDER") or "INBOX"

    diz()
    diz("  Teste da caixa de alertas")
    diz("  " + "=" * 56)
    diz(f"  servidor  {host}:{porta}")
    diz(f"  usuário   {usuario or '(VAZIO)'}")
    mascara = ("*" * min(len(senha), 20) + f"  ({len(senha)} caracteres)"
               if senha else "(VAZIA)")
    diz(f"  senha     {mascara}")
    diz(f"  pasta     {pasta}")
    diz()

    if not usuario or not senha:
        diz("  [ERRO] IMAP_USER ou IMAP_PASSWORD estão vazios no .env.")
        diz()
        diz("  Abra o .env na pasta do projeto e preencha:")
        diz("      IMAP_USER=seuemail@gmail.com")
        diz("      IMAP_PASSWORD=<a senha de app de 16 caracteres>")
        diz()
        diz("  A senha de app se cria em:")
        diz("      https://myaccount.google.com/apppasswords")
        diz("  Não é a senha da conta. Se a sua tem 16 caracteres e nenhum")
        diz("  espaço, é a certa — o Google mostra em grupos de 4, mas você")
        diz("  pode colar com ou sem os espaços.")
        return 1

    # Parar ANTES de conectar quando a senha claramente não é uma senha
    # de app. O servidor só sabe responder "Invalid credentials", que não
    # diz o que está errado — e já custou uma rodada inteira de tentativa
    # e erro. Aqui dá para dizer exatamente o que está fora do formato.
    if host.endswith("gmail.com"):
        from configurar_email import conferir
        problemas = conferir(senha)
        if problemas:
            diz("  [ERRO] A senha gravada no .env não tem o formato de uma")
            diz("         senha de app do Google.")
            diz()
            diz("         A do Google é sempre: 16 letras minúsculas,")
            diz("         nenhum número, nenhum símbolo. Ela aparece em")
            diz("         4 grupos de 4:  abcd efgh ijkl mnop")
            diz()
            diz("         A que está gravada:")
            for item in problemas:
                diz(f"           - {item}")
            diz()
            diz("         Nem tentei conectar — o Google ia recusar e a")
            diz("         resposta dele não explicaria o motivo.")
            diz()
            diz("         Pegue o código certo em:")
            diz("           https://myaccount.google.com/apppasswords")
            diz("         Se a 'coletor-vagas' já estiver na lista, apague")
            diz("         e crie outra: o código só aparece uma vez.")
            diz()
            diz("         Depois rode o CONFIGURAR-EMAIL.bat de novo.")
            return 1

    diz("  [..] Conectando...")
    try:
        caixa = imaplib.IMAP4_SSL(host, porta)
    except Exception as exc:                                  # noqa: BLE001
        diz(f"  [ERRO] Não conectei em {host}:{porta} — {exc}")
        diz("         Quase sempre é internet, firewall da empresa, ou")
        diz("         antivírus bloqueando a porta 993.")
        return 1

    try:
        caixa.login(usuario, senha)
    except imaplib.IMAP4.error as exc:
        diz(f"  [ERRO] O servidor recusou o login: {exc}")
        diz()
        diz("  A senha tem o formato certo (16 letras minúsculas), então")
        diz("  não é erro de digitação. As causas, em ordem:")
        diz()
        diz("    1. VOCÊ TROCOU A SENHA DA CONTA depois de criar esta.")
        diz("       O Google revoga TODAS as senhas de app quando a senha")
        diz("       da conta muda. Não avisa. É só criar outra em")
        diz("       https://myaccount.google.com/apppasswords e rodar o")
        diz("       CONFIGURAR-EMAIL.bat de novo.")
        diz()
        diz("    2. A senha de app foi apagada naquela mesma página.")
        diz()
        diz("    3. O e-mail está escrito errado no .env.")
        diz(f"       Está gravado: {usuario}")
        return 1
    diz("  [ok] Login aceito.")

    # ── pastas ──────────────────────────────────────────────────────
    diz()
    diz("  Pastas nesta conta (rótulo do Gmail = pasta do IMAP):")
    try:
        _, linhas = caixa.list()
        nomes = []
        for bruto in linhas or []:
            t = bruto.decode("utf-8", "replace")
            m = re.search(r'"([^"]+)"\s*$', t) or re.search(r"(\S+)\s*$", t)
            if m:
                nomes.append(m.group(1))
        for n in nomes:
            marca = "  <-- é esta" if n == pasta else ""
            diz(f"     {n}{marca}")
        if pasta not in nomes:
            diz()
            diz(f"  [!] A pasta {pasta!r} não está na lista acima.")
            diz("      Corrija IMAP_FOLDER no .env com um dos nomes de cima.")
    except Exception as exc:                                  # noqa: BLE001
        diz(f"     (não consegui listar: {exc})")

    # ── conteúdo ────────────────────────────────────────────────────
    diz()
    try:
        tipo, dados = caixa.select(f'"{pasta}"', readonly=True)
        if tipo != "OK":
            diz(f"  [ERRO] Não abri a pasta {pasta!r}: {dados}")
            return 1
        total = int(dados[0])
    except Exception as exc:                                  # noqa: BLE001
        diz(f"  [ERRO] Não abri a pasta {pasta!r}: {exc}")
        return 1

    diz(f"  [ok] Pasta {pasta!r} aberta: {total} mensagem(ns).")
    if total == 0:
        diz()
        diz("  A caixa está vazia. Isso é esperado se você acabou de")
        diz("  assinar os alertas: eles chegam no dia seguinte.")
        diz("  Volte aqui amanhã antes de ligar o coletor.")
        caixa.logout()
        return 0

    # ── o que dá para extrair ───────────────────────────────────────
    diz()
    diz("  [..] Lendo as 5 mensagens mais recentes...")
    try:
        from adelaide_jobs.collectors.email_alerts import parse_email
    except Exception as exc:                                  # noqa: BLE001
        diz(f"  [!] O pacote não está instalado ({exc}).")
        diz("      Rode o INSTALAR.bat. A conexão está boa, que é o que")
        diz("      este teste precisava provar.")
        caixa.logout()
        return 0

    _, res = caixa.search(None, "ALL")
    uids = (res[0].split() if res and res[0] else [])[-5:]
    achadas, remetentes = [], collections.Counter()
    for uid in uids:
        _, dados = caixa.fetch(uid, "(RFC822)")
        for parte in dados or []:
            if isinstance(parte, tuple):
                bruto = parte[1]
                de = re.search(rb"^From:.*$", bruto, re.M | re.I)
                if de:
                    remetentes[de.group(0).decode("utf-8", "replace")[:78]] += 1
                try:
                    achadas.extend(parse_email(bruto))
                except Exception as exc:                      # noqa: BLE001
                    diz(f"      (uma mensagem não foi lida: {exc})")
    caixa.logout()

    diz()
    diz("  Quem mandou:")
    for r, n in remetentes.most_common():
        diz(f"     {n}x  {r}")

    por_fonte = collections.Counter(j.source for j in achadas)
    diz()
    diz(f"  Vagas extraídas dessas mensagens: {len(achadas)}")
    for f, n in por_fonte.most_common():
        diz(f"     {n:4d}  {f}")
    if achadas:
        diz()
        diz("  Amostra:")
        for j in achadas[:6]:
            diz(f"     {(j.title or '(sem título)')[:52]:52s}  {j.url[:44]}")
        diz()
        diz("  Está funcionando. Pode ligar o coletor:")
        diz("     config/sources.yaml → email_alerts → enabled: true")
    else:
        diz()
        diz("  [!] Conectou e leu, mas não extraiu nenhuma vaga.")
        diz("      Ou as mensagens não são alertas de vaga, ou são de uma")
        diz("      plataforma que o programa ainda não conhece. Ele conhece:")
        diz("      SEEK, LinkedIn, Indeed, Jora, Adzuna, iworkfor.sa.gov.au")
        diz("      e Gumtree. Me mande uma dessas mensagens e eu acrescento.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
