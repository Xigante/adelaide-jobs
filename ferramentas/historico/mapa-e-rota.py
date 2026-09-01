"""Mini-mapa do centro e a aba de rota a pé com CV impresso.

DUAS DECISÕES DE HONESTIDADE, porque as duas seriam fáceis de falsificar:

1. O MAPA É UM ESQUEMA, não um mapa de GPS. A posição de cada ponto vem
   do nome da rua (que é exato) mais o número (que vira uma posição
   aproximada ao longo dela). Serve para ordenar a caminhada e entender
   a cidade, não para navegar. Está escrito na tela.

   O que salva o esquema é que o centro de Adelaide é literalmente uma
   grade de 1 km por 1 km entre as quatro Terraces, com King William no
   meio. Então as distâncias saem perto das reais, e a ordem das paradas
   sai certa.

2. O HORÁRIO É REGRA DE SETOR, NÃO HORÁRIO VERIFICADO DA LOJA. Eu não
   tenho o horário de funcionamento de 232 empregadores e não vou
   inventar. O que existe e é sólido é a norma do setor sobre quando o
   gerente está presente e sem rush — que é exatamente o que importa
   para entregar currículo na mão.

   O horário legal do CBD, esse sim é fato verificado (SafeWork SA):
   loja comum fecha 21h de segunda a sexta, 17h no sábado, e domingo é
   9h às 17h. Café e restaurante são ISENTOS e fazem o horário que
   quiserem — por isso a regra de café é norma do ramo, não lei.
"""
import json
import pathlib
import re
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")

# ── A grade do centro, em metros a partir de West Tce / North Tce ────
# Adelaide foi desenhada em 1837 como um quadrado perfeito de 1 milha
# quadrada. Isso é o que torna o esquema utilizável.
CORREDORES = {  # ruas leste-oeste → distância ao sul da North Terrace
    "north terrace": 0, "north tce": 0,
    "rundle": 155, "hindley": 155,
    "grenfell": 300, "currie": 300,
    "pirie": 420, "waymouth": 420,
    "flinders": 540, "franklin": 540,
    "wakefield": 660, "grote": 660,
    "angas": 770, "gouger": 770,
    "carrington": 850, "sturt": 850,
    "halifax": 905, "gilbert": 905,
    "gilles": 955, "wright": 955,
    "south terrace": 1000, "south tce": 1000,
}
# Ruas a LESTE de King William: o número cresce para o leste.
LESTE = {"rundle", "grenfell", "pirie", "flinders", "wakefield",
         "angas", "carrington", "halifax", "gilles"}
# Ruas a OESTE: o número cresce para o oeste.
OESTE = {"hindley", "currie", "waymouth", "franklin", "grote",
         "gouger", "sturt", "gilbert", "wright"}

TRANSVERSAIS = {  # ruas norte-sul → distância a leste da West Terrace
    "west terrace": 0, "west tce": 0,
    "morphett": 250, "light square": 300, "light sq": 300,
    "king william": 500,
    "gawler place": 600, "gawler pl": 600,
    "pulteney": 700, "frome": 800, "hutt": 840,
    "east terrace": 1000, "east tce": 1000,
    "victoria square": 500, "victoria sq": 500,
}

RE_END = re.compile(
    r"(\d[\d\-/]*)\s+([A-Z][A-Za-z'\. ]*?)\s*"
    r"(St|Street|Tce|Terrace|Rd|Road|Sq|Square|Place|Pl|Mall|Pde|Parade)\b", re.I)


def coordenada(endereco: str) -> tuple[float, float] | None:
    """(x, y) em metros no esquema, ou None se não for uma rua da grade."""
    if not re.search(r"\bSA 5000\b", endereco or ""):
        return None
    for m in RE_END.finditer(endereco):
        numero = int(re.match(r"\d+", m.group(1)).group(0))
        rua = re.sub(r"\s+", " ", m.group(2)).strip().lower()
        rua = re.sub(r"^(north|south|east|west)\s+(?=terrace|tce)", r"\1 ", rua)

        if rua in CORREDORES:
            y = CORREDORES[rua]
            base = rua.split()[0]
            if base in LESTE:
                x = 500 + min(numero * 2.4, 490)
            elif base in OESTE:
                x = 500 - min(numero * 2.4, 490)
            else:                      # North/South Terrace: número cresce a leste
                x = min(numero * 1.6, 990)
            return (x, y)

        if rua in TRANSVERSAIS or rua.replace(" street", "") in TRANSVERSAIS:
            x = TRANSVERSAIS.get(rua, TRANSVERSAIS.get(rua.replace(" street", ""), 500))
            return (x, min(numero * 2.2, 990))
    return None


