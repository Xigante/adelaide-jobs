"""Banco local — a fonte da verdade.

Duas tabelas, e a distinção entre elas é o coração do dedup:

  job_sighting  cada vez que uma vaga foi VISTA, em qualquer fonte
  job_cluster   a vaga em si — vários sightings apontam para um cluster

O Sheets é a interface; isto aqui é o que sabe o que já foi visto, o que
já foi pontuado e o que é anúncio fantasma.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from .models import Dimensions, Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS job_cluster (
    cluster_id      TEXT PRIMARY KEY,
    canon_key       TEXT,
    role_canon      TEXT,
    employer_canon  TEXT,
    title           TEXT,
    employer        TEXT,
    suburb          TEXT,
    postcode        TEXT,
    url             TEXT,
    source          TEXT,
    legitimacy      TEXT,
    first_seen      TEXT,
    last_seen       TEXT,
    posted_at       TEXT,
    repost_count    INTEGER DEFAULT 0,
    sighting_count  INTEGER DEFAULT 0,
    source_count    INTEGER DEFAULT 0,
    ghost_flag      INTEGER DEFAULT 0,
    score           INTEGER,
    score_version   TEXT,
    verdict         TEXT,
    blocked_reason  TEXT,
    dims_json       TEXT,
    scored_at       TEXT,
    applied_at      TEXT,
    outcome         TEXT,
    notes           TEXT
);
CREATE INDEX IF NOT EXISTS idx_cluster_canon ON job_cluster(canon_key);
CREATE INDEX IF NOT EXISTS idx_cluster_role  ON job_cluster(role_canon, postcode);
CREATE INDEX IF NOT EXISTS idx_cluster_score ON job_cluster(score DESC);

CREATE TABLE IF NOT EXISTS job_sighting (
    sighting_id  TEXT PRIMARY KEY,
    cluster_id   TEXT REFERENCES job_cluster(cluster_id),
    source       TEXT,
    source_id    TEXT,
    url          TEXT,
    content_hash TEXT,
    posted_at    TEXT,
    seen_at      TEXT,
    raw_title    TEXT,
    raw_employer TEXT,
    description  TEXT,
    merge_stage  TEXT,
    merge_score  REAL
);
CREATE INDEX IF NOT EXISTS idx_sight_cluster ON job_sighting(cluster_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sight_src ON job_sighting(source, source_id);

-- O cadastro de empregadores. Existe por um motivo só: um anúncio sai
-- do ar, mas a empresa continua existindo e continua contratando o
-- mesmo tipo de gente. `job_cluster` é a vaga e é volátil; isto aqui é
-- a empresa, e nada nunca apaga uma linha daqui. É desta tabela que
-- sai a lista de portas em que vale a pena bater com currículo na mão.
CREATE TABLE IF NOT EXISTS employer (
    employer_canon TEXT PRIMARY KEY,
    employer       TEXT,      -- como aparece escrito, versão mais recente
    primeira_vaga  TEXT,      -- data em que apareceu a primeira vaga
    ultima_vaga    TEXT,
    total_vagas    INTEGER DEFAULT 0,   -- clusters distintos, não sightings
    cargos         TEXT,      -- JSON {título: quantas vezes} — o que pedem
    suburbs        TEXT,      -- JSON {subúrbio: quantas vezes} — onde ficam
    fontes         TEXT,      -- JSON [fonte]
    site           TEXT,      -- melhor URL já vista
    melhor_nota    INTEGER    -- maior nota que uma vaga desta empresa tirou
);
CREATE INDEX IF NOT EXISTS idx_employer_nome ON employer(employer);

CREATE TABLE IF NOT EXISTS run_log (
    run_id     TEXT PRIMARY KEY,
    started_at TEXT,
    ended_at   TEXT,
    source     TEXT,
    collected  INTEGER,
    new_jobs   INTEGER,
    errors     TEXT
);
"""

# Fora da pasta do projeto de proposito. Quando o projeto vive dentro do
# OneDrive (ou de qualquer pasta sincronizada / unidade de rede), o SQLite
# em modo WAL falha com "disk I/O error": o WAL precisa de memoria
# compartilhada que esses sistemas de arquivos nao oferecem. O banco fica
# no perfil do usuario, que nunca e sincronizado.
DEFAULT_DB = Path.home() / ".adelaide-jobs" / "jobs.db"

