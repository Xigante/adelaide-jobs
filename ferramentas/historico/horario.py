"""Crítica de design aplicada: horário vira instrução, e o celular vira usável.

DOIS ACHADOS, os dois relatados pelo usuário e confirmados na tela.

1. O HORÁRIO ERA UM PARÁGRAFO, NÃO UMA INSTRUÇÃO.
   Estava assim: "14h–16h. Entre 14h e 16h o rush do almoço acabou. Vá
   às 14h, não às 15h50: muito café de Adelaide fecha entre 15h e 16h."
   São três orações para extrair uma ação, e a pergunta que a pessoa faz
   — "vou antes ou depois do rush?" — não é respondida em lugar nenhum.
   Agora são duas linhas: VÁ ENTRE / NÃO VÁ. O porquê vem depois, em
   letra menor, para quem quiser.

2. NO CELULAR A ABA DE ROTA ABRIA DENTRO DO MAPA.
   Mapa de 380px ocupava a primeira tela inteira; o seletor de janela e
   o botão principal ficavam abaixo da dobra. A pessoa caía no meio de
   um mapa sem saber o que fazer. Agora, em tela estreita, a ordem é:
   escolher a janela → botão principal → mapa → lista.
"""
import json
import pathlib
import re
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")

RE_PADARIA = re.compile(r"baker|padaria|brumby|banjo|bread|patisserie", re.I)

# (janela, ir, evitar, porque)
def regra(reg: dict) -> tuple[str, str, str, str]:
    setor = reg["setor"]
    cat = (reg.get("categoria") or "").lower()
    nome = reg["empregador"]

    if setor == "Saúde e aged care":
        return ("online", "Não vá até lá — é só online",
                "aparecer sem aviso não ajuda e pode atrapalhar",
                "Hospital e casa de repouso exigem police check e worker screening. "
                "Tudo entra pelo portal, e o RH nem atende na portaria.")

    if setor == "Escritório":
        if any(k in cat for k in ("games", "edtech", "animação")):
            return ("online", "Não vá até lá — é e-mail com portfólio",
                    "estúdio pequeno não tem recepção",
                    "Quem abre a porta é o portfólio, não a visita.")
        if "executive search" in cat:
            return ("online", "Não vá até lá — e-mail direto ao sócio",
                    "boutique de 5 pessoas não tem recepção",
                    "Anexe um trabalho seu. É isso que eles não têm em casa.")
        return ("manha", "10h00 – 11h30, terça a quinta",
                "antes das 9h30 · 12h–14h (almoço) · sexta à tarde",
                "Já passou o e-mail da abertura e ainda não é almoço — a única "
                "janela em que o recrutador para para olhar seu currículo.")

    if setor == "Hotéis e eventos":
        if any(k in cat for k in ("agência", "plataforma", "catering", "terceirizado")):
            if "housekeeping" in cat or "limpeza" in cat:
                return ("manha", "10h00 – 11h30",
                        "antes das 10h (troca de turno) · depois das 14h",
                        "A supervisora de housekeeping fecha a escala depois do "
                        "check-out e sabe quem faltou.")
            return ("online", "Não vá até lá — é cadastro online",
                    "ir pessoalmente não gera turno",
                    "O turno sai do perfil na plataforma, não da visita.")
        if "limpeza" in cat or "facilities" in cat:
            return ("manha", "9h00 – 11h00, no ESCRITÓRIO da empresa",
                    "não vá ao prédio que eles limpam — lá ninguém contrata",
                    "Limpeza é terceirizada: quem contrata é o escritório da "
                    "empresa, não o shopping nem o hospital onde você vai "
                    "trabalhar. Ir ao local de trabalho não adianta nada.")
        if "pub" in cat:
            return ("tarde", "14h30 – 16h30",
                    "12h–14h (almoço) · depois das 17h (montagem do jantar)",
                    "É o vão entre almoço e jantar, a única hora em que o gerente "
                    "de salão consegue parar.")
        return ("manha", "10h00 – 11h30",
                "antes das 10h (check-out) · depois das 14h (check-in)",
                "Entre a saída e a entrada dos hóspedes a governanta está no "
                "prédio e já sabe de quantas camareiras vai precisar.")

    if setor == "Armazém e logística":
        if "aplicativo" in cat:
            return ("online", "Não vá até lá — e este nem serve para você",
                    "exige carta australiana e carro próprio",
                    "Cadastro por aplicativo, e os requisitos te excluem.")
        if "agência" in cat:
            return ("manha", "9h00 – 11h00 — LIGUE às 8h antes de ir",
                    "depois das 11h, quando a escala do dia já fechou",
                    "Agência de labour hire fecha a escala cedo, e telefone "
                    "funciona muito melhor que formulário.")
        return ("manha", "9h00 – 11h00",
                "depois das 11h",
                "O encarregado está no chão de manhã. Depois disso ele some "
                "para dentro da operação.")

    if RE_PADARIA.search(nome) or RE_PADARIA.search(cat):
        return ("manha", "9h00 – 11h00",
                "antes das 8h (pico do café da manhã) · depois do meio-dia",
                "O turno da padaria começou às 4h. Às 9h o gerente já está há "
                "cinco horas na loja e o movimento passou.")

    if setor == "Supermercados e varejo":
        if "varejo" in cat and "supermercado" not in cat and "conveniência" not in cat:
            return ("manha", "10h00 – 12h00, segunda a quarta",
                    "quinta à noite (late night trading) · sexta · fim de semana",
                    "Loja de shopping fica vazia no começo da semana de manhã, "
                    "que é quando o gerente consegue conversar.")
        return ("manha", "9h00 – 11h00, segunda a quinta",
                "sábado e domingo · depois das 16h30 (troca de turno)",
                "O gerente de loja faz o giro de manhã, e o corredor está vazio.")

    if setor == "Cafés independentes":
        return ("tarde", "14h00 – 15h00",
                "7h–14h (café da manhã e almoço) · depois das 15h30, muitos já fecharam",
                "Você quer o dono com o salão vazio. Logo depois do almoço, "
                "não em cima do fechamento.")

    if setor == "Redes de restaurante":
        return ("tarde", "14h30 – 16h30",
                "12h–14h (almoço) · depois das 17h (montagem do jantar)",
                "É o vão entre almoço e jantar, a única hora do dia em que o "
                "gerente consegue parar para te ouvir.")

    return ("manha", "10h00 – 12h00", "12h–14h (almoço)", "Horário comercial, fora do pico.")


def main() -> None:
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak7"))
    i = s.find('[{"setor"')
    prof = 0
    for j in range(i, len(s)):
        if s[j] == "[":
            prof += 1
        elif s[j] == "]":
            prof -= 1
            if prof == 0:
                break
    d = json.loads(s[i:j + 1])
    for r in d:
        jan, ir, evitar, porque = regra(r)
        r["jan"] = jan
        r["ir"] = ir
        r["nao"] = evitar
        r["jpq"] = porque
    s = s[:i] + json.dumps(d, ensure_ascii=False) + s[j + 1:]
    ARQ.write_text(s, encoding="utf-8")
    from collections import Counter
    print("por janela:", dict(Counter(r["jan"] for r in d)))
    for ex in ("Seafaring Fool", "Estia Health", "Australian Green Clean"):
        r = next((x for x in d if x["empregador"] == ex), None)
        if r:
            print(f"\n{ex}\n  VÁ:    {r['ir']}\n  NÃO:   {r['nao']}\n  porquê: {r['jpq'][:70]}…")


if __name__ == "__main__":
    main()