# ── Janela de visita, por setor. Norma do ramo, não horário da loja ──
RE_PADARIA = re.compile(r"baker|padaria|brumby|banjo|p[aã]o|bread|patisserie", re.I)

JANELAS = {
    "manha": ("9h–11h30", "manhã"),
    "tarde": ("14h–16h", "tarde"),
    "online": ("não bater na porta", "online"),
}


def janela(reg: dict) -> tuple[str, str]:
    """(chave da janela, por que) para um empregador."""
    setor = reg["setor"]
    cat = (reg.get("categoria") or "").lower()
    nome = reg["empregador"]

    if setor == "Saúde e aged care":
        return "online", ("Hospital e casa de repouso não recebem currículo na porta: "
                          "exigem police check e worker screening, e tudo entra pelo portal.")
    if setor == "Armazém e logística":
        if "aplicativo" in cat:
            return "online", ("É cadastro em aplicativo. E este em particular exige "
                              "carta australiana e carro — não serve para você.")
        if "agência" in cat:
            return "manha", ("Agência de labour hire fecha a escala do dia cedo. Ligue "
                             "às 8h e apareça entre 9h e 11h — telefone funciona melhor "
                             "que formulário aqui.")
        return "manha", ("Armazém abre cedo e o encarregado está no chão de manhã. "
                         "Depois das 11h ele some para dentro da operação.")
    if setor == "Escritório":
        if "games" in cat or "edtech" in cat or "animação" in cat:
            return "online", ("Estúdio pequeno não recebe visita. É e-mail direto com "
                              "portfólio, e o portfólio é que abre a porta.")
        if "executive search" in cat:
            return "online", ("Boutique de search de 5 pessoas não tem recepção. "
                              "E-mail direto ao sócio, com o seu trabalho anexado.")
        return "manha", ("Agência de recrutamento faz triagem de manhã. Chegue entre "
                         "10h e 11h30: passou o e-mail da abertura, ainda não é almoço.")
    if setor == "Hotéis e eventos":
        if "agência" in cat or "plataforma" in cat or "catering" in cat:
            return "online", ("É cadastro em plataforma ou talent pool. Ir até lá não "
                              "adianta — o perfil online é que gera o turno.")
        return "manha", ("Housekeeping fecha a escala depois do check-out. Entre 10h e "
                         "11h30 a governanta está no prédio e já sabe quem faltou.")
    if RE_PADARIA.search(nome) or RE_PADARIA.search(cat):
        return "manha", ("O turno da padaria começa às 4h. Às 9h o gerente já está há "
                         "cinco horas na loja e o rush do café da manhã passou.")
    if setor == "Supermercados e varejo":
        return "manha", ("Gerente de loja faz o giro de manhã. Entre 9h e 11h em dia de "
                         "semana ele está no chão e a loja está vazia. Nunca no sábado.")
    if setor == "Cafés independentes":
        return "tarde", ("Entre 14h e 16h o rush do almoço acabou. Vá às 14h, não às "
                         "15h50: muito café de Adelaide fecha entre 15h e 16h.")
    if setor == "Redes de restaurante":
        return "tarde", ("Entre 14h30 e 16h30 é o vão entre almoço e jantar — a única "
                         "hora do dia em que o gerente consegue parar para te ouvir.")
    return "manha", "Horário comercial, fora do pico."


def main() -> None:
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak3"))

    i = s.find('[{"setor"')
    prof = 0
    for j in range(i, len(s)):
        if s[j] == "[":
            prof += 1
        elif s[j] == "]":
            prof -= 1
            if prof == 0:
                break
    dados = json.loads(s[i:j + 1])

    plotados = 0
    for idx, reg in enumerate(dados):
        reg["id"] = idx
        xy = coordenada(reg.get("endereco", ""))
        chave, porque = janela(reg)
        reg["jan"] = chave
        reg["jpq"] = porque
        if xy:
            reg["x"] = round(xy[0])
            reg["y"] = round(xy[1])
            plotados += 1

    s = s[:i] + json.dumps(dados, ensure_ascii=False) + s[j + 1:]
    ARQ.write_text(s, encoding="utf-8")

    from collections import Counter
    print(f"{plotados} de {len(dados)} registros posicionados no esquema do centro")
    print("por janela:", dict(Counter(r["jan"] for r in dados)))
    print("por janela, só os do mapa:",
          dict(Counter(r["jan"] for r in dados if "x" in r)))
    # confere âncoras conhecidas
    for nome in ("Stanton Chase Adelaide", "Mighty Kingdom", "ibis Adelaide"):
        r = next((x for x in dados if x["empregador"] == nome), None)
        if r:
            print(f"  {nome:24} {r.get('x','—'):>4},{r.get('y','—'):>4}  "
                  f"{r['endereco'][:46]}")


if __name__ == "__main__":
    main()