# Quando a mesma vaga aparece em várias fontes, é por esta ordem que se
# escolhe onde clicar. A página do próprio empregador vem primeiro: o
# agregador às vezes perde campo, corta a descrição, ou manda para um
# formulário degradado — e candidatar-se na origem é sempre melhor.
ORDEM_DAS_FONTES = """
    CASE
        WHEN s.source LIKE 'ats:%%' THEN 0
        WHEN s.source LIKE 'email:%%' THEN 1
        WHEN s.source = 'adzuna'    THEN 2
        WHEN s.source = 'seek_v5'   THEN 3
        ELSE 4
    END
"""


class StorageUnavailable(RuntimeError):
    """O SQLite não consegue escrever nesse caminho.

    Quase sempre é pasta sincronizada (OneDrive, Dropbox, Google Drive) ou
    unidade de rede. O erro cru do sqlite3 é só "disk I/O error", que não
    diz nada — daí esta exceção existir.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(
            f"Não consegui criar o banco em {path}.\n"
            "Isso costuma acontecer em pasta do OneDrive, Dropbox, Google Drive "
            "ou unidade de rede: o SQLite precisa de travas de arquivo que esses "
            "sistemas não oferecem.\n"
            "Solução: use um caminho fora da pasta sincronizada, por exemplo\n"
            f"    adelaide-jobs --db \"{Path.home() / '.adelaide-jobs' / 'jobs.db'}\" collect\n"
            "(esse já é o padrão — você só cai aqui se passou --db apontando "
            "para dentro da pasta sincronizada)."
        )


class Database:
    def __init__(self, path: str | Path = DEFAULT_DB) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = self._connect(wal=True)
        try:
            self.conn.executescript(SCHEMA)
            self.conn.commit()
        except sqlite3.OperationalError:
            # WAL precisa de memória compartilhada, que pasta sincronizada
            # e unidade de rede não oferecem. O modo clássico resolve em
            # boa parte desses casos — mas não em todos.
            self.conn.close()
            try:
                self.conn = self._connect(wal=False)
                self.conn.executescript(SCHEMA)
                self.conn.commit()
            except sqlite3.OperationalError as exc:
                raise StorageUnavailable(self.path) from exc

    def _connect(self, *, wal: bool) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA journal_mode={'WAL' if wal else 'DELETE'}")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── ciclo de vida ────────────────────────────────────────────────

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    # ── L0: cache de vistos ──────────────────────────────────────────

    def seen_hashes(self) -> set[str]:
        """Hashes de conteúdo já processados. O maior descarte do pipeline."""
        rows = self.conn.execute("SELECT DISTINCT content_hash FROM job_sighting").fetchall()
        return {r["content_hash"] for r in rows if r["content_hash"]}

    def sighting_exists(self, source: str, source_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM job_sighting WHERE source=? AND source_id=?",
            (source, source_id),
        ).fetchone()
        return row is not None

    # ── escrita ──────────────────────────────────────────────────────

    def upsert_cluster(self, cluster_id: str, fields: dict[str, Any]) -> None:
        existing = self.conn.execute(
            "SELECT cluster_id, first_seen, sighting_count, repost_count, last_seen "
            "FROM job_cluster WHERE cluster_id=?",
            (cluster_id,),
        ).fetchone()
        today = date.today().isoformat()

        if existing is None:
            fields = {**fields, "cluster_id": cluster_id,
                      "first_seen": today, "last_seen": today,
                      "sighting_count": 1, "source_count": 1}
            cols = ", ".join(fields)
            marks = ", ".join("?" for _ in fields)
            self.conn.execute(
                f"INSERT INTO job_cluster ({cols}) VALUES ({marks})",
                list(fields.values()),
            )
            return

        # Reaparecimento. Gap >= 14 dias conta como repostagem.
        repost = existing["repost_count"] or 0
        last_seen = existing["last_seen"]
        if last_seen:
            gap = (date.today() - date.fromisoformat(last_seen)).days
            if gap >= 14:
                repost += 1

        updates = {**fields, "last_seen": today,
                   "sighting_count": (existing["sighting_count"] or 0) + 1,
                   "repost_count": repost}
        updates.pop("first_seen", None)
        sets = ", ".join(f"{k}=?" for k in updates)
        self.conn.execute(
            f"UPDATE job_cluster SET {sets} WHERE cluster_id=?",
            [*updates.values(), cluster_id],
        )

    # ── cadastro de empregadores ────────────────────────────────────

    def upsert_employer(self, job: Job, employer_canon: str,
                        novo_cluster: bool) -> None:
        """Registra a empresa. Chamado a cada ingest, nunca apaga nada.

        `total_vagas` só cresce quando o cluster é novo — senão a mesma
        vaga vista cinco vezes viraria cinco vagas. `cargos` e `suburbs`
        são contadores acumulados: é a resposta para "o que esta empresa
        costuma contratar", que é o que interessa quando você decide em
        que porta bater.
        """
        hoje = date.today().isoformat()
        atual = self.conn.execute(
            "SELECT * FROM employer WHERE employer_canon=?", (employer_canon,)
        ).fetchone()

        cargos = json.loads(atual["cargos"]) if atual and atual["cargos"] else {}
        suburbs = json.loads(atual["suburbs"]) if atual and atual["suburbs"] else {}
        fontes = json.loads(atual["fontes"]) if atual and atual["fontes"] else []

        titulo = (job.title or "").strip()
        if titulo and (novo_cluster or titulo not in cargos):
            # Conta uma vez por vaga distinta. Um título que reaparece na
            # mesma vaga não é a empresa contratando de novo.
            cargos[titulo] = cargos.get(titulo, 0) + 1
        bairro = (job.suburb or "").strip()
        if bairro and novo_cluster:
            suburbs[bairro] = suburbs.get(bairro, 0) + 1
        if job.source and job.source not in fontes:
            fontes.append(job.source)

        # Um título só, repetido mil vezes, não ajuda ninguém a decidir.
        # Fica com os 40 mais frequentes; o resto é ruído de anúncio.
        if len(cargos) > 40:
            cargos = dict(sorted(cargos.items(), key=lambda kv: -kv[1])[:40])

        if atual is None:
            self.conn.execute(
                "INSERT INTO employer (employer_canon, employer, primeira_vaga, "
                "ultima_vaga, total_vagas, cargos, suburbs, fontes, site) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (employer_canon, job.employer, hoje, hoje, 1 if novo_cluster else 0,
                 json.dumps(cargos, ensure_ascii=False),
                 json.dumps(suburbs, ensure_ascii=False),
                 json.dumps(fontes, ensure_ascii=False), job.url),
            )
            return

        self.conn.execute(
            "UPDATE employer SET employer=?, ultima_vaga=?, total_vagas=?, "
            "cargos=?, suburbs=?, fontes=?, site=COALESCE(site, ?) "
            "WHERE employer_canon=?",
            (job.employer or atual["employer"], hoje,
             (atual["total_vagas"] or 0) + (1 if novo_cluster else 0),
             json.dumps(cargos, ensure_ascii=False),
             json.dumps(suburbs, ensure_ascii=False),
             json.dumps(fontes, ensure_ascii=False), job.url, employer_canon),
        )

    def rebuild_employers(self) -> int:
        """Recalcula o cadastro a partir dos clusters que existem hoje.

        MERGE, não substituição: uma empresa cujo anúncio saiu do ar
        continua na tabela com os números que tinha. É o que faz o
        cadastro ser cadastro e não um retrato do dia.

        Serve para duas coisas: encher a tabela na primeira vez, e
        corrigir contadores que tenham derivado.
        """
        linhas = self.conn.execute(
            "SELECT employer_canon, employer, title, suburb, url, source, "
            "       first_seen, last_seen, score "
            "FROM job_cluster WHERE employer_canon IS NOT NULL "
            "  AND employer_canon <> ''"
        ).fetchall()

        acc: dict[str, dict[str, Any]] = {}
        for r in linhas:
            e = acc.setdefault(r["employer_canon"], {
                "employer": r["employer"], "primeira": r["first_seen"],
                "ultima": r["last_seen"], "total": 0, "cargos": {},
                "suburbs": {}, "fontes": [], "site": None, "nota": None,
            })
            e["total"] += 1
            if r["employer"]:
                e["employer"] = r["employer"]
            for campo, valor, menor in (("primeira", r["first_seen"], True),
                                        ("ultima", r["last_seen"], False)):
                if valor and (not e[campo] or
                              (valor < e[campo] if menor else valor > e[campo])):
                    e[campo] = valor
            if r["title"]:
                e["cargos"][r["title"]] = e["cargos"].get(r["title"], 0) + 1
            if r["suburb"]:
                e["suburbs"][r["suburb"]] = e["suburbs"].get(r["suburb"], 0) + 1
            if r["source"] and r["source"] not in e["fontes"]:
                e["fontes"].append(r["source"])
            if r["url"] and not e["site"]:
                e["site"] = r["url"]
            if r["score"] is not None and (e["nota"] is None or r["score"] > e["nota"]):
                e["nota"] = r["score"]

        for canon, e in acc.items():
            cargos = dict(sorted(e["cargos"].items(), key=lambda kv: -kv[1])[:40])
            self.conn.execute(
                "INSERT INTO employer (employer_canon, employer, primeira_vaga, "
                "  ultima_vaga, total_vagas, cargos, suburbs, fontes, site, melhor_nota) "
                "VALUES (?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(employer_canon) DO UPDATE SET "
                "  employer=excluded.employer, "
                "  primeira_vaga=MIN(COALESCE(employer.primeira_vaga, excluded.primeira_vaga), "
                "                    excluded.primeira_vaga), "
                "  ultima_vaga=NULLIF(MAX(COALESCE(employer.ultima_vaga, ''), "
                "                          COALESCE(excluded.ultima_vaga, '')), ''), "
                "  total_vagas=MAX(employer.total_vagas, excluded.total_vagas), "
                "  cargos=excluded.cargos, suburbs=excluded.suburbs, "
                "  fontes=excluded.fontes, "
                "  site=COALESCE(employer.site, excluded.site), "
                "  melhor_nota=NULLIF(MAX(COALESCE(employer.melhor_nota, -1), "
                "                         COALESCE(excluded.melhor_nota, -1)), -1)",
                (canon, e["employer"], e["primeira"], e["ultima"], e["total"],
                 json.dumps(cargos, ensure_ascii=False),
                 json.dumps(e["suburbs"], ensure_ascii=False),
                 json.dumps(e["fontes"], ensure_ascii=False), e["site"], e["nota"]),
            )
        self.conn.commit()
        return len(acc)

    def empregadores(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM employer ORDER BY total_vagas DESC, employer"
        ).fetchall()

    def insert_sighting(
        self,
        job: Job,
        cluster_id: str,
        merge_stage: str,
        merge_score: float | None = None,
    ) -> str:
        sighting_id = f"{job.source}:{job.source_id}"
        self.conn.execute(
            """INSERT OR REPLACE INTO job_sighting
               (sighting_id, cluster_id, source, source_id, url, content_hash,
                posted_at, seen_at, raw_title, raw_employer, description,
                merge_stage, merge_score)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sighting_id, cluster_id, job.source, job.source_id, job.url,
                job.content_hash(),
                job.posted_at.isoformat() if job.posted_at else None,
                datetime.now().isoformat(timespec="seconds"),
                job.title, job.employer, job.description[:20000],
                merge_stage, merge_score,
            ),
        )
        # source_count = fontes distintas que viram este cluster
        self.conn.execute(
            """UPDATE job_cluster SET source_count =
               (SELECT COUNT(DISTINCT source) FROM job_sighting WHERE cluster_id=?)
               WHERE cluster_id=?""",
            (cluster_id, cluster_id),
        )
        return sighting_id

    def save_score(
        self,
        cluster_id: str,
        score: int | None,
        verdict: str,
        blocked_reason: str | None,
        dims: Dimensions | None,
        score_version: str,
    ) -> None:
        self.conn.execute(
            """UPDATE job_cluster
               SET score=?, verdict=?, blocked_reason=?, dims_json=?,
                   score_version=?, scored_at=?
               WHERE cluster_id=?""",
            (
                score, verdict, blocked_reason,
                json.dumps(dims.to_row(), ensure_ascii=False) if dims else None,
                score_version, datetime.now().isoformat(timespec="seconds"),
                cluster_id,
            ),
        )

    def mark_ghosts(self, min_reposts: int = 4, window_days: int = 90) -> int:
        """Anúncio repostado muitas vezes sem mudar = banco de currículos.

        É o sinal que um humano olhando anúncio por anúncio não detecta,
        e a justificativa mais forte para o pipeline existir.
        """
        cutoff = (date.today() - timedelta(days=window_days)).isoformat()
        cur = self.conn.execute(
            "UPDATE job_cluster SET ghost_flag=1 "
            "WHERE repost_count >= ? AND first_seen >= ? AND ghost_flag=0",
            (min_reposts, cutoff),
        )
        return cur.rowcount

    # ── leitura ──────────────────────────────────────────────────────

    def candidates_by_key(self, role_canon: str, postcode3: str | None) -> list[sqlite3.Row]:
        """Bloco de comparação para o dedup fuzzy (estágio 2)."""
        if postcode3:
            return self.conn.execute(
                "SELECT * FROM job_cluster WHERE role_canon=? "
                "AND (postcode IS NULL OR substr(postcode,1,3)=?)",
                (role_canon, postcode3),
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM job_cluster WHERE role_canon=?", (role_canon,)
        ).fetchall()

    def cluster_by_canon(self, canon_key: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM job_cluster WHERE canon_key=?", (canon_key,)
        ).fetchone()

    def queue(self, threshold: int = 55, limit: int = 200) -> list[sqlite3.Row]:
        """A fila: o que vale a pena olhar, melhor primeiro."""
        return self.conn.execute(
            f"""SELECT c.*,
                   (SELECT s.url FROM job_sighting s WHERE s.cluster_id = c.cluster_id
                    ORDER BY {ORDEM_DAS_FONTES} LIMIT 1) AS melhor_url,
                   (SELECT s.source FROM job_sighting s WHERE s.cluster_id = c.cluster_id
                    ORDER BY {ORDEM_DAS_FONTES} LIMIT 1) AS melhor_fonte
               FROM job_cluster c
               WHERE c.verdict='SCORED' AND c.score >= ? AND c.applied_at IS NULL
               ORDER BY c.score DESC, c.last_seen DESC LIMIT ?""",
            (threshold, limit),
        ).fetchall()

    def todas(self, limit: int = 3000) -> list[sqlite3.Row]:
        """Tudo que foi avaliado, inclusive o que foi bloqueado.

        A `queue` é a fila de trabalho e corta pelo threshold. Esta aqui
        alimenta o relatório HTML, onde o filtro é do leitor, não meu —
        às vezes vale ver o que foi descartado e por quê.
        """
        return self.conn.execute(
            f"""SELECT c.*,
                   (SELECT s.url FROM job_sighting s WHERE s.cluster_id = c.cluster_id
                    ORDER BY {ORDEM_DAS_FONTES} LIMIT 1) AS melhor_url,
                   (SELECT s.source FROM job_sighting s WHERE s.cluster_id = c.cluster_id
                    ORDER BY {ORDEM_DAS_FONTES} LIMIT 1) AS melhor_fonte
               FROM job_cluster c
               WHERE c.verdict IS NOT NULL
               ORDER BY (c.verdict = 'BLOCKED'), c.score DESC, c.last_seen DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

    def unscored(self, lote: int = 500) -> list[sqlite3.Row]:
        """Um LOTE de clusters sem nota — não todos.

        Quem chama tem que repetir até vir vazio. `Pipeline.score_pending`
        faz isso. O lote existe para a memória não explodir com 6 mil
        vagas de uma vez; não é um limite de quantas se pontua.
        """
        return self.conn.execute(
            "SELECT * FROM job_cluster WHERE verdict IS NULL LIMIT ?", (lote,)
        ).fetchall()

    def stats(self) -> dict[str, Any]:
        q = self.conn.execute
        return {
            "clusters": q("SELECT COUNT(*) c FROM job_cluster").fetchone()["c"],
            "sightings": q("SELECT COUNT(*) c FROM job_sighting").fetchone()["c"],
            "scored": q("SELECT COUNT(*) c FROM job_cluster WHERE score IS NOT NULL").fetchone()["c"],
            "blocked": q("SELECT COUNT(*) c FROM job_cluster WHERE verdict='BLOCKED'").fetchone()["c"],
            "ghosts": q("SELECT COUNT(*) c FROM job_cluster WHERE ghost_flag=1").fetchone()["c"],
            "sources": [
                (r["source"], r["c"])
                for r in q("SELECT source, COUNT(*) c FROM job_sighting "
                           "GROUP BY source ORDER BY c DESC").fetchall()
            ],
        }

    def log_run(self, run_id: str, source: str, collected: int,
                new_jobs: int, started: str, errors: str = "") -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO run_log VALUES (?,?,?,?,?,?,?)",
            (run_id, started, datetime.now().isoformat(timespec="seconds"),
             source, collected, new_jobs, errors),
        )
