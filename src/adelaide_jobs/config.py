"""Carregamento de configuração. Nada de valor mágico no código."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config não encontrada: {path}")
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass(slots=True)
class Config:
    profile: dict[str, Any]
    sources: dict[str, Any]

    # ── atalhos usados em vários lugares ─────────────────────────────

    @property
    def weights(self) -> dict[str, int]:
        return (self.profile.get("scoring") or {}).get("weights") or {}

    @property
    def score_version(self) -> str:
        return (self.profile.get("scoring") or {}).get("version", "w1")

    @property
    def ghost_penalty(self) -> float:
        return float((self.profile.get("scoring") or {}).get("ghost_penalty", 15))

    @property
    def queue_threshold(self) -> int:
        return int((self.profile.get("scoring") or {}).get("queue_threshold", 55))

    @property
    def max_commute_km(self) -> float:
        return float((self.profile.get("transport") or {}).get("max_commute_km", 25))

    @property
    def class_pattern(self) -> str:
        return (self.profile.get("study") or {}).get("class_pattern", "UNKNOWN")

    @property
    def boh_keywords(self) -> list[str]:
        return self.profile.get("boh_keywords") or []

    def enabled_sources(self) -> dict[str, dict[str, Any]]:
        return {k: v for k, v in self.sources.items()
                if isinstance(v, dict) and v.get("enabled")}


def load(config_dir: str | Path | None = None) -> Config:
    load_dotenv()
    base = Path(config_dir) if config_dir else CONFIG_DIR
    return Config(
        profile=_read_yaml(base / "profile.yaml"),
        sources=_read_yaml(base / "sources.yaml"),
    )
