"""Contrato dos coletores.

A única peça do repo de referência que valeu copiar inteira. Com seis
fontes heterogêneas, é o contrato único que impede o projeto de virar
espaguete — e é o que permite adicionar a sétima sem tocar em nada.

Um coletor NUNCA levanta exceção para fora: falha de rede numa fonte não
pode derrubar o run inteiro. Ele registra o erro e devolve o que conseguiu.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ..models import Job, Legitimacy

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


class CollectorError(RuntimeError):
    pass


class BaseCollector(ABC):
    """Molde. Todo coletor devolve `list[Job]` e nada mais."""

    name: ClassVar[str] = "base"
    legitimacy: ClassVar[Legitimacy] = Legitimacy.PUBLIC_ENDPOINT
    #: segundos entre requisições. Educação, não opcional.
    min_interval: ClassVar[float] = 1.0

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.errors: list[str] = []
        self._last_call = 0.0

    # ── utilidades ───────────────────────────────────────────────────

    def throttle(self) -> None:
        interval = float(self.config.get("min_seconds_between_calls", self.min_interval))
        elapsed = time.monotonic() - self._last_call
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_call = time.monotonic()

    def note_error(self, msg: str) -> None:
        log.warning("[%s] %s", self.name, msg)
        self.errors.append(msg)

    # ── interface ────────────────────────────────────────────────────

    @abstractmethod
    def collect(self) -> list[Job]:
        """Busca e devolve vagas. Não levanta — registra em self.errors."""

    def safe_collect(self) -> list[Job]:
        try:
            jobs = self.collect()
        except Exception as exc:  # noqa: BLE001 — de propósito
            self.note_error(f"{type(exc).__name__}: {exc}")
            return []
        log.info("[%s] %d vagas coletadas", self.name, len(jobs))
        return jobs


registry: dict[str, type[BaseCollector]] = {}


def register(cls: type[BaseCollector]) -> type[BaseCollector]:
    registry[cls.name] = cls
    return cls
