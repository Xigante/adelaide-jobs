"""Registra os empregadores novos no material consolidado de Adelaide.

Tudo aqui foi verificado em 27/08/2026. Onde a verificação falhou, o
campo diz "NÃO confirmado" — o material já marca esses registros com um
aviso na tela, e é melhor um campo vazio que um endereço inventado.
"""
import json
import pathlib
import re
import shutil
from datetime import date

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")

# ── Setores novos ───────────────────────────────────────────────────
# Nenhum dos quatro setores existentes cobria hotel, evento ou aged
# care — e é exatamente onde está o housekeeping, a função de maior
# nota no primeiro relatório do coletor (87 pontos, Avani).
SETORES_NOVOS = {"Hotéis e eventos": 5, "Saúde e aged care": 6}
CORES_NOVAS = {"--s5": ("#8b5cf6", "#7c4ddb"), "--s6": ("#0e9d9d", "#0b8686")}

C = "Casual, Hospitality Award MA000009"
AC = "Casual, Aged Care Award MA000018"


def r(**kw):
    base = dict(setor="", empregador="", unidade="", categoria="", regiao="",
                chance="Média", chance2="Média-Alta", funcao="", ingles="",
                como="", portal="", endereco="", piso="", dica="", fonte="")
    base.update(kw)
    return base


