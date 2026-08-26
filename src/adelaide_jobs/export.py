"""Saída: CSV sempre, Google Sheets quando configurado.

SQLite é a fonte da verdade; isto aqui é a interface. A sincronização é
num sentido só (SQLite → Sheets) e só a coluna `status` volta — assim não
existe conflito de escrita.
"""

from __future__ import annotations

import csv
import os
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
