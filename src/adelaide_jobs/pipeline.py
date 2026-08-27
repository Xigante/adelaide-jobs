"""O orquestrador: coleta → dedup → triagem → score.

A cascata de filtros existe por qualidade da fila, não por economia de
token. Trinta vagas boas por semana é utilizável; trezentas com 270
irrelevantes não é, e você para de abrir o sistema em duas semanas.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from . import filters
from .config import Config
from .db import Database
from .dedup import (
    FUZZY_SAME, body_shingle, canon_employer, canon_key, canon_role,
    employer_is_anonymous, fuzzy_match_score,
)
from .extract import Extractor, RuleExtractor
from .models import Job
from .scoring import score as compute_score

log = logging.getLogger(__name__)


@dataclass
class RunReport:
    collected: int = 0
    duplicates: int = 0
    already_seen: int = 0
    new_clusters: int = 0
    blocked: int = 0
    scored: int = 0
    ghosts: int = 0
    by_source: dict[str, int] = field(default_factory=dict)
    knockouts: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"coletadas         {self.collected}",
            f"  já vistas       {self.already_seen}",
            f"  duplicatas      {self.duplicates}",
            f"  novas           {self.new_clusters}",
            f"bloqueadas        {self.blocked}",
            f"pontuadas         {self.scored}",
            f"fantasmas         {self.ghosts}",
        ]
        if self.by_source:
            lines.append("por fonte:")
            for src, n in sorted(self.by_source.items(), key=lambda kv: -kv[1]):
                lines.append(f"  {src:<16} {n}")
        if self.knockouts:
            lines.append("knockouts:")
            for code, n in sorted(self.knockouts.items(), key=lambda kv: -kv[1]):
                lines.append(f"  {code:<26} {n}")
        if self.errors:
            lines.append(f"erros ({len(self.errors)}):")
            lines += [f"  ! {e}" for e in self.errors[:10]]
        return "\n".join(lines)


class Pipeline:
    def __init__(
        self,
        cfg: Config,
        db: Database,
        extractor: Extractor | None = None,
    ) -> None:
        """`extractor` é o ponto de troca da camada de inteligência.

        O padrão é o `RuleExtractor`, que é regex puro: sem chave, sem
        custo, sem rede. Qualquer objeto com `.name` e `.extract(job) ->
        Dimensions` serve no lugar — Gemini, Ollama local, outro modelo.
        O scorer não muda, porque ele lê `Dimensions`, não texto.

        Ver docs/AUTONOMIA.md.
        """
        self.cfg = cfg
        self.db = db
        self.extractor: Extractor = extractor or RuleExtractor(cfg.boh_keywords)

    # ── dedup ────────────────────────────────────────────────────────

    def resolve_cluster(self, job: Job) -> tuple[str, str, float | None]:
        """Devolve (cluster_id, estágio_do_merge, score_do_merge)."""
        key_hash, key_raw = canon_key(job.employer, job.title, job.suburb, job.postcode)
        role = canon_role(job.title)

        # Estágio 1 — chave exata. Não se aplica quando o empregador é
        # anônimo: aí todos os kitchen hands de agência do CBD colapsariam
        # na mesma chave.
        if not employer_is_anonymous(job.employer):
            hit = self.db.cluster_by_canon(key_hash)
            if hit:
                return hit["cluster_id"], "EXACT", 100.0

        # Estágio 2 — blocking por (papel, 3 primeiros dígitos do CEP)
        # e comparação fuzzy dentro do bloco.
        postcode3 = job.postcode[:3] if job.postcode else None
        emp_c = canon_employer(job.employer)
        body = body_shingle(job.description)
        best_id, best_score = None, 0.0
        for cand in self.db.candidates_by_key(role, postcode3):
            s = fuzzy_match_score(
                role, cand["role_canon"] or "",
                emp_c, cand["employer_canon"] or "",
                body, body_shingle(cand["title"] or ""),
                job.postcode, cand["postcode"],
            )
            if s > best_score:
                best_id, best_score = cand["cluster_id"], s
        if best_id and best_score >= FUZZY_SAME:
            return best_id, "FUZZY", best_score

        # Estágio 3 (embeddings) fica de fora de propósito — ver dedup.py.
        return key_hash, "NEW", None

    # ── run ──────────────────────────────────────────────────────────

    def ingest(self, jobs: list[Job]) -> RunReport:
        report = RunReport(collected=len(jobs))
        seen = self.db.seen_hashes()

        for job in jobs:
            report.by_source[job.source] = report.by_source.get(job.source, 0) + 1

            # L0 — cache de vistos. O maior descarte do pipeline, e não é
            # filtro de qualidade: é memória.
            if job.content_hash() in seen and self.db.sighting_exists(job.source, job.source_id):
                report.already_seen += 1
                continue

            cluster_id, stage, merge_score = self.resolve_cluster(job)
            if stage == "NEW":
                report.new_clusters += 1
            else:
                report.duplicates += 1

            key_hash, _ = canon_key(job.employer, job.title, job.suburb, job.postcode)
            with self.db.tx():
                self.db.upsert_cluster(cluster_id, {
                    "canon_key": key_hash,
                    "role_canon": canon_role(job.title),
                    "employer_canon": canon_employer(job.employer),
                    "title": job.title,
                    "employer": job.employer,
                    "suburb": job.suburb,
                    "postcode": job.postcode,
                    "url": job.url,
                    "source": job.source,
                    "legitimacy": job.legitimacy.value,
                    "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                })
                self.db.insert_sighting(job, cluster_id, stage, merge_score)
            seen.add(job.content_hash())

        with self.db.tx():
            report.ghosts = self.db.mark_ghosts()
        return report

    def score_pending(self, report: RunReport | None = None) -> RunReport:
        report = report or RunReport()
        rows = self.db.unscored()

        for row in rows:
            sight = self.db.conn.execute(
                "SELECT description FROM job_sighting WHERE cluster_id=? "
                "ORDER BY length(description) DESC LIMIT 1",
                (row["cluster_id"],),
            ).fetchone()
            job = Job(
                source=row["source"] or "",
                source_id=row["cluster_id"],
                title=row["title"] or "",
                url=row["url"] or "",
                employer=row["employer"],
                description=(sight["description"] if sight else "") or "",
                suburb=row["suburb"],
                postcode=row["postcode"],
            )
            dims = self.extractor.extract(job)
            ko = filters.check(job, dims, self.cfg.max_commute_km)

            with self.db.tx():
                if ko:
                    report.blocked += 1
                    report.knockouts[ko.code] = report.knockouts.get(ko.code, 0) + 1
                    self.db.save_score(row["cluster_id"], 0, "BLOCKED", ko.reason,
                                       dims, self.cfg.score_version)
                else:
                    breakdown = compute_score(
                        dims,
                        self.cfg.weights,
                        class_pattern=self.cfg.class_pattern,
                        ghost=bool(row["ghost_flag"]),
                        ghost_penalty=self.cfg.ghost_penalty,
                        multi_source=row["source_count"] or 1,
                        version=self.cfg.score_version,
                    )
                    report.scored += 1
                    self.db.save_score(row["cluster_id"], breakdown.total, "SCORED",
                                       None, dims, self.cfg.score_version)
        return report

    def run(self, sources: list[str] | None = None) -> RunReport:
        from .collectors import registry
        from .collectors import adzuna, ats, seek_v5  # noqa: F401  (registra)

        run_id = uuid.uuid4().hex[:12]
        started = datetime.now().isoformat(timespec="seconds")
        all_jobs: list[Job] = []
        errors: list[str] = []

        wanted = self.cfg.enabled_sources()
        for name, source_cfg in wanted.items():
            if sources and name not in sources:
                continue
            cls = registry.get(name)
            if cls is None:
                errors.append(f"fonte {name!r} configurada mas sem coletor")
                continue
            collector = cls(source_cfg)
            log.info("coletando de %s…", name)
            jobs = collector.safe_collect()
            errors.extend(f"{name}: {e}" for e in collector.errors)
            all_jobs.extend(jobs)
            with self.db.tx():
                self.db.log_run(f"{run_id}:{name}", name, len(jobs), 0,
                                started, "; ".join(collector.errors))

        report = self.ingest(all_jobs)
        report = self.score_pending(report)
        report.errors = errors
        return report
