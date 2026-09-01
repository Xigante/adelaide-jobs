"""As 35 fichas novas, curadas com pesquisa verificada em 30/08/2026.

O que a pesquisa CORRIGIU do que a Adzuna dizia — e isto é metade do
valor deste arquivo:

  Resthaven "Wellbeing Assistant"   → não existe. É Housekeeping
                                      Services Assistant.
  Compass "Sous Chef"               → não é vaga de entrada. É Catering
                                      Assistant / Utility Attendant.
  ALH "Sous Chef"                   → idem. É Bar / F&B Attendant.
  Infinite Aged Care "Blair Athol"  → não existe unidade lá. É Kilburn.
  Labourforce "North Plympton"      → é o local de trabalho, não a
                                      agência. A agência é Mawson Lakes.
  OPSM 10 vagas                     → nenhuma é OPSM. São Sunglass Hut.
  HR Partners "production worker"   → é anúncio da Randstad, marca irmã.
  SeaLink "Adelaide"                → o trabalho é em Mannum, a 85 km.
  Amazon Flex 66 vagas              → exige carta australiana e carro.
  Canva "Adelaide"                  → é co-working, não escritório.

Campos derivados dos DADOS REAIS do banco (não são chute): a chance vem
da nota mediana das vagas daquele empregador; o inglês, da dimensão que
o extrator tirou dos anúncios.
"""
import json
import pathlib
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")

SETOR_NOVO = {"Armazém e logística": 7}
COR_NOVA = ("--s7", "#b45309", "#e0a955")

AC = "Casual, Aged Care Award MA000018"
HO = "Casual, Hospitality Award MA000009"
VA = "Casual, General Retail Award MA000004"
CL = "Casual, Cleaning Services Award MA000022"


def r(**kw):
    base = dict(setor="", empregador="", unidade="", categoria="", regiao="",
                chance="Média", chance2="Média-Alta", funcao="", ingles="",
                como="", portal="", endereco="", piso="", dica="", fonte="Site oficial")
    base.update(kw)
    return base


