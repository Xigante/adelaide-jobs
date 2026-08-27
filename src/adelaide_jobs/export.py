"""Saída: CSV sempre, Google Sheets quando configurado.

SQLite é a fonte da verdade; isto aqui é a interface. A sincronização é
num sentido só (SQLite → Sheets) e só a coluna `status` volta — assim não
existe conflito de escrita.
"""

from __future__ import annotations

import csv
import html
import os
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
#  Arquivo único, sem dependência externa: clique duplo e abre.
# ─────────────────────────────────────────────────────────────────────

_PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vagas em Adelaide</title>
<style>
:root{{--bg:#f1f3f0;--card:#fafbf8;--line:#d3d9d1;--ink:#131816;--ink2:#4d5651;
--ink3:#737d77;--ac:#0e5b52;--ok:#2c6738;--okbg:#dcebdd;--wa:#8f6209;--wabg:#f5ead2}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0e1211;--card:#161b19;--line:#2b3330;
--ink:#e9ede8;--ink2:#b0bab4;--ink3:#818b85;--ac:#5cc0ae;--ok:#7cbf87;--okbg:#16281a;
--wa:#d69b34;--wabg:#33270f}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 80px}}
h1{{font-size:1.9rem;margin:0 0 6px;letter-spacing:-.02em}}
.sub{{color:var(--ink3);margin:0 0 22px;font-size:.9rem}}
.stats{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:10px 16px}}
.stat b{{display:block;font-size:1.5rem;color:var(--ac);
font-variant-numeric:tabular-nums;line-height:1.1}}
.stat span{{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}}
#f{{width:100%;padding:11px 14px;font-size:1rem;border:1px solid var(--line);
border-radius:8px;background:var(--card);color:var(--ink);margin-bottom:16px}}
#f:focus{{outline:2px solid var(--ac);outline-offset:1px}}
table{{width:100%;border-collapse:collapse;background:var(--card);
border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:.88rem}}
th{{text-align:left;padding:10px 12px;background:var(--bg);color:var(--ink3);
font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;font-weight:600;
border-bottom:1px solid var(--line);cursor:pointer;user-select:none;white-space:nowrap}}
th:hover{{color:var(--ac)}}
td{{padding:10px 12px;border-bottom:1px solid var(--bg);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
tbody tr:hover{{background:var(--bg)}}
a{{color:var(--ac)}}
.sc{{font-weight:700;font-variant-numeric:tabular-nums;color:var(--ac);white-space:nowrap}}
.km{{font-variant-numeric:tabular-nums;color:var(--ink2);white-space:nowrap}}
.tag{{display:inline-block;font-size:.66rem;text-transform:uppercase;letter-spacing:.05em;
padding:.18em .45em;border-radius:3px;background:var(--okbg);color:var(--ok);white-space:nowrap}}
.tag.w{{background:var(--wabg);color:var(--wa)}}
.emp{{color:var(--ink2)}}
footer{{margin-top:26px;color:var(--ink3);font-size:.8rem;line-height:1.6}}
.hide{{display:none}}
</style></head><body><div class="wrap">
<h1>Vagas em Adelaide</h1>
<p class="sub">Gerado em {quando} &middot; ordenado por aderência ao seu perfil &middot;
clique num cabeçalho para reordenar</p>
<div class="stats">{stats}</div>
<input id="f" placeholder="Filtrar por cargo, empregador ou subúrbio…" autofocus>
<table><thead><tr>
<th data-n="1">Score</th><th>Vaga</th><th>Empregador</th><th>Local</th>
<th data-n="1">km</th><th>Turno</th><th>Inglês</th><th>Fonte</th>
</tr></thead><tbody id="b">{linhas}</tbody></table>
<footer>{rodape}</footer>
</div><script>
const b=document.getElementById('b');
document.getElementById('f').addEventListener('input',e=>{{
  const q=e.target.value.toLowerCase();
  for(const tr of b.rows) tr.classList.toggle('hide', q && !tr.textContent.toLowerCase().includes(q));
}});
document.querySelectorAll('th').forEach((th,i)=>th.addEventListener('click',()=>{{
  const num=th.dataset.n==='1', dir=th.dataset.d==='asc'?-1:1;
  th.dataset.d=dir===1?'asc':'desc';
  [...b.rows].sort((x,y)=>{{
    const a=x.cells[i].textContent.trim(), c=y.cells[i].textContent.trim();
    return (num ? (parseFloat(a)||0)-(parseFloat(c)||0) : a.localeCompare(c))*dir;
  }}).forEach(r=>b.appendChild(r));
}}));
</script></body></html>"""


def to_html(db: Database, path: str | Path, threshold: int = 55, limit: int = 500) -> Path:
    """Página única com a fila. Clique duplo e abre no navegador."""
    import json as _json

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = db.queue(threshold, limit)
    e = html.escape

    linhas = []
    for r in rows:
        d = _json.loads(r["dims_json"]) if r["dims_json"] else {}
        km = d.get("distance_km")
        ing = d.get("eng_contact", "")
        classe = "tag" if ing in ("BOH_MINIMAL", "LOW") else "tag w"
        rotulo = {"BOH_MINIMAL": "sem atendimento", "LOW": "pouco contato",
                  "MEDIUM": "atende cliente", "HIGH": "exige inglês bom",
                  "UNKNOWN": "não diz"}.get(ing, ing.lower())
        turno = {"OVERNIGHT": "noturno", "EVENING": "noite", "EARLY_MORNING": "madrugada",
                 "WEEKEND": "fim de semana", "DAYTIME": "diurno",
                 "ROTATING": "rotativo", "NOT_STATED": "—"}.get(d.get("shift_window", ""), "—")
        fonte = (r["melhor_fonte"] if "melhor_fonte" in r.keys() else None) or r["source"] or ""
        url = (r["melhor_url"] if "melhor_url" in r.keys() else None) or r["url"] or ""
        fonte_txt = ("site da empresa" if fonte.startswith("ats:")
                     else "alerta de e-mail" if fonte == "email"
                     else "Adzuna" if fonte == "adzuna"
                     else fonte)
        linhas.append(
            f'<tr><td class="sc">{r["score"]}</td>'
            f'<td><a href="{e(url)}" target="_blank" rel="noopener">'
            f'{e(r["title"] or "")}</a></td>'
            f'<td class="emp">{e(r["employer"] or "—")}</td>'
            f'<td>{e(r["suburb"] or "—")}</td>'
            f'<td class="km">{f"{km:.1f}" if isinstance(km, (int, float)) else "?"}</td>'
            f'<td>{turno}</td><td><span class="{classe}">{e(rotulo)}</span></td>'
            f'<td>{e(fonte_txt)}</td></tr>'
        )

    s = db.stats()
    stats = "".join(
        f'<div class="stat"><b>{v}</b><span>{k}</span></div>'
        for k, v in [("na fila", len(rows)), ("vagas no banco", s["clusters"]),
                     ("bloqueadas", s["blocked"]), ("anúncios fantasma", s["ghosts"])]
    )
    rodape = (
        "<b>O que a coluna Inglês quer dizer</b><br>"
        "<span class='tag'>sem atendimento</span> você trabalha longe do cliente — "
        "cozinha, reposição de mercado à noite, limpeza, armazém. É onde inglês "
        "básico não atrapalha.<br>"
        "<span class='tag'>pouco contato</span> conversa curta e ocasional.<br>"
        "<span class='tag w'>atende cliente</span> caixa, balcão, servir mesa.<br>"
        "<span class='tag w'>exige inglês bom</span> o anúncio pede comunicação "
        "fluente. Deixe para depois.<br><br>"
        f"<b>Corte em {threshold} pontos</b> — o que ficou abaixo disso não aparece "
        "aqui. Para entender uma nota: <code>adelaide-jobs why &lt;id&gt;</code>.<br><br>"
        "<b>De onde vem o link.</b> Quando a mesma vaga aparece em mais de um "
        "lugar, a coluna Fonte mostra o mais direto: o site da própria empresa "
        "ganha do agregador, porque candidatar-se na origem preserva campos que "
        "o intermediário às vezes perde.<br>"
        "Dados de vagas fornecidos por Jobs by Adzuna e pelas páginas de carreira "
        "dos próprios empregadores."
    )
    out.write_text(
        _PAGINA.format(
            quando=datetime.now().strftime("%d/%m/%Y às %H:%M"),
            stats=stats, rodape=rodape,
            linhas="\n".join(linhas) or
                   '<tr><td colspan="8">Nada na fila ainda. '
                   'Rode <code>adelaide-jobs collect</code>.</td></tr>',
        ),
        encoding="utf-8",
    )
    return out
