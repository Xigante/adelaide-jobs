"""Troca o esquema desenhado à mão por um mapa de verdade.

POR QUE MUDOU
O esquema anterior não era legível: linhas e nomes de rua, sem as ruas.
Agora é OpenStreetMap com Leaflet — as ruas reais, com zoom.

A PARTE HONESTA, e ela importa
O pino de cada lugar é APROXIMADO. Eu calibrei cada rua com endereços
reais geocodificados no Nominatim (o geocodificador do OpenStreetMap),
mas ele não tem número de casa em várias ruas de Adelaide — Hindley,
Franklin e Gouger, entre outras. Onde faltou âncora, a posição vem da
grade da cidade. O pino pode cair na quadra vizinha.

O que é EXATO é o endereço escrito e o botão do Google Maps: ele manda
o texto do endereço, e quem geocodifica é o Google, no aparelho dele,
na hora de andar. É por isso que o botão é a peça central e o pino é só
para entender a distribuição.

ÂNCORAS (Nominatim, 30/08/2026, só resultados de PRÉDIO — resultado de
eixo de via foi descartado porque não sabe o número):
  Grenfell 25 e 115 · Pirie 63 e 185 · Rundle 50 e 280 · Hutt 81 e 259
  King William 33 e 121 · Waymouth 11 e 60 · Currie 41 · Wakefield 193
  Gouger 41 · Flinders 31 · Gawler Place 99
"""
import json
import math
import pathlib
import re
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")

# ── Calibração: rua → (lat0, lon0, dlat/número, dlon/número, confiança)
# Duas âncoras = ajuste exato da rua. Uma âncora = usa a inclinação da
# família (leste, oeste ou norte-sul). Nenhuma = grade da cidade.
LESTE_DLON, OESTE_DLON, NS_DLAT = 3.63e-5, -3.10e-5, -3.55e-5

RUAS = {
    # duas âncoras — inclinação medida na própria rua
    "grenfell":     (-34.9248580, 138.6008631, 25,  3.971e-6,  3.4544e-5, "medida"),
    "pirie":        (-34.9260027, 138.6023238, 63,  3.409e-6,  3.7546e-5, "medida"),
    "rundle":       (-34.9225078, 138.6015108, 50,  6.710e-7,  3.6670e-5, "medida"),
    "hutt":         (-34.9282966, 138.6116931, 81, -3.381e-5,  2.668e-6,  "medida"),
    "king william": (-34.9227806, 138.5991290, 33, -3.725e-5,  2.916e-6,  "medida"),
    "waymouth":     (-34.9260673, 138.5988477, 11,  8.808e-6, -3.104e-5,  "medida"),
    # uma âncora — inclinação da família
    "currie":       (-34.9247550, 138.5978890, 41,  0.0, OESTE_DLON, "uma âncora"),
    "wakefield":    (-34.9285888, 138.6079265, 193, 0.0, LESTE_DLON, "uma âncora"),
    "gouger":       (-34.9304891, 138.5976901, 41,  0.0, OESTE_DLON, "uma âncora"),
    "flinders":     (-34.9273808, 138.6016841, 31,  0.0, LESTE_DLON, "uma âncora"),
    "gawler place": (-34.9249912, 138.6017931, 99,  NS_DLAT, 0.0, "uma âncora"),
    # sem âncora — corredor da grade. O par oeste de cada rua leste
    # compartilha a latitude, que é como Adelaide foi desenhada.
    "hindley":      (-34.9225078, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "franklin":     (-34.9273808, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "grote":        (-34.9285888, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "sturt":        (-34.9310000, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "gilbert":      (-34.9322000, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "wright":       (-34.9330000, 138.5991290, 0,   0.0, OESTE_DLON, "grade"),
    "angas":        (-34.9304891, 138.5991290, 0,   0.0, LESTE_DLON, "grade"),
    "carrington":   (-34.9310000, 138.5991290, 0,   0.0, LESTE_DLON, "grade"),
    "halifax":      (-34.9322000, 138.5991290, 0,   0.0, LESTE_DLON, "grade"),
    "gilles":       (-34.9330000, 138.5991290, 0,   0.0, LESTE_DLON, "grade"),
    "pulteney":     (-34.9209000, 138.6060000, 0,   NS_DLAT, 0.0, "grade"),
    "frome":        (-34.9209000, 138.6090000, 0,   NS_DLAT, 0.0, "grade"),
    "morphett":     (-34.9209000, 138.5940000, 0,   NS_DLAT, 0.0, "grade"),
    "victoria":     (-34.9285000, 138.5999000, 0,   0.0, 0.0, "grade"),
    "north":        (-34.9209000, 138.5940000, 0,   0.0, 2.7e-5,  "grade"),
}

RE_END = re.compile(
    r"(\d[\d\-/]*)\s+([A-Z][A-Za-z'\. ]*?)\s*"
    r"(St|Street|Tce|Terrace|Rd|Road|Sq|Square|Place|Pl|Mall|Pde|Parade)\b", re.I)

ILSC = (-34.9245006, 138.6039721)   # 115 Grenfell St, geocodificado


def numero(bruto: str) -> int:
    """Endereço australiano escreve unidade/rua: em "609/147" a rua é 147."""
    if "/" in bruto:
        bruto = bruto.split("/")[-1]
    return int(re.match(r"\d+", bruto).group(0))


def geo(endereco: str):
    if not re.search(r"\bSA 5000\b", endereco or ""):
        return None
    for m in RE_END.finditer(endereco):
        rua = re.sub(r"\s+", " ", m.group(2)).strip().lower()
        rua = re.sub(r"\s+(street|st|terrace|tce)$", "", rua)
        info = RUAS.get(rua)
        if not info:
            continue
        lat0, lon0, n0, dlat, dlon, conf = info
        n = numero(m.group(1))
        return (round(lat0 + dlat * (n - n0), 6),
                round(lon0 + dlon * (n - n0), 6), conf)
    return None


def main():
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak5"))
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

    from collections import Counter
    conf = Counter()
    for r in d:
        g = geo(r.get("endereco", ""))
        r.pop("x", None)
        r.pop("y", None)
        if g:
            r["lat"], r["lon"], r["conf"] = g
            conf[g[2]] += 1

    s = s[:i] + json.dumps(d, ensure_ascii=False) + s[j + 1:]
    ARQ.write_text(s, encoding="utf-8")

    print(f"{sum(conf.values())} lugares com coordenada:")
    for k, v in conf.most_common():
        print(f"  {v:>3}  {k}")

    # confere contra os endereços que eu geocodifiquei de verdade
    print("\nconferência contra o Nominatim (erro em metros):")
    for nome, real in [("Stanton Chase Adelaide", (-34.9260027, 138.6023238)),
                       ("ibis Adelaide", (-34.9245006, 138.6039721))]:
        r = next((x for x in d if x["empregador"] == nome), None)
        if r and "lat" in r:
            dy = (r["lat"] - real[0]) * 111320
            dx = (r["lon"] - real[1]) * 111320 * math.cos(math.radians(real[0]))
            print(f"  {nome:24} {math.hypot(dx, dy):5.0f} m   ({r['conf']})")


if __name__ == "__main__":
    main()