NOVOS = [
    # ══ HOTÉIS E EVENTOS ═════════════════════════════════════════════
    r(setor="Hotéis e eventos", empregador="Adelaide Venue Management",
      unidade="Convention Centre, Entertainment Centre, Coopers Stadium",
      categoria="Eventos e centros de convenção", regiao="North Terrace / Hindmarsh",
      chance="Alta", chance2="Alta",
      funcao="Housekeeping – Cleaner · Uniform Attendant · Event Security (casual)",
      ingles="Básico basta em housekeeping e uniform",
      como="Online + talent pool aberto",
      portal="https://adelaideconventioncentre.jobs.subscribe-hr.com",
      endereco="Adelaide Convention Centre, North Terrace, Adelaide SA 5000",
      piso=C,
      dica="A MELHOR porta de entrada desta lista. Tem uma vaga permanente "
           "'Expression of Interest – Casual Event & Hospitality' para quem não "
           "vê vaga aberta na sua área: você se cadastra e eles chamam quando "
           "tem evento. Operam três locais, então o volume de turno é grande. "
           "Também fazem traineeship Certificate III em Hospitality.",
      fonte="Portal oficial (Subscribe-HR)"),

    r(setor="Hotéis e eventos", empregador="Adelaide Oval", unidade="Oval Hotel",
      categoria="Estádio e hotel", regiao="North Adelaide",
      chance="Alta", chance2="Alta",
      funcao="Food & Beverage Attendant · Barista · cozinha · front of house",
      ingles="Intermediário no salão; básico na cozinha",
      como="Online (e também pela Pinnacle People)",
      portal="https://careers.adelaideoval.com.au",
      endereco="War Memorial Drive, North Adelaide SA 5006", piso=C,
      dica="Contrata cerca de 1.200 casuais por temporada, uns 500 anunciados ao "
           "público. DUAS PORTAS para o mesmo lugar: candidatar-se direto, e "
           "cadastrar-se na Pinnacle People, que recruta o F&B casual deles. "
           "Faça as duas. Dia de jogo é turno garantido.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="SkyCity Adelaide", unidade="Cassino + hotel Eos",
      categoria="Cassino e hotel", regiao="North Terrace",
      chance="Média", chance2="Média-Alta",
      funcao="Housekeeping do Eos · F&B Attendant · In-room Dining",
      ingles="Intermediário", como="Online",
      portal="https://skycityadelaide.com.au/about-us/work-at-skycity/",
      endereco="North Terrace, Adelaide SA 5001 (edifício da Adelaide Railway Station) "
               "— número de rua NÃO confirmado",
      piso=C,
      dica="1.300 funcionários e cerca de 200 tipos de função. Está no CBD, colado "
           "na estação. ATENÇÃO: 'gaming' aqui é cassino, não jogos digitais — não "
           "confunda a vaga. O portal de vagas bloqueia robô, então não dá para "
           "acompanhar automaticamente: entre no site à mão uma vez por semana.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="National Wine Centre of Australia",
      unidade="", categoria="Eventos e restaurante", regiao="Botanic / Hackney",
      chance="Média", chance2="Média-Alta",
      funcao="F&B e eventos (candidatura para futuras oportunidades)",
      ingles="Intermediário", como="Online, com 'Apply for future opportunities'",
      portal="https://www.nationalwinecentre.com.au/careers",
      endereco="Esquina de Botanic Road com Hackney Road, Adelaide SA 5000", piso=C,
      dica="Sem vaga de entrada aberta na checagem, mas TEM cadastro para futuras "
           "oportunidades — use. Fica a 15 min a pé do ILSC, do outro lado do "
           "Jardim Botânico. O formulário pede certificado RSA: fazer o RSA online "
           "custa pouco e destranca todo o setor de bebida.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="ahs services group",
      unidade="Escritório de SA em Hilton", categoria="Terceirizada de housekeeping",
      regiao="Hilton", chance="Alta", chance2="Alta",
      funcao="Room Attendant · Houseperson · Public Area Attendant",
      ingles="Básico — é o exemplo clássico de vaga sem atendimento",
      como="Online, criando perfil no portal (ou por telefone)",
      portal="https://www.ahsservicesgroup.com.au/jobs",
      endereco="Level 1, 78 Sir Donald Bradman Drive, Hilton SA 5033 · 1800 026 036",
      piso=C,
      dica="Housekeeping terceirizado é o NEGÓCIO deles, não um departamento: eles "
           "colocam gente nos hotéis de Adelaide inteiros. Um cadastro só vale por "
           "vários hotéis. Era 'ahs hospitality', mudou de nome — se achar o nome "
           "antigo em algum lugar, é a mesma empresa.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="Pullman Adelaide", unidade="Grupo Accor",
      categoria="Hotel 5 estrelas", regiao="Hindmarsh Square",
      chance="Média-Alta", chance2="Alta",
      funcao="Room Attendant / housekeeping",
      ingles="Básico em housekeeping", como="Online, portal global da Accor",
      portal="https://careers.accor.com",
      endereco="16 Hindmarsh Square, Adelaide SA 5000", piso=C,
      dica="8 min a pé do ILSC. Vaga de Room Attendant confirmada no portal da "
           "Accor. Como é portal global, filtre por Adelaide — a Accor tem ibis, "
           "Novotel, Mercure e Sofitel na cidade e um cadastro serve para todos.",
      fonte="Portal Accor"),

    r(setor="Hotéis e eventos", empregador="ibis Adelaide", unidade="Grupo Accor",
      categoria="Hotel", regiao="Grenfell Street",
      chance="Média-Alta", chance2="Alta",
      funcao="Housekeeping / Room Attendant · Receptionist · F&B",
      ingles="Básico em housekeeping; bom na recepção",
      como="Online, portal global da Accor", portal="https://careers.accor.com",
      endereco="122 Grenfell Street, Adelaide SA 5000", piso=C,
      dica="Fica a 200 metros do ILSC — é o empregador mais perto da sua escola "
           "neste material. CUIDADO: o link de carreiras no site do próprio hotel "
           "(jobsataccor.com.au) foi sequestrado e leva a um domínio sem relação "
           "com a Accor. Use só careers.accor.com.",
      fonte="Site oficial + portal Accor"),

    r(setor="Hotéis e eventos", empregador="Rydges South Park Adelaide", unidade="Grupo EVT",
      categoria="Hotel", regiao="South Terrace",
      chance="Média", chance2="Média-Alta",
      funcao="Housekeeping · Houseperson · Public Area Attendant · F&B",
      ingles="Básico em housekeeping", como="Online",
      portal="NÃO confirmado — evt.com/careers dá erro 404",
      endereco="1 South Terrace, Adelaide SA 5000", piso=C,
      dica="ATENÇÃO, dois hotéis com nome parecido: o 'Rydges Pit Lane' NÃO fica em "
           "Adelaide, fica em Tailem Bend, a 1 hora de carro, dentro do autódromo. "
           "Sem carro é inviável. O Rydges do centro é este, o South Park, na esquina "
           "de South com West Terrace, 15 min a pé do ILSC.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="Sidekicker", unidade="Plataforma, sem escritório",
      categoria="Agência de turno por aplicativo", regiao="Adelaide (100% online)",
      chance="Alta", chance2="Alta",
      funcao="Kitchen Hand · Catering Assistant · Barista · Bartender · montagem de evento",
      ingles="Básico para cozinha e montagem", como="Cadastro 100% online no app",
      portal="https://app.sidekicker.com/worker/register/sidekicker/",
      endereco="Sem escritório físico — não é omissão, a empresa não tem atendimento presencial",
      piso=C,
      dica="A via mais rápida para o PRIMEIRO turno de todas as deste material: "
           "cadastro online, aprovação de perfil, e daí você escolhe turno pelo "
           "aplicativo. Faz staffing de estádio, convenção e evento em Adelaide. "
           "Não dá para coletar automaticamente (é marketplace fechado), então "
           "cadastre-se na primeira semana e deixe o app instalado.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="Pinnacle People", unidade="",
      categoria="Agência de hospitalidade e eventos", regiao="Gilles Street",
      chance="Alta", chance2="Alta",
      funcao="Turno casual de hospitalidade e eventos, incluindo o Adelaide Oval",
      ingles="Intermediário no salão; básico na cozinha",
      como="Talent pool — 'Join our talent'",
      portal="https://www.pinnaclepeople.com.au/join-our-talent/",
      endereco="Unit 6, 181 Gilles Street, Adelaide SA 5000 · 1300 746 625", piso=C,
      dica="É a agência que recruta o F&B casual do Adelaide Oval — tem até portal "
           "próprio para isso (aojobs.pinnaclepeople.com.au). Entrar no talent pool "
           "rende turno recorrente sem candidatura nova a cada vez. Fica a 12 min a "
           "pé do ILSC, dá para ir entregar o CV em pessoa.",
      fonte="Site oficial"),

    r(setor="Hotéis e eventos", empregador="Cater Care", unidade="Escritório de SA",
      categoria="Catering institucional", regiao="Richmond / Keswick",
      chance="Média", chance2="Média-Alta",
      funcao="Catering Assistant", ingles="Básico", como="Online, criando conta",
      portal="https://catercare.elmotalent.com.au/careers/default/jobs",
      endereco="209 Richmond Road, Richmond SA 5033 — CONFIRMAR: o próprio site diz "
               "em outro lugar '82 Richmond Road, Keswick SA 5035'",
      piso=C,
      dica="LIGUE ANTES DE IR: o site da empresa se contradiz sobre o endereço e o "
           "telefone publicado tem prefixo de Perth. Está no material porque faz "
           "catering de escola, hospital e mina — volume alto de assistente de "
           "cozinha. Na checagem, a única vaga de Adelaide era de chef FIFO.",
      fonte="Site oficial (com inconsistência)"),

    r(setor="Hotéis e eventos", empregador="Journey Beyond", unidade="Monarto Safari Resort",
      categoria="Resort", regiao="Monarto — 70 km de Adelaide",
      chance="Baixa", chance2="Baixa",
      funcao="Housekeeping Attendant (talent pool aberto)",
      ingles="Básico", como="Talent pool formal, via Workable",
      portal="https://apply.workable.com/journey-beyond/",
      endereco="63 Monarto Road, Monarto SA 5254", piso=C,
      dica="FICA LONGE: 70 km a leste de Adelaide, perto de Murray Bridge. Sem carro "
           "não dá para ir e voltar todo dia, e a vaga pressupõe morar na região. "
           "Está aqui só porque tem talent pool formal aberto de housekeeping — "
           "guarde para o caso de você conseguir carta e carro, não para agora.",
      fonte="Portal Workable"),

    # ══ SAÚDE E AGED CARE ════════════════════════════════════════════
    r(setor="Saúde e aged care", empregador="Southern Cross Care", unidade="SA, NT & VIC",
      categoria="Aged care", regiao="Glenside",
      chance="Alta", chance2="Alta",
      funcao="Food Services Assistant · Cleaner · Domestic Assistant",
      ingles="Básico — as três funções são back of house",
      como="Online", portal="https://careers.southerncrosscare.com.au/jobs/search",
      endereco="Peter Taylor House, 25 Conyngham Street, Glenside SA (CEP não publicado)",
      piso=AC,
      dica="As três funções de entrada estão listadas com esse nome no portal deles, "
           "confirmado. Aged care é o setor que mais cresce em SA e a barra de inglês "
           "em cozinha e limpeza é baixa. O turno costuma ser de manhã cedo ou à "
           "tarde, o que combina com aula.",
      fonte="Portal oficial (PageUp)"),

    r(setor="Saúde e aged care", empregador="Helping Hand", unidade="",
      categoria="Aged care", regiao="Hindmarsh",
      chance="Alta", chance2="Alta",
      funcao="Hotel Services Assistant · Lifestyle Assistant",
      ingles="Básico", como="Online",
      portal="https://www.helpinghand.org.au/careers/job-vacancies/",
      endereco="180 Port Road, Hindmarsh SA 5007 · 1300 653 600", piso=AC,
      dica="'Hotel Services Assistant' é o nome australiano para quem faz limpeza e "
           "serviço de refeição dentro de casa de repouso — está citado nominalmente "
           "na página deles. O processo tem checagem de referência e worker screening "
           "check, então comece cedo: a papelada leva semanas.",
      fonte="Site oficial"),

    r(setor="Saúde e aged care", empregador="ACH Group", unidade="",
      categoria="Aged care", regiao="Mile End",
      chance="Alta", chance2="Alta",
      funcao="Residential and Community Cleaner · Catering Assistant",
      ingles="Básico", como="Online",
      portal="https://achgroup.org.au/work-with-us/current-opportunities/",
      endereco="22 Henley Beach Road, Mile End SA 5031", piso=AC,
      dica="Tem uma categoria inteira chamada 'Hospitality and Domestic' no portal, "
           "com limpeza e assistente de cozinha. Mile End é logo a oeste do CBD, "
           "acessível de ônibus. As vagas deles aparecem no SEEK, então o alerta de "
           "e-mail do SEEK pega essa empresa também.",
      fonte="Site oficial"),

    r(setor="Saúde e aged care", empregador="Calvary Adelaide Hospital",
      unidade="Calvary Health Care", categoria="Hospital privado", regiao="Angas Street",
      chance="Média", chance2="Média-Alta",
      funcao="Hospitality dentro do hospital (limpeza, cozinha, ala)",
      ingles="Básico", como="Online, criando conta",
      portal="https://careers.calvarycare.org.au/jobs/search",
      endereco="120 Angas Street, Adelaide SA 5000", piso=AC,
      dica="É o maior hospital privado de SA e fica a 10 min a pé do ILSC. O portal "
           "tem categoria 'Hospitality', mas na checagem as vagas de Adelaide eram "
           "de enfermagem — as de hotel services aparecem e somem rápido, então vale "
           "olhar toda semana. 221 vagas no grupo inteiro.",
      fonte="Portal oficial (PageUp)"),

    # ══ ESCRITÓRIO — games e tech, a formação dele ═══════════════════
    r(setor="Escritório", empregador="Tantalus South", unidade="Keywords Studios",
      categoria="Games — maior estúdio de Adelaide", regiao="Gawler Place",
      chance="Baixa", chance2="Média",
      funcao="QA / games tester é a porta de entrada típica em estúdio Keywords",
      ingles="Escrito bom; falado intermediário",
      como="Online, portal global da Keywords",
      portal="https://www.keywordsstudios.com/en/careers/browse-careers/",
      endereco="Gawler Place, Adelaide — número e andar NÃO confirmados", piso="",
      dica="O maior empregador de games de Adelaide, e ainda assim são 21 pessoas com "
           "meta de 50. Abriu em 2023 atraído pelo incentivo fiscal do estado. Fazem "
           "port e co-desenvolvimento de AAA. O portal é global: filtre por Australia, "
           "porque a maioria das vagas listadas é de outros países.",
      fonte="Site oficial + governo de SA"),

    r(setor="Escritório", empregador="Mighty Kingdom", unidade="Game Plus",
      categoria="Games — mobile e work-for-hire", regiao="Pirie Street",
      chance="Baixa", chance2="Baixa",
      funcao="Expressão de interesse; playtester por formulário separado",
      ingles="Escrito bom", como="Expressão de interesse online",
      portal="https://www.mightykingdom.com/careers",
      endereco="Game Plus, Level 2, 44 Pirie Street, Adelaide SA 5000", piso="",
      dica="Fica no MESMO QUARTEIRÃO da Stanton Chase (63 Pirie St), 6 min do ILSC. "
           "Era a âncora do setor, mas demitiu 40% do quadro em fev/2025 e hoje só "
           "aceita expressão de interesse — estágio suspenso. Monitore, não conte "
           "com. O prédio 'Game Plus' é um hub de games: vale conhecer pelo "
           "networking, não pela vaga.",
      fonte="Site oficial"),

    r(setor="Escritório", empregador="Makers Empire", unidade="",
      categoria="EdTech — 3D para escolas", regiao="Grote Street",
      chance="Baixa", chance2="Média",
      funcao="Desenvolvimento e design (vagas históricas são de experiente)",
      ingles="Escrito bom", como="Contato direto pelo formulário do site",
      portal="NÃO confirmado — não existe página de carreiras; as vagas saem como "
             "post no blog deles",
      endereco="Level 1, 109 Grote Street, Adelaide SA 5000", piso="",
      dica="Fica a 10 min a pé do ILSC, na mesma rua do Central Market. Dos poucos "
           "de Adelaide com produto e receita recorrente, então contrata de forma "
           "mais previsível que estúdio de games puro. Sem página de carreiras: "
           "acompanhe o blog do site ou mande e-mail direto com portfólio.",
      fonte="Site oficial"),

    r(setor="Escritório", empregador="Monkeystack", unidade="Adelaide Studios",
      categoria="Animação, serious games e simulação", regiao="Glenside",
      chance="Muito baixa", chance2="Baixa",
      funcao="Nenhuma de entrada — declaram isso por escrito",
      ingles="Escrito bom", como="Sem processo formal; acompanhar as redes sociais",
      portal="https://monkeystack.com.au/careers/",
      endereco="Adelaide Studios, 1 Mulberry Road, Glenside SA 5065", piso="",
      dica="A página de carreiras diz textualmente que NÃO oferecem estágio nem work "
           "experience. Está no material para você não perder tempo tentando. Parte "
           "do trabalho deles é para defesa e governo, o que traz a exigência de "
           "cidadania australiana.",
      fonte="Site oficial"),
]


