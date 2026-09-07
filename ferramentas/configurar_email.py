"""Escreve o e-mail e a senha de app no .env, sem você abrir arquivo nenhum.

POR QUE EXISTE
    O passo "edite o .env" derruba todo mundo. O arquivo começa com
    ponto, o Windows esconde arquivos assim, o Bloco de Notas insiste
    em salvar como .txt, e a senha de app que o Google mostra vem
    escrita "abcd efgh ijkl mnop" — com espaços que NÃO fazem parte
    da senha. Quem cola do jeito que aparece grava uma senha errada e
    o erro que volta é "credenciais inválidas", que não ajuda em nada.

    Este script pergunta as duas coisas, tira os espaços sozinho, e
    grava nas linhas certas. O resto do .env não é tocado.

A SENHA NÃO APARECE NA TELA enquanto você digita e não é impressa em
lugar nenhum depois. Ela vai direto para o .env, que está no
.gitignore e nunca sobe para o GitHub.

RODAR
    Duplo clique no CONFIGURAR-EMAIL.bat
"""
from __future__ import annotations

import getpass
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import caminhos  # noqa: E402

ENV = caminhos.RAIZ / ".env"


def diz(msg: str = "") -> None:
    print(msg, flush=True)


def gravar(chaves: dict[str, str]) -> None:
    """Troca só as linhas pedidas. Comentários e o resto ficam iguais."""
    bruto = ENV.read_bytes().decode("utf-8")
    # Preserva a quebra de linha que o arquivo já usa.
    fim = "\r\n" if "\r\n" in bruto else "\n"
    linhas = bruto.replace("\r\n", "\n").split("\n")

    faltando = dict(chaves)
    for i, linha in enumerate(linhas):
        m = re.match(r"^([A-Z_]+)=", linha.strip())
        if m and m.group(1) in faltando:
            chave = m.group(1)
            linhas[i] = f"{chave}={faltando.pop(chave)}"

    # Chave que não existia: entra logo depois do IMAP_PORT.
    for chave, valor in faltando.items():
        alvo = next((i for i, l in enumerate(linhas)
                     if l.startswith("IMAP_PORT=")), len(linhas) - 1)
        linhas.insert(alvo + 1, f"{chave}={valor}")

    ENV.write_bytes(fim.join(linhas).encode("utf-8"))


def conferir(senha: str) -> list[str]:
    """Diz o que há de errado com o que foi colado, sem mostrar nada.

    A senha de app do Google é `[a-z]{16}`, sempre. Antes isto aqui só
    olhava o comprimento e deixava passar com um "s" — e passou: foram
    gravados 19 caracteres com números e hífen, o servidor respondeu
    "Invalid credentials" e a mensagem não dizia o que estava errado.
    """
    fora = []
    if len(senha) != 16:
        fora.append(f"tem {len(senha)} caracteres, e não 16")
    if any(c.isdigit() for c in senha):
        fora.append("tem número, e senha de app não tem número")
    if any(c.isupper() for c in senha):
        fora.append("tem letra MAIÚSCULA, e senha de app é toda minúscula")
    simbolos = sorted({c for c in senha if not c.isalnum()})
    if simbolos:
        mostra = " ".join(repr(c) for c in simbolos)
        fora.append(f"tem símbolo ({mostra}), e senha de app só tem letras")
    return fora


def main() -> int:
    diz()
    diz("  Configurar a caixa de alertas")
    diz("  " + "=" * 56)
    diz()

    if not ENV.exists():
        diz(f"  [ERRO] Não achei o .env em {ENV.parent}")
        diz("  Rode o INSTALAR.bat uma vez antes deste aqui.")
        return 1

    diz("  1) O endereço da conta NOVA do Gmail, a que recebe os")
    diz("     alertas do SEEK, LinkedIn, Indeed e Jora.")
    diz()
    email = input("     e-mail: ").strip()
    if "@" not in email or " " in email:
        diz()
        diz("  [ERRO] Isso não parece um endereço de e-mail.")
        return 1
    if not email.lower().endswith("@gmail.com"):
        diz()
        diz(f"  [AVISO] {email} não é um Gmail. O servidor configurado")
        diz("          é o do Gmail (imap.gmail.com), então isto só vai")
        diz("          funcionar se for mesmo uma conta Google.")
        diz()
        if input("     Continuar assim? (s/N): ").strip().lower() != "s":
            return 1

    diz()
    diz("  2) A SENHA DE APP de 16 caracteres, a que o Google mostrou")
    diz("     depois que você criou a 'coletor-vagas'.")
    diz()
    diz("     NÃO é a senha que você usa para entrar no Gmail.")
    diz("     Pode colar com os espaços — eu tiro sozinho.")
    diz("     Ela não vai aparecer enquanto você digita. Isso é normal:")
    diz("     cole e aperte Enter, mesmo parecendo que nada aconteceu.")
    diz()
    senha = getpass.getpass("     senha de app: ")
    senha = re.sub(r"\s+", "", senha)

    if not senha:
        diz()
        diz("  [ERRO] Nada foi digitado.")
        return 1

    problemas = conferir(senha)
    if problemas:
        diz()
        diz("  " + "=" * 56)
        diz("  ISSO NÃO PARECE UMA SENHA DE APP")
        diz("  " + "=" * 56)
        diz()
        diz("  A senha de app do Google é sempre assim:")
        diz("      16 caracteres, só letras minúsculas.")
        diz("      Nenhum número. Nenhum símbolo. Nenhuma maiúscula.")
        diz("      O Google mostra em 4 grupos:  abcd efgh ijkl mnop")
        diz()
        diz("  O que você colou:")
        for p_ in problemas:
            diz(f"      - {p_}")
        diz()
        diz("  Quase sempre isso quer dizer uma destas duas:")
        diz()
        diz("    a) você colou a senha com que ENTRA no Gmail.")
        diz("       Essa não funciona aqui — o Google bloqueia de")
        diz("       propósito. Tem que ser a senha de app.")
        diz()
        diz("    b) você copiou o NOME que deu para a senha de app")
        diz("       ('coletor-vagas') em vez do código que apareceu")
        diz("       na caixa amarela depois de clicar em Criar.")
        diz()
        diz("  Onde pegar o código certo:")
        diz("      https://myaccount.google.com/apppasswords")
        diz("      Se a 'coletor-vagas' já estiver na lista, apague e")
        diz("      crie outra — o código só aparece uma vez, e depois")
        diz("      não tem como ver de novo.")
        diz()
        if input("     Gravar assim mesmo? digite CONTINUAR: ").strip() != "CONTINUAR":
            diz()
            diz("  Nada foi gravado. Rode este botão de novo com o")
            diz("  código de 16 letras na mão.")
            return 1

    gravar({
        "IMAP_USER": email,
        "IMAP_PASSWORD": senha,
        "IMAP_FOLDER": "INBOX",
    })

    diz()
    diz("  " + "=" * 56)
    diz("  Gravado no .env.")
    diz(f"    IMAP_USER      {email}")
    diz(f"    IMAP_PASSWORD  {'*' * len(senha)}  ({len(senha)} caracteres)")
    diz("    IMAP_FOLDER    INBOX")
    diz()
    diz("  O .env fica só no seu computador. Ele está no .gitignore,")
    diz("  então nunca sobe para o GitHub.")
    diz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