NOVOS = [
    # ══ SAÚDE E AGED CARE ════════════════════════════════════════════
    r(setor="Saúde e aged care", empregador="Estia Health", categoria="Aged care",
      regiao="Parkside", chance="Alta", chance2="Alta",
      funcao="Food Services Assistant", ingles="Básico — é cozinha, não atendimento",
      como="Online (Workday)",
      portal="https://estiahealth.wd105.myworkdayjobs.com/Estia_Health_Careers",
      endereco="Estia Health Parkside, 17 Robsart Street, Parkside SA 5063 "
               "(o escritório de RH em SA não é publicado)",
      piso=AC,
      dica="40 vagas ativas, mais que qualquer outro empregador de aged care da "
           "cidade. Mire nas casas do centro — Parkside, Myrtle Bank, Toorak "
           "Gardens — que têm ônibus do CBD. A primeira entrevista é por MS Teams, "
           "então dá para preparar as respostas escritas antes: vantagem real com "
           "inglês A2. Desde 01/11/2025 aged care exige police check ou NDIS check."),

    r(setor="Saúde e aged care", empregador="Resthaven", categoria="Aged care",
      regiao="Wayville", chance="Alta", chance2="Alta",
      funcao="Housekeeping Services Assistant", ingles="Básico",
      como="Online + expressão de interesse permanente",
      portal="https://careers.resthaven.asn.au/jobs/search",
      endereco="6 Bartley Crescent, Wayville SA 5034 · (08) 8373 9000", piso=AC,
      dica="Candidate-se à vaga permanente 'Housekeeping Services Assistants – All "
           "Areas': ela fica aberta o ano todo e cobre a rede inteira, em vez de "
           "você esperar abrir vaga numa casa específica. Cuidado: a Adzuna diz "
           "'Wellbeing Assistant' e esse cargo não existe lá. Dúvidas: "
           "careers@resthaven.asn.au"),

    r(setor="Saúde e aged care", empregador="Eldercare", categoria="Aged care",
      regiao="Eastwood", chance="Alta", chance2="Alta",
      funcao="Hospitality Assistant", ingles="Básico",
      como="Online (applynow) + talent pool",
      portal="https://www.eldercare.net.au/careers/current-employment-opportunities",
      endereco="247 Fullarton Road, Eastwood SA 5063 · (08) 8291 1000", piso=AC,
      dica="FILTRE PELO LOCAL antes de aplicar: as vagas de Hospitality Assistant "
           "que apareceram eram em Mount Barker e na Península de Yorke, a 2,5 a 3 "
           "horas de carro. Os sites metropolitanos são Eastwood, Wayville, "
           "Glengowrie, Payneham e Seaford."),

    r(setor="Saúde e aged care", empregador="Opal HealthCare", categoria="Aged care",
      regiao="Everard Park", chance="Alta", chance2="Alta",
      funcao="General Services Officer (limpeza, lavanderia, housekeeping)",
      ingles="Básico", como="Online (Dayforce)",
      portal="https://globalaus241.dayforcehcm.com/CandidatePortal/en-AU/opalhealthcare",
      endereco="Opal Everard Park, 34 Norman Terrace, Everard Park SA 5035 "
               "(escritório de RH em SA não publicado)",
      piso=AC,
      dica="O ÚNICO desta lista que declara por escrito que ORGANIZA O POLICE CHECK "
           "para você. Isso economiza semanas de espera e o custo. Everard Park tem "
           "tram direto do CBD. O processo inclui exame médico pré-admissional."),

    r(setor="Saúde e aged care", empregador="AnglicareSA", categoria="Aged care e serviços comunitários",
      regiao="Hindmarsh", chance="Média", chance2="Média-Alta",
      funcao="Hospitality Worker (Casuals) — NÃO o Care Worker comunitário",
      ingles="Básico na hospitalidade", como="Online (LiveHire) + Talent Community",
      portal="https://www.livehire.com/careers/anglicaresa",
      endereco="Port Road, Hindmarsh SA 5007 — NÃO confirmado o número "
               "(fontes divergem entre 159 e 184). Ligue antes de ir.",
      piso=AC,
      dica="NÃO gaste tempo com 'Care Worker, Community Aged Care': o anúncio exige "
           "Certificate III, carta australiana, carro próprio segurado e, ao que "
           "tudo indica, cidadania ou PR. Vá direto na Hospitality Worker casual e "
           "entre na Talent Community."),

    r(setor="Saúde e aged care", empregador="Infinite Aged Care", unidade="infin8care",
      categoria="Aged care", regiao="Kilburn", chance="Alta", chance2="Alta",
      funcao="Hotel Services – Cleaner (também Servery e Laundry)",
      ingles="Básico", como="Online (LiveHire) + Talent Community",
      portal="https://www.livehire.com/careers/infin8care/jobs",
      endereco="The Churchill Retreat, 470 Churchill Rd, Kilburn SA 5084 — "
               "confirme por e-mail antes de ir",
      piso=AC,
      dica="A Adzuna diz 'Blair Athol' e a empresa NÃO tem unidade lá. Kilburn faz "
           "divisa com Blair Athol e dividem o CEP, então é quase certo que seja a "
           "Churchill Retreat — mas escreva para recruitment@infin8care.com.au "
           "confirmando, porque são 6 km ao norte do centro."),

    r(setor="Saúde e aged care", empregador="ECH Inc", categoria="Aged care e moradia assistida",
      regiao="Parkside", chance="Média", chance2="Média-Alta",
      funcao="Assisted Living Services Team Member",
      ingles="Básico", como="Online (Dayforce)",
      portal="https://jobs.dayforcehcm.com/en-AU/echinc/CANDIDATEPORTAL",
      endereco="174 Greenhill Road, Parkside SA 5063 · 1300 275 324", piso=AC,
      dica="Prefira as funções de site fixo às de visita domiciliar — 'home services' "
           "na Austrália quase sempre exige carro próprio. O escritório fica a 2 km "
           "do CBD, dá para ir a pé pela Greenhill Rd."),

    r(setor="Saúde e aged care", empregador="Central Adelaide Local Health Network",
      unidade="Royal Adelaide Hospital", categoria="Hospital público", regiao="Port Road, CBD",
      chance="Média-Alta", chance2="Alta",
      funcao="Patient Services Assistant (Candidate Pool) · Services Assistant (Casual Pool)",
      ingles="Básico", como="Online, pelo portal do SA Health — não tem portal próprio",
      portal="https://careers.sahealth.sa.gov.au",
      endereco="Royal Adelaide Hospital, Port Road, Adelaide SA 5000", piso=AC,
      dica="O RAH é o único empregador grande DENTRO do centro — você vai a pé de "
           "casa. Entre no 'Patient Services Assistant Candidate Pool' mesmo sem "
           "vaga aberta: o pool fica ativo por meses e chamam quando precisam. "
           "Exige police certificate e, em algumas funções, imunização antes da oferta."),

    r(setor="Saúde e aged care", empregador="Southern Adelaide Local Health Network",
      unidade="Flinders Medical Centre", categoria="Hospital público", regiao="Bedford Park",
      chance="Média", chance2="Média-Alta",
      funcao="Patient Services Assistant · Services Assistant (Casual Pool)",
      ingles="Básico", como="Online, pelo portal do SA Health",
      portal="https://careers.sahealth.sa.gov.au",
      endereco="Flinders Medical Centre, Flinders Drive, Bedford Park SA 5042", piso=AC,
      dica="12 km do centro, mas tem TREM DIRETO — linha Seaford/Flinders, com "
           "estação dentro do campus. Confira o horário do último trem antes de "
           "aceitar turno noturno."),

    r(setor="Saúde e aged care", empregador="Women's and Children's Health Network",
      unidade="Women's and Children's Hospital", categoria="Hospital público",
      regiao="North Adelaide", chance="Média", chance2="Média-Alta",
      funcao="Employment pools do SA Health", ingles="Básico",
      como="Online, pelo portal do SA Health + employment pools",
      portal="https://careers.sahealth.sa.gov.au",
      endereco="72 King William Road, North Adelaide SA 5006", piso=AC,
      dica="A BARREIRA MAIS PESADA dos três hospitais públicos: por ser hospital "
           "infantil exige Working with Children Check, que leva semanas. Comece o "
           "WWCC no DHS SA ANTES de aplicar. Em compensação, quem entra no pool fica "
           "ativo por 12 meses. Fica a 1 km do centro."),

    # ══ HOTÉIS E EVENTOS ═════════════════════════════════════════════
    r(setor="Hotéis e eventos", empregador="IHG Hotels & Resorts",
      unidade="6 hotéis em Adelaide", categoria="Rede de hotéis", regiao="CBD",
      chance="Alta", chance2="Alta",
      funcao="Steward (louça e limpeza de cozinha) · Food & Beverage Attendant",
      ingles="Steward quase não fala com hóspede — é a porta de entrada",
      como="Online, por hotel", portal="https://careers.ihg.com/en/search-and-apply/",
      endereco="InterContinental Adelaide, North Terrace, Adelaide SA 5000 · "
               "Crowne Plaza, 27 Frome St · Holiday Inn Express, 30 Blyth St · "
               "Hotel Indigo, 23-29 Market St · Mayfair, 45 King William St",
      piso=HO,
      dica="CINCO dos seis hotéis ficam no CBD, a pé de onde você vai morar. Cada "
           "hotel recruta separado: candidate-se ao mesmo cargo em vários. 'Steward' "
           "é o cargo onde o inglês pesa menos. Não existe voco em Adelaide."),

    r(setor="Hotéis e eventos", empregador="Accor", unidade="17 hotéis em Adelaide",
      categoria="Rede de hotéis", regiao="CBD", chance="Alta", chance2="Alta",
      funcao="Room Attendant / Housekeeping Attendant",
      ingles="Básico em housekeeping", como="Online, portal global",
      portal="https://careers.accor.com",
      endereco="Sofitel Adelaide, 108 Currie Street, Adelaide SA 5000 "
               "(os outros 16 hotéis não publicam rua na página do grupo)",
      piso=HO,
      dica="17 hotéis: Sofitel, Pullman, Playford, Watson, Peppers Waymouth, ibis, "
           "ibis Styles, quatro Mantra, dois BreakFree, Grosvenor, Adabco, Adelaide "
           "Rockford, Mount Lofty. Cada um recruta separado — cinco candidaturas "
           "valem mais que uma. O police clearance só é pedido DEPOIS da oferta, "
           "então não gaste dinheiro com isso agora."),

    r(setor="Hotéis e eventos", empregador="Adelaide Marriott Hotel",
      unidade="Marriott International", categoria="Hotel", regiao="King William St",
      chance="Média-Alta", chance2="Alta",
      funcao="Kitchen Steward", ingles="Steward: básico. Guest Service Agent: alto",
      como="Online", portal="https://careers.marriott.com/jobs",
      endereco="141 King William Street, Adelaide SA 5000 · +61 8 8451 3300", piso=HO,
      dica="É um hotel só em Adelaide, no prédio do antigo Correio — aberto em "
           "agosto de 2024. Concorrência alta. MAS: o Westin Adelaide está em obra "
           "com previsão para o fim de 2026, e pré-abertura de hotel é a MELHOR "
           "janela para quem não tem experiência local, porque contratam times "
           "inteiros de uma vez. Fique de olho."),

    r(setor="Hotéis e eventos", empregador="ALH Hotels", unidade="Endeavour Group",
      categoria="Rede de pubs", regiao="East End", chance="Média-Alta", chance2="Alta",
      funcao="Bar Attendant · Food & Beverage Attendant (NÃO Sous Chef)",
      ingles="Intermediário no bar", como="Online + presencial",
      portal="https://endeavourgroupcareers.com.au/careers-at-alh-hotels",
      endereco="The Laneway Social, 27-29 Ebenezer Place, Adelaide SA 5000",
      piso=HO,
      dica="O Laneway Social é o ÚNICO ALH no centro — dá para ir a pé, entregar "
           "currículo entre 14h e 16h e perguntar pelo venue manager. Os outros "
           "(Norwood, Ramsgate, Tower, Beach) exigem ônibus de 20 a 60 min. A Adzuna "
           "mostra 'Sous Chef', que não é vaga de entrada."),

    r(setor="Hotéis e eventos", empregador="Matthews Hospitality", categoria="Grupo de pubs familiar",
      regiao="Maylands", chance="Média-Alta", chance2="Alta",
      funcao="Funções de salão e cozinha nos pubs do grupo",
      ingles="Intermediário", como="Online + presencial",
      portal="https://www.matthewshospitality.com.au/jobs",
      endereco="Escritório: First Floor, 67 Phillis Street, Maylands SA 5069 · "
               "(08) 8130 4500. Windmill Hotel: 94 Main North Rd, Prospect SA 5082",
      piso=HO,
      dica="Grupo FAMILIAR de 9 pubs, e só 4 dão para chegar de Adelaide: Windmill "
           "(Prospect), Sussex (Walkerville), Maylands e Salisbury. Os outros 5 ficam "
           "em Clare, Whyalla e Mount Gambier, a centenas de quilômetros. Em empresa "
           "familiar, entregar currículo em mãos tem peso real — diferente das redes."),

    r(setor="Hotéis e eventos", empregador="Compass Group", categoria="Catering institucional",
      regiao="Grande Adelaide", chance="Alta", chance2="Alta",
      funcao="Catering Assistant · Utility Attendant · Cleaner (NÃO Sous Chef)",
      ingles="Básico", como="Online",
      portal="https://careers.compass-group.com.au/jobs/search",
      endereco="Escritório em SA NÃO confirmado (a empresa só publica a sede "
               "nacional, em NSW)",
      piso=HO,
      dica="Mire em Catering Assistant pela divisão Chartwells, que atende escolas: "
           "o anúncio deles destaca horário de segunda a sexta com folga nas férias "
           "escolares, o que encaixa com 48h/quinzena. EVITE as vagas de Roxby Downs "
           "e FIFO — 560 km e regime que não cabe no visto."),

    r(setor="Hotéis e eventos", empregador="ISS Facility Services", categoria="Facilities e limpeza",
      regiao="Marleston", chance="Média-Alta", chance2="Alta",
      funcao="Hospital Cleaner · Educational Cleaner · Food Service Assistant",
      ingles="Básico", como="Online",
      portal="https://careers.au.issworld.com/en/listing/",
      endereco="Marleston SA 5033 — rua e número NÃO confirmados", piso=CL,
      dica="ATENÇÃO: em set/2025 a ISS assinou contrato de facilities com o "
           "Ministério da Defesa cobrindo 85 locais em SA e WA — é por isso que "
           "aparecem tantas vagas 'Defence' em Adelaide, e essas exigem cidadania "
           "australiana. FILTRE por saúde e educação: Flinders Medical Centre, "
           "Repatriation Hospital, escolas e campus. Essas pedem police check e "
           "WWCC, que você consegue."),

    r(setor="Hotéis e eventos", empregador="City Facilities Management", unidade="City FM",
      categoria="Limpeza de supermercado", regiao="Grande Adelaide",
      chance="Alta", chance2="Alta",
      funcao="Casual Cleaner", ingles="Básico", como="Online (Dayforce)",
      portal="https://jobs.dayforcehcm.com/en-AU/cityfmaus/CANDIDATEPORTAL",
      endereco="Sem escritório em SA — a sede australiana é em Mulgrave, VIC",
      piso=CL,
      dica="'City FM' e 'City Facilities Management' são A MESMA EMPRESA — o "
           "agregador contou duas vezes. Eles fazem a limpeza das lojas da COLES, "
           "Kmart, Target e Bunnings, então é uma vaga por loja. OLHE O SUBÚRBIO "
           "antes de aplicar: pode ser um Coles em Elizabeth, a 1 h de trem. Turno "
           "de madrugada ou pós-fechamento, o que combina com aula de dia."),

    r(setor="Hotéis e eventos", empregador="Australian Green Clean", categoria="Limpeza comercial",
      regiao="Hindmarsh", chance="Alta", chance2="Alta",
      funcao="Commercial Cleaner (turnos de dia e de noite) · Event & Venue Cleaner",
      ingles="Básico", como="Online (Expr3ss — não exige currículo formatado)",
      portal="https://www.australiangreenclean.com.au/careers",
      endereco="39 Bacon Street, Hindmarsh SA 5007 · (08) 8229 7400", piso=CL,
      dica="A MELHOR APOSTA da lista para começar: empresa sul-australiana de "
           "família, 500 funcionários diretos, sede a 10 min do centro na linha do "
           "tram, e a candidatura é pelo Expr3ss, que não pede currículo formatado. "
           "A vaga do Royal Adelaide Show (setembro) é sazonal e costuma virar "
           "trabalho contínuo."),

    r(setor="Hotéis e eventos", empregador="LUXXE Outsourced Hotel Services",
      unidade="Little National Adelaide", categoria="Housekeeping terceirizado",
      regiao="North Terrace", chance="Alta", chance2="Alta",
      funcao="Housekeeping Room Attendant · Houseperson",
      ingles="Básico — Houseperson não fala com hóspede",
      como="Online (Expr3ss: 'No resume? No problem!')",
      portal="https://luxxe.expr3ss.com",
      endereco="Little National Adelaide, 100 North Terrace, Adelaide SA 5000 "
               "(a LUXXE não tem escritório em Adelaide; o trabalho é no hotel)",
      piso=HO,
      dica="A MELHOR JANELA DO MOMENTO, e é questão de timing: o Little National "
           "Adelaide abre em OUTUBRO DE 2026, umas semanas depois de você chegar. "
           "Pré-abertura de hotel monta a equipe inteira de housekeeping de uma vez "
           "e treina do zero — não podem exigir experiência local de todo mundo. "
           "North Terrace é a pé. Eles pedem 4 dias por semana: diga desde o início "
           "quantas horas você pode fazer, para não ser cortado depois."),

    r(setor="Hotéis e eventos", empregador="Lagardère AWPL", unidade="Adelaide Airport",
      categoria="Varejo e café de aeroporto", regiao="Adelaide Airport",
      chance="Média", chance2="Média-Alta",
      funcao="Cafe Assistant · Cafe Team Member", ingles="Intermediário",
      como="Online (PageUp)", portal="https://careers.pageuppeople.com/1121/cw/en/listing/",
      endereco="Adelaide Airport, 1 James Schofield Drive, Adelaide Airport SA 5950",
      piso=HO,
      dica="ATENÇÃO AO CUSTO DE ENTRADA: o anúncio exige RSA, Food Safety "
           "Certificate e capacidade de tirar o ASIC (crachá de segurança de "
           "aviação), que leva semanas e envolve checagem de antecedentes. Tirar o "
           "RSA online antes já resolve metade. Turno 14h-23h, ônibus JetBus do "
           "centro em 20 min."),

    r(setor="Hotéis e eventos", empregador="SeaLink South Australia", unidade="Kelsian Group",
      categoria="Turismo e ferry", regiao="Mannum e Cape Jervis — NÃO Adelaide",
      chance="Muito baixa", chance2="Baixa",
      funcao="Cabin Waiter / Galley Hand a bordo", ingles="Intermediário",
      como="Online (Expr3ss)", portal="https://kelsian.expr3ss.com",
      endereco="Sede: Level 3, 26 Flinders Street, Adelaide SA 5000 — mas o "
               "TRABALHO é em Mannum (85 km) e Cape Jervis (100 km)",
      piso=HO,
      dica="ARMADILHA DO AGREGADOR: as 12 vagas aparecem como 'Adelaide' porque a "
           "empresa é registrada aqui, mas o trabalho é a bordo do Murray Princess "
           "em Mannum e no ferry de Kangaroo Island. Sem carro, inviável. Está no "
           "material para você não perder tempo."),

    # ══ SUPERMERCADOS E VAREJO ═══════════════════════════════════════
    r(setor="Supermercados e varejo", empregador="OTR", unidade="Viva Energy",
      categoria="Rede de conveniência 24h", regiao="Brompton / Prospect",
      chance="Média-Alta", chance2="Alta",
      funcao="Team Member", ingles="Intermediário — é balcão",
      como="Online (Dayforce)",
      portal="https://jobs.dayforcehcm.com/en-AU/vivaenergyau/OTRSITE",
      endereco="Não há OTR no CBD. As mais perto: Brompton (73-77 Torrens Rd), "
               "Prospect (68-72 Prospect Rd), Croydon Park (207-209 Regency Rd)",
      piso=VA,
      dica="Comprada pela Viva Energy em 2024. Filtre pelas lojas de Brompton, "
           "Prospect e Croydon Park — 15 min de ônibus do centro. Loja de "
           "conveniência 24h combina com o teto de 48h/quinzena porque tem turno de "
           "madrugada. O processo inclui police clearance."),

    r(setor="Supermercados e varejo", empregador="Vili's Family Bakery",
      categoria="Produção de alimentos", regiao="Mile End South",
      chance="Alta", chance2="Alta",
      funcao="Bakery Production Roles · Kitchen Hands – Production Kitchen",
      ingles="Básico — produção, sem atendimento",
      como="Online, pelo SEEK (o anúncio manda aplicar por lá)",
      portal="https://www.seek.com.au/Vilis-Bakery-jobs",
      endereco="2–14 Manchester Street, Mile End South SA 5031 · (08) 8234 5711",
      piso=HO,
      dica="TURNOS CONFIRMADOS: dia 9h30–16h00, noite 15h30–09h00. O turno da noite "
           "rende adicional e deixa o dia livre para aula. O processo inclui exame "
           "médico pré-admissional com teste de drogas e álcool — saiba disso antes. "
           "Candidatura presencial não é documentada: use o SEEK. 3 km do centro, "
           "ônibus direto pela Henley Beach Rd."),

    r(setor="Supermercados e varejo", empregador="Spendless Shoes", categoria="Varejo de calçados",
      regiao="Gillman", chance="Média", chance2="Média-Alta",
      funcao="Casual Retail Sales Assistant", ingles="Intermediário",
      como="Online, em 3 etapas com vídeo opcional",
      portal="https://www.spendless.com.au/careers",
      endereco="25 Bedford Street, Gillman SA 5013 — só confirmado por diretório "
               "de terceiros, não pela empresa",
      piso=VA,
      dica="O site diz literalmente 'we hire the attitude and train the skills'. "
           "GRAVE O VÍDEO OPCIONAL: com inglês em evolução e sem experiência local, "
           "é onde você compensa o currículo — eles veem energia, não sotaque."),

    r(setor="Supermercados e varejo", empregador="adidas", categoria="Varejo esportivo",
      regiao="Rundle Mall", chance="Média", chance2="Média-Alta",
      funcao="Casual Retail Professional · Stockroom Specialist",
      ingles="Intermediário no salão; básico no estoque",
      como="Online, portal global",
      portal="https://careers.adidas-group.com/jobs",
      endereco="adidas Originals, 148 Rundle Mall, Adelaide SA 5000 · também "
               "Harbour Town, 727 Tapleys Hill Rd, West Beach SA 5024",
      piso=VA,
      dica="Está abrindo um Factory Outlet NOVO em Salisbury, e loja nova contrata "
           "equipe inteira de uma vez — saíram 5 vagas juntas. Mas Salisbury é longe. "
           "Para você, a vaga a pé é Casual Retail Professional na Originals da "
           "Rundle Mall. 'Stockroom Specialist' é a de menor exigência de inglês."),

    r(setor="Supermercados e varejo", empregador="Sunglass Hut", unidade="EssilorLuxottica",
      categoria="Varejo de óculos", regiao="Rundle Mall",
      chance="Média", chance2="Média-Alta",
      funcao="Retail Associate", ingles="Intermediário", como="Online",
      portal="https://careers.essilorluxottica.com/search/?locationsearch=AU",
      endereco="Rundle Mall, Adelaide SA 5000 · a OPSM fica no 71 Rundle Mall",
      piso=VA,
      dica="As '10 vagas da OPSM' que o agregador mostra são do grupo "
           "EssilorLuxottica inteiro, e na verdade TODAS as de Adelaide eram da "
           "Sunglass Hut. O alvo real é Retail Associate na Rundle Mall, 10 min a "
           "pé, com vaga de Christmas Casual já aberta."),

    r(setor="Supermercados e varejo", empregador="Salvos Stores", unidade="The Salvation Army",
      categoria="Varejo beneficente", regiao="Morphett Street",
      chance="Média-Alta", chance2="Alta",
      funcao="Loja (triagem de doações, caixa) — e VOLUNTARIADO",
      ingles="Básico", como="Online (Workday) — e portal de voluntariado separado",
      portal="https://salvationarmy.wd3.myworkdayjobs.com/Salvos",
      endereco="422 Morphett Street, Adelaide SA 5000 · (08) 8231 9779 — "
               "fonte única, confirme por telefone",
      piso=VA,
      dica="O CAMINHO REAL AQUI É O VOLUNTARIADO, num portal separado e muito menos "
           "concorrido: salvationarmy.wd3.myworkdayjobs.com/Volunteer. Algumas "
           "semanas de voluntariado na loja da Morphett Street viram a primeira "
           "referência australiana com telefone local — exatamente o que falta no "
           "seu currículo, e não conta nas 48h/quinzena."),

    # ══ ARMAZÉM E LOGÍSTICA ══════════════════════════════════════════
    r(setor="Armazém e logística", empregador="Symons Clark Logistics",
      categoria="Transporte e armazém", regiao="Port Adelaide",
      chance="Média", chance2="Média-Alta",
      funcao="Yard Hand – General Maintenance (o único sem licença exigida)",
      ingles="Básico", como="Online (Employment Hero)",
      portal="https://employmenthero.com/jobs/organisations/symons-clark-logistics/",
      endereco="13 Francis Street, Port Adelaide SA 5015", piso="Casual, Road Transport Award",
      dica="Das ~10 vagas, quase todas são motorista HC/MC ou mecânico. Sobram duas: "
           "Warehouse Forklift Operator, que exige licença de empilhadeira (curso "
           "curto e pago, mas vale para dezenas de empregadores), e Yard Hand, que "
           "provavelmente não exige nada. Port Adelaide tem trem direto, 25 min."),

    r(setor="Armazém e logística", empregador="Omni Recruit", categoria="Agência de armazém",
      regiao="Torrensville", chance="Média-Alta", chance2="Alta",
      funcao="Store person · Pick pack", ingles="Básico",
      como="Cadastro online + telefone",
      portal="https://www.omnirecruit.com.au/user-register/",
      endereco="Level 1/235 Henley Beach Road, Torrensville SA 5031 · 08 8257 6523",
      piso="Casual, conforme o cliente",
      dica="Fica no MESMO eixo da Henley Beach Rd que passa pela Vili's — dá para "
           "fazer os dois no mesmo dia, no mesmo ônibus. LIGUE antes: agência de "
           "labour hire responde muito melhor a telefone que a formulário."),

    r(setor="Armazém e logística", empregador="Labourforce", categoria="Agência de cadeia de suprimentos",
      regiao="Mawson Lakes", chance="Média", chance2="Média-Alta",
      funcao="Storeperson e operações de armazém", ingles="Básico",
      como="Online + presencial",
      portal="https://www.labourforce.com.au/find-jobs/",
      endereco="1/14–16 Hurtle Parade, Mawson Lakes SA — o site publica CEP 5039, "
               "mas Mawson Lakes é 5095. Confirme antes de ir.",
      piso="Casual, conforme o cliente",
      dica="'North Plympton' que aparece nos anúncios é o LOCAL DE TRABALHO, não a "
           "agência. O telefone 13 30 91 atende 24 horas — ligue antes de gastar a "
           "viagem, ainda mais com o CEP inconsistente no site deles. Mawson Lakes "
           "tem trem direto da estação central, 25 min."),

    r(setor="Armazém e logística", empregador="Amazon Flex", categoria="Entrega por aplicativo",
      regiao="Elizabeth Grove", chance="Muito baixa", chance2="Muito baixa",
      funcao="Delivery Partner — INVIÁVEL sem carta australiana e carro",
      ingles="Básico", como="Cadastro pelo aplicativo",
      portal="https://flex.amazon.com.au/",
      endereco="Sem escritório — é aplicativo", piso="Contratado independente (ABN)",
      dica="RISQUE DA LISTA. São 66 vagas e nenhuma serve: exige carta de motorista "
           "australiana COMPLETA (carta estrangeira não é aceita, provisória também "
           "não), veículo próprio de 4 portas, ABN e seguro. E mesmo se você tivesse: "
           "trabalho com ABN CONTA no teto de 48h/quinzena, e as horas do Flex são "
           "difíceis de documentar para o Home Affairs."),

    # ══ ESCRITÓRIO ═══════════════════════════════════════════════════
    r(setor="Escritório", empregador="Frontline Hospitality SA & NT",
      categoria="Agência de hospitalidade", regiao="Glenelg",
      chance="Média", chance2="Média-Alta",
      funcao="Cadastro de candidato — food & beverage casual", ingles="Intermediário",
      como="Cadastro online + visita presencial",
      portal="https://www.frontlinerecruitmentgroup.com/user-register/",
      endereco="Office G, Unit 29, 12/760 Anzac Highway, Glenelg SA 5045 · "
               "+61 8 8372 7861",
      piso=HO,
      dica="Glenelg é o fim da linha do TRAM que sai da King William — 30 min "
           "direto do centro, sem baldeação. Vá numa terça ou quarta de manhã com "
           "currículo impresso e peça vaga de food & beverage attendant casual, não "
           "de cozinha. Um cadastro só cobre Hospitality e Retail do grupo."),

    r(setor="Escritório", empregador="Frontline Retail South Australia",
      categoria="Agência de varejo", regiao="Wayville",
      chance="Média", chance2="Média-Alta",
      funcao="Cadastro de candidato — varejo", ingles="Intermediário",
      como="Cadastro online + visita presencial",
      portal="https://www.frontlinerecruitmentgroup.com/user-register/",
      endereco="22 Greenhill Road, Wayville SA 5034 · +61 8 8372 7871", piso=VA,
      dica="MESMO CADASTRO da Frontline Hospitality — não preencha duas vezes. "
           "Wayville fica a 2,5 km do centro, dá para ir a pé pela King William Rd "
           "em 30 minutos."),

    r(setor="Escritório", empregador="Kelsian Group", categoria="Transporte — escritório corporativo",
      regiao="Flinders Street", chance="Baixa", chance2="Média",
      funcao="Vagas de TI e integração (sênior, full-time)",
      ingles="Escrito bom", como="Online (Expr3ss)",
      portal="https://kelsian.expr3ss.com/homeModern",
      endereco="Level 3, 26 Flinders Street, Adelaide SA 5000 · +61 8 8202 8688",
      piso="",
      dica="A vaga que apareceu (Enterprise Integration Developer) é sênior e "
           "full-time, incompatível com 48h/quinzena. O valor aqui é o ENDEREÇO: "
           "Flinders 26 fica a 5 min a pé, e é onde você entrega currículo de dados "
           "quando o visto mudar."),

    r(setor="Escritório", empregador="G'day Group", unidade="Discovery Parks",
      categoria="Turismo — escritório corporativo", regiao="Rundle Mall",
      chance="Baixa", chance2="Média",
      funcao="Housekeeper nos parques; vagas de dados no escritório",
      ingles="Básico em housekeeping; escrito bom no escritório",
      como="Online (LiveHire)",
      portal="https://www.livehire.com/careers/gdaygroup/jobs",
      endereco="Level 6, Rundle Mall Plaza, Rundle Mall, Adelaide SA 5000", piso="",
      dica="O 'Head of Data' que apareceu é cargo de diretoria, fora de alcance. Mas "
           "o escritório fica DENTRO do Rundle Mall Plaza e o grupo também contrata "
           "housekeeper nos parques. A jogada é criar o perfil no LiveHire agora: o "
           "mesmo perfil serve para vaga operacional hoje e vaga de dados depois."),

    r(setor="Escritório", empregador="SA Water", categoria="Estatal — água",
      regiao="Victoria Square", chance="Baixa", chance2="Média-Alta",
      funcao="Customer Care Centre Officer · Business Support Officer",
      ingles="Alto — é call center", como="Online",
      portal="https://careers.sawater.com.au/jobs/search",
      endereco="250 Victoria Square / Tarntanyangga, Adelaide SA 5000 · 1300 729 283",
      piso="",
      dica="Estatal no meio da Victoria Square, 10 min a pé. Mas as vagas abertas "
           "são de call center, e call center com inglês A2 não passa da triagem. "
           "Nenhuma vaga de dados ou BI na checagem. Cadastre alerta e volte quando "
           "o inglês subir — talentacquisition@sawater.com.au"),
]


def main() -> None:
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak6"))

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
    ja = {(d["empregador"], d.get("unidade", "")) for d in dados}
    novos = [n for n in NOVOS if (n["empregador"], n["unidade"]) not in ja]
    dados.extend(novos)
    s = s[:i] + json.dumps(dados, ensure_ascii=False) + s[j + 1:]

    # setor novo + cor
    import re as _re
    m = _re.search(r"SLOTS=(\{.*?\})", s)
    slots = json.loads(m.group(1))
    slots.update(SETOR_NOVO)
    s = s.replace(m.group(0), "SLOTS=" + json.dumps(slots, ensure_ascii=False), 1)
    var, claro, escuro = COR_NOVA
    s = s.replace("--s5:#8b5cf6", f"--s5:#8b5cf6;{var}:{claro}", 1)
    s = s.replace("--s5:#7c4ddb", f"--s5:#7c4ddb;{var}:{escuro}", 1)

    ARQ.write_text(s, encoding="utf-8")
    from collections import Counter
    print(f"registros: {antes} → {len(dados)}  (+{len(novos)})")
    for k, v in Counter(n["setor"] for n in novos).most_common():
        print(f"  {v:>2}  {k}")


if __name__ == "__main__":
    main()