def main() -> None:
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak"))

    # ── 1. o array DATA ─────────────────────────────────────────────
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
    antes = len(dados)

    ja_tem = {(d["empregador"], d.get("unidade", "")) for d in dados}
    novos = [n for n in NOVOS if (n["empregador"], n["unidade"]) not in ja_tem]
    dados.extend(novos)

    s = s[:i] + json.dumps(dados, ensure_ascii=False) + s[j + 1:]

    # ── 2. SLOTS ganha os dois setores novos ────────────────────────
    velho = '{"Supermercados e varejo": 1, "Redes de restaurante": 2, "Cafés independentes": 3, "Escritório": 4}'
    if velho not in s:
        raise SystemExit("não achei SLOTS — o arquivo mudou de forma")
    slots = json.loads(velho)
    slots.update(SETORES_NOVOS)
    s = s.replace(velho, json.dumps(slots, ensure_ascii=False), 1)

    # ── 3. cores --s5 e --s6, nos dois temas ────────────────────────
    # O card usa border-left-color:var(--s{SLOTS[setor]}). Sem a
    # variável, a borda some e o setor novo fica invisível na tela.
    for var, (claro, escuro) in CORES_NOVAS.items():
        s = s.replace("--s4:#eda100", f"--s4:#eda100;{var}:{claro}")
        s = s.replace("--s4:#c98500", f"--s4:#c98500;{var}:{escuro}")

    ARQ.write_text(s, encoding="utf-8")
    print(f"registros: {antes} → {len(dados)}  (+{len(novos)})")
    if len(novos) != len(NOVOS):
        pulados = [n["empregador"] for n in NOVOS if n not in novos]
        print("já existiam, pulados:", pulados)
    for n in novos:
        print(f"  + [{n['setor']}] {n['empregador']}")


if __name__ == "__main__":
    main()
