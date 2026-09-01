"""Saída: CSV sempre, Google Sheets quando configurado.

SQLite é a fonte da verdade; isto aqui é a interface. A sincronização é
num sentido só (SQLite → Sheets) e só a coluna `status` volta — assim não
existe conflito de escrita.
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .db import Database

COLUMNS = [
    "score", "title", "employer", "suburb", "url", "source",
    "legitimacy", "shift", "english", "experience", "distance_km",
    "first_seen", "last_seen", "reposts", "sources", "ghost", "cluster_id",
]


def _row_to_export(row: Any) -> dict[str, Any]:
    import json
    dims = json.loads(row["dims_json"]) if row["dims_json"] else {}
    km = dims.get("distance_km")
    return {
        "score": row["score"],
        "title": row["title"],
        "employer": row["employer"] or "",
        "suburb": row["suburb"] or "",
        "url": row["url"],
        "source": row["source"],
        "legitimacy": row["legitimacy"] or "",
        "shift": dims.get("shift_window", ""),
        "english": dims.get("eng_contact", ""),
        "experience": dims.get("exp_req", ""),
        "distance_km": round(km, 1) if isinstance(km, (int, float)) else "",
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "reposts": row["repost_count"],
        "sources": row["source_count"],
        "ghost": "sim" if row["ghost_flag"] else "",
        "cluster_id": row["cluster_id"],
    }


def to_csv(db: Database, path: str | Path, threshold: int = 55, limit: int = 500) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = db.queue(threshold, limit)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_row_to_export(row))
    return out


# ══ Cadastro de empregadores ═════════════════════════════════════════
#
# Isto NÃO é a fila de vagas. A fila responde "onde me candidato hoje";
# o cadastro responde "quem contrata gente como eu em Adelaide" — e
# continua respondendo depois que o anúncio saiu do ar. É a lista de
# portas para bater com currículo impresso.

# Heurística de exibição, e só de exibição: serve para filtrar a aba
# por setor. Quem decide se a vaga presta é o scoring.py, não isto.
FAMILIAS: list[tuple[str, str]] = [
    ("limpeza",     r"clean|housekeep|janitor|laundry|washroom"),
    ("armazém",     r"warehouse|pick|pack|freight|forklift|storeperson|store person|"
                    r"courier|delivery|driver|logistic|dispatch|loader"),
    ("cozinha",     r"kitchen|chef|cook|barista|wait|bar\b|food service|catering|"
                    r"caf[eé]|restaurant|dish|barback|glass"),
    ("varejo",      r"retail|checkout|customer service|team member|merchandis|"
                    r"sales assistant|shop|store\b|cashier"),
    ("saúde",       r"nurse|care worker|aged care|health|clinical|medical|patient|"
                    r"disability|support worker"),
    ("dados",       r"\bdata\b|analyst|power bi|reporting|business intelligence|"
                    r"insights|sql|dashboard"),
    ("escritório",  r"admin|office|clerk|reception|coordinator|assistant\b|payroll|"
                    r"accounts|finance"),
    ("hotel",       r"hotel|hospitality|housekeeping|front office|concierge|motel"),
    ("construção",  r"construction|labourer|trades|carpent|electric|plumb|paint"),
]

# Nomes que os agregadores usam quando o anunciante não quis se
# identificar. Não são empresas, e bater na porta deles é impossível.
# Ficam no cadastro (nada se perde), mas marcados.
RE_SEM_NOME = re.compile(
    r"^(private advertiser|confidential|not specified|anonymous|various|"
    r"n/?a|undisclosed|company confidential)\.?$", re.I)


# "escritório" pega admin/assistant/coordinator, que aparecem em quase
# toda empresa grande — sem este peso, a SA Health inteira vira
# escritório em vez de saúde. É desempate de exibição, nada mais.
PESO = {"escritório": 0.55}


def _setores(cargos: dict[str, int], quantos: int = 2) -> list[str]:
    """Os setores da empresa, pelos cargos que ela mais anuncia.

    Devolve até dois de propósito. Uma rede de supermercado anuncia
    caixa e repositor de depósito; forçar um rótulo só faria ela sumir
    de um dos dois filtros.
    """
    texto = " ".join(cargos).lower()
    marcados = []
    for nome, padrao in FAMILIAS:
        n = len(re.findall(padrao, texto)) * PESO.get(nome, 1.0)
        if n:
            marcados.append((n, nome))
    marcados.sort(reverse=True)
    return [n for _, n in marcados[:quantos]] or ["outros"]


def _link_limpo(url: str | None) -> str:
    """Tira a query string dos links da Adzuna.

    Eles vêm com `utm_source=<app_id>` grudado. O link funciona sem isso,
    e o cadastro vai parar numa página pública — o app_id não tem por que
    passear por lá.
    """
    if not url:
        return ""
    if "adzuna." in url:
        return url.split("?", 1)[0]
    return url


# Nome de empresa vindo de scraping chega com BOM e espaço de largura
# zero grudado. Invisível na tela, mas quebra ordenação e busca: quem
# digita "Dymocks" não acha "\ufeffDymocks".
RE_INVISIVEL = re.compile(r"[\ufeff\u200b-\u200d\u2060]")


def _empregador_linha(row: Any, cargos_max: int = 8,
                      corte: int = 0) -> dict[str, Any]:
    cargos = json.loads(row["cargos"] or "{}")
    suburbs = json.loads(row["suburbs"] or "{}")
    ordenados = [t for t, _ in sorted(cargos.items(), key=lambda kv: -kv[1])]
    if corte:
        ordenados = [t if len(t) <= corte else t[:corte - 1].rstrip() + "…"
                     for t in ordenados]
    bairros = sorted(suburbs.items(), key=lambda kv: -kv[1])
    return {
        "nome": RE_INVISIVEL.sub("", row["employer"] or "").strip(),
        "chave": row["employer_canon"],
        "vagas": row["total_vagas"] or 0,
        "setores": _setores(cargos),
        "cargos": ordenados[:cargos_max],
        "cargos_total": len(cargos),
        "bairros": [b for b, _ in bairros[:3]],
        "primeira": row["primeira_vaga"] or "",
        "ultima": row["ultima_vaga"] or "",
        "nota": row["melhor_nota"],
        "fontes": json.loads(row["fontes"] or "[]"),
        "link": _link_limpo(row["site"]),
        "sem_nome": bool(RE_SEM_NOME.match((row["employer"] or "").strip())),
    }


COLUNAS_EMPREGADOR = ["nome", "vagas", "setor", "cargos", "bairros",
                      "primeira", "ultima", "nota", "fontes", "link"]


def empregadores_to_csv(db: Database, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUNAS_EMPREGADOR)
        w.writeheader()
        for row in db.empregadores():
            d = _empregador_linha(row, cargos_max=40)
            w.writerow({
                "nome": d["nome"], "vagas": d["vagas"],
                "setor": " | ".join(d["setores"]),
                "cargos": " | ".join(d["cargos"]),
                "bairros": " | ".join(d["bairros"]),
                "primeira": d["primeira"], "ultima": d["ultima"],
                "nota": d["nota"] if d["nota"] is not None else "",
                "fontes": " | ".join(d["fontes"]), "link": d["link"],
            })
    return out


def empregadores_to_json(db: Database, path: str | Path) -> Path:
    """O arquivo que alimenta a aba Empresas do material.

    Chaves de uma letra, e não é preciosismo: são 2.995 empresas, o
    material é embutido num HTML único, e ele abre isso no celular na
    rua. Só o nome das chaves, escrito por extenso, custava 165 KB.

        n  nome            v  quantas vagas já teve
        s  setores (1-2)   c  até 3 cargos, cortados em 52 caracteres
        b  até 2 bairros   p  melhor nota que uma vaga dela tirou
        de / ate           primeira e última vaga vista (AAAA-MM-DD)
        a  id da Adzuna    u  URL inteira, quando não é da Adzuna
        x  1 = anunciante sem nome ("Private Advertiser" e afins)
        t  total de cargos distintos, só quando passa dos 3 mostrados

    Campo ausente = vazio. Quem quer tudo, com os nomes por extenso e
    os 40 cargos, abre o empregadores.csv.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    dados = []
    for r in db.empregadores():
        d = _empregador_linha(r, cargos_max=3, corte=52)
        e: dict[str, Any] = {"n": d["nome"], "v": d["vagas"], "s": d["setores"]}
        if d["cargos"]:
            e["c"] = d["cargos"]
        if d["cargos_total"] > len(d["cargos"]):
            e["t"] = d["cargos_total"]
        if d["bairros"]:
            e["b"] = d["bairros"][:2]
        if d["primeira"]:
            e["de"] = d["primeira"]
        if d["ultima"]:
            e["ate"] = d["ultima"]
        if d["nota"] is not None:
            e["p"] = d["nota"]
        link = d["link"]
        if link.startswith("https://www.adzuna.com.au/details/"):
            e["a"] = link.rsplit("/", 1)[-1]
        elif link:
            e["u"] = link
        if d["sem_nome"]:
            e["x"] = 1
        dados.append(e)

    out.write_text(json.dumps({
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "total": len(dados),
        "adzuna": "https://www.adzuna.com.au/details/",
        "empresas": dados,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


def to_sheets(db: Database, threshold: int = 55, limit: int = 500,
              worksheet: str = "Vagas") -> str:
    """Escreve a fila numa planilha do Google.

    Uma única chamada em lote para as N linhas — a quota é de 60 escritas
    por minuto por usuário, e escrever linha a linha estoura na hora.
    """
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not creds_path or not sheet_id:
        raise RuntimeError(
            "GOOGLE_SHEETS_CREDENTIALS e GOOGLE_SHEETS_ID precisam estar no .env. "
            "Lembre de compartilhar a planilha com o e-mail da service account."
        )
    try:
        import gspread
    except ImportError as exc:
        raise RuntimeError('Rode: pip install "adelaide-jobs[sheets]"') from exc

    gc = gspread.service_account(filename=creds_path)
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(worksheet)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet, rows=1000, cols=len(COLUMNS))

    rows = db.queue(threshold, limit)
    values: list[Sequence[Any]] = [COLUMNS]
    values += [[_row_to_export(r).get(c, "") for c in COLUMNS] for r in rows]

    ws.clear()
    ws.update(values, "A1")   # uma chamada, todas as linhas
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}"



# ─────────────────────────────────────────────────────────────────────
#  Relatório HTML — o jeito de olhar as vagas sem abrir terminal.
#  Mostra TUDO, inclusive o que foi bloqueado, e deixa o filtro com
#  quem lê. Arquivo único, sem dependência: clique duplo e abre.
# ─────────────────────────────────────────────────────────────────────

_CSS = """
:root{--bg:#f1f3f0;--card:#fafbf8;--line:#d3d9d1;--ink:#131816;--ink2:#4d5651;
--ink3:#737d77;--ac:#0e5b52;--ok:#2c6738;--okbg:#dcebdd;--wa:#8f6209;
--wabg:#f5ead2;--no:#9c2b26;--nobg:#f6dedc}
@media(prefers-color-scheme:dark){:root{--bg:#0e1211;--card:#161b19;--line:#2b3330;
--ink:#e9ede8;--ink2:#b0bab4;--ink3:#818b85;--ac:#5cc0ae;--ok:#7cbf87;--okbg:#16281a;
--wa:#d69b34;--wabg:#33270f;--no:#e2908a;--nobg:#331a19}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
.wrap{max-width:1320px;margin:0 auto;padding:26px 18px 80px}
h1{font-size:1.85rem;margin:0 0 5px;letter-spacing:-.02em}
.sub{color:var(--ink3);margin:0 0 20px;font-size:.88rem}
.stats{display:flex;flex-wrap:wrap;gap:9px;margin-bottom:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 15px}
.stat b{display:block;font-size:1.4rem;color:var(--ac);font-variant-numeric:tabular-nums;line-height:1.1}
.stat span{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:14px}
#f{flex:1 1 260px;min-width:220px;padding:10px 13px;font-size:.95rem;
border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
#f:focus{outline:2px solid var(--ac);outline-offset:1px}
.chip{border:1px solid var(--line);background:var(--card);color:var(--ink2);
border-radius:999px;padding:7px 13px;font-size:.8rem;cursor:pointer;font-weight:600;
font-family:inherit;white-space:nowrap}
.chip:hover{border-color:var(--ac);color:var(--ac)}
.chip[aria-pressed="true"]{background:var(--ac);border-color:var(--ac);color:var(--bg)}
.chip small{font-weight:400;opacity:.75;margin-left:.35em}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:8px;overflow:hidden;font-size:.87rem}
th{text-align:left;padding:9px 11px;background:var(--bg);color:var(--ink3);font-size:.68rem;
text-transform:uppercase;letter-spacing:.07em;font-weight:600;border-bottom:1px solid var(--line);
cursor:pointer;user-select:none;white-space:nowrap}
th:hover{color:var(--ac)}
td{padding:9px 11px;border-bottom:1px solid var(--bg);vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--bg)}
a{color:var(--ac)}
.nota{font-weight:800;font-size:.95rem;white-space:nowrap;letter-spacing:-.02em}
.n-Ap,.n-A,.n-Am{color:var(--ok)} .n-Bp,.n-B{color:var(--wa)}
.n-C,.n-D{color:var(--ink3)} .n-X{color:var(--no)}
.pts{font-variant-numeric:tabular-nums;color:var(--ink3);font-size:.8rem}
.km{font-variant-numeric:tabular-nums;color:var(--ink2);white-space:nowrap}
.tag{display:inline-block;font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;
padding:.18em .45em;border-radius:3px;background:var(--okbg);color:var(--ok);white-space:nowrap}
.tag.w{background:var(--wabg);color:var(--wa)} .tag.n{background:var(--nobg);color:var(--no)}
.emp{color:var(--ink2)}
.btn{display:inline-block;background:var(--ac);color:var(--bg);text-decoration:none;
padding:.4em .8em;border-radius:6px;font-size:.78rem;font-weight:700;white-space:nowrap}
.btn:hover{filter:brightness(1.12)}
.btn.off{background:var(--line);color:var(--ink3);pointer-events:none}
.motivo{color:var(--no);font-size:.78rem}
footer{margin-top:24px;color:var(--ink3);font-size:.8rem;line-height:1.65}
footer b{color:var(--ink2)}
.hide{display:none}
#vazio{padding:26px;text-align:center;color:var(--ink3)}
"""

_JS = """
const b=document.getElementById('b'), busca=document.getElementById('f');
let faixa='todas';
function aplicar(){
  const q=busca.value.toLowerCase().trim();
  let n=0;
  for(const tr of b.rows){
    const okF = faixa==='todas' || tr.dataset.faixa===faixa;
    const okQ = !q || tr.textContent.toLowerCase().includes(q);
    const mostra = okF && okQ;
    tr.classList.toggle('hide', !mostra);
    if(mostra) n++;
  }
  document.getElementById('conta').textContent=n;
  document.getElementById('vazio').classList.toggle('hide', n>0);
}
busca.addEventListener('input',aplicar);
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>{
  document.querySelectorAll('.chip').forEach(o=>o.setAttribute('aria-pressed','false'));
  c.setAttribute('aria-pressed','true');
  faixa=c.dataset.faixa;
  aplicar();
}));
document.querySelectorAll('th[data-i]').forEach(th=>th.addEventListener('click',()=>{
  const i=+th.dataset.i, num=th.dataset.n==='1', dir=th.dataset.d==='asc'?-1:1;
  th.dataset.d = dir===1?'asc':'desc';
  [...b.rows].sort((x,y)=>{
    const a=x.cells[i].textContent.trim(), c=y.cells[i].textContent.trim();
    return (num ? (parseFloat(a)||0)-(parseFloat(c)||0) : a.localeCompare(c,'pt'))*dir;
  }).forEach(r=>b.appendChild(r));
}));
aplicar();
"""

_PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vagas em Adelaide</title>
<style>{css}</style></head><body><div class="wrap">
<h1>Vagas em Adelaide</h1>
<p class="sub">{quando} &middot; <span id="conta">{total}</span> de {total} vagas visíveis
&middot; inglês configurado: <b>{ingles}</b></p>
<div class="stats">{stats}</div>
<div class="controls">
  <input id="f" placeholder="Filtrar por cargo, empregador ou subúrbio…" autofocus>
  {chips}
</div>
<table><thead><tr>
<th data-i="0" data-n="1">Nota</th><th data-i="1" data-n="1">Pts</th>
<th data-i="2">Vaga</th><th data-i="3">Empregador</th><th data-i="4">Local</th>
<th data-i="5" data-n="1">km</th><th data-i="6">Turno</th><th data-i="7">Inglês</th>
<th data-i="8">Fonte</th><th>Candidatar-se</th>
</tr></thead><tbody id="b">{linhas}</tbody></table>
<div id="vazio" class="hide">Nada bate com esse filtro.</div>
<footer>{rodape}</footer>
</div><script>{js}</script></body></html>"""

_CLASSE_NOTA = {"A+": "n-Ap", "A": "n-A", "A-": "n-Am", "B+": "n-Bp",
                "B": "n-B", "C": "n-C", "D": "n-D", "X": "n-X", "?": "n-D"}

_ROTULO_INGLES = {
    "BOH_MINIMAL": ("sem atendimento", "tag"),
    "LOW": ("pouco contato", "tag"),
    "MEDIUM": ("atende cliente", "tag w"),
    "HIGH": ("exige inglês bom", "tag n"),
    "UNKNOWN": ("não diz", "tag w"),
}
_ROTULO_TURNO = {"OVERNIGHT": "noturno", "EVENING": "noite", "EARLY_MORNING": "madrugada",
                 "WEEKEND": "fim de semana", "DAYTIME": "diurno", "ROTATING": "rotativo"}


def to_html(db: Database, path: str | Path, threshold: int = 0,
            limit: int = 3000) -> Path:
    """Página única com TODAS as vagas avaliadas, filtráveis por nota."""
    import json as _json

    from .scoring import FAIXAS, nota

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [r for r in db.todas(limit)
            if r["verdict"] == "BLOCKED" or (r["score"] or 0) >= threshold]
    e = html.escape

    contagem: dict[str, int] = {}
    linhas = []
    for r in rows:
        bloqueada = r["verdict"] == "BLOCKED"
        letra, acao = nota(r["score"], bloqueada)
        contagem[letra] = contagem.get(letra, 0) + 1

        d = _json.loads(r["dims_json"]) if r["dims_json"] else {}
        km = d.get("distance_km")
        rotulo, classe = _ROTULO_INGLES.get(d.get("eng_contact", ""), ("não diz", "tag w"))
        turno = _ROTULO_TURNO.get(d.get("shift_window", ""), "—")

        fonte = (r["melhor_fonte"] or r["source"] or "")
        url = (r["melhor_url"] or r["url"] or "")
        fonte_txt = ("site da empresa" if fonte.startswith("ats:")
                     else "alerta de e-mail" if fonte == "email"
                     else "Adzuna" if fonte == "adzuna"
                     else fonte or "—")

        if bloqueada:
            titulo = f'<span class="motivo">{e(r["title"] or "")}</span><br>' \
                     f'<span class="motivo">✕ {e(r["blocked_reason"] or "")}</span>'
            botao = '<span class="btn off">bloqueada</span>'
        else:
            titulo = e(r["title"] or "")
            botao = (f'<a class="btn" href="{e(url)}" target="_blank" rel="noopener">'
                     f'Candidatar-se →</a>' if url else '<span class="btn off">sem link</span>')

        linhas.append(
            f'<tr data-faixa="{e(letra)}">'
            f'<td class="nota {_CLASSE_NOTA.get(letra, "")}" title="{e(acao)}">{e(letra)}</td>'
            f'<td class="pts">{"" if bloqueada else (r["score"] or 0)}</td>'
            f'<td>{titulo}</td>'
            f'<td class="emp">{e(r["employer"] or "—")}</td>'
            f'<td>{e(r["suburb"] or "—")}</td>'
            f'<td class="km">{f"{km:.1f}" if isinstance(km, (int, float)) else "?"}</td>'
            f'<td>{turno}</td><td><span class="{classe}">{e(rotulo)}</span></td>'
            f'<td>{e(fonte_txt)}</td><td>{botao}</td></tr>'
        )

    ordem = [l for _, l, _ in FAIXAS] + ["X"]
    chips = ['<button class="chip" data-faixa="todas" aria-pressed="true">'
             f'todas<small>{len(rows)}</small></button>']
    for letra in ordem:
        if contagem.get(letra):
            acao = next((a for _, l, a in FAIXAS if l == letra), "bloqueadas")
            chips.append(f'<button class="chip" data-faixa="{letra}" aria-pressed="false" '
                         f'title="{html.escape(acao)}">{letra}'
                         f'<small>{contagem[letra]}</small></button>')

    s = db.stats()
    boas = sum(contagem.get(l, 0) for l in ("A+", "A", "A-"))
    stats = "".join(
        f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
        for k, v in [("nota A ou melhor", boas), ("avaliadas", len(rows)),
                     ("bloqueadas", contagem.get("X", 0)),
                     ("anúncios fantasma", s["ghosts"])]
    )

    faixas_txt = " &middot; ".join(f"<b>{l}</b> {c}–{FAIXAS[i-1][0]-1 if i else 100}"
                                   for i, (c, l, _) in enumerate(FAIXAS))
    rodape = (
        f"<b>As notas.</b> {faixas_txt} &middot; <b>X</b> bloqueada por um knockout — "
        "o motivo aparece embaixo do título.<br><br>"
        "<b>A coluna Inglês.</b> "
        "<span class='tag'>sem atendimento</span> longe do cliente: cozinha, reposição "
        "noturna, limpeza, armazém — inglês básico não atrapalha. "
        "<span class='tag'>pouco contato</span> conversa curta. "
        "<span class='tag w'>atende cliente</span> caixa, balcão, mesa. "
        "<span class='tag n'>exige inglês bom</span> o anúncio pede fluência.<br>"
        "Essa coluna muda sozinha quando você atualizar <code>english.current_level</code> "
        "no <code>config/profile.yaml</code> e rodar <code>adelaide-jobs score --rescore</code>.<br><br>"
        "<b>De onde vem o link.</b> Quando a mesma vaga aparece em vários lugares, o botão "
        "aponta para o mais direto: site do empregador &gt; alerta de e-mail &gt; Adzuna. "
        "Candidatar-se na origem preserva campos que o intermediário às vezes perde.<br><br>"
        "Para entender uma nota: <code>adelaide-jobs why &lt;id&gt;</code>.<br>"
        "Dados de vagas fornecidos por Jobs by Adzuna e pelas páginas de carreira dos "
        "próprios empregadores."
    )

    out.write_text(
        _PAGINA.format(
            css=_CSS, js=_JS,
            quando=datetime.now().strftime("%d/%m/%Y às %H:%M"),
            total=len(rows), ingles=_nivel_ingles(),
            stats=stats, chips="".join(chips), rodape=rodape,
            linhas="\n".join(linhas) or
                   '<tr><td colspan="10">Nada avaliado ainda. '
                   'Rode <code>adelaide-jobs collect</code>.</td></tr>',
        ),
        encoding="utf-8",
    )
    return out


def _nivel_ingles() -> str:
    try:
        from . import config as _cfg
        return _cfg.load().english_level
    except Exception:
        return "A2"
