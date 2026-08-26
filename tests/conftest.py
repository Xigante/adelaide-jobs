import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def adzuna_payload() -> dict:
    return json.loads((FIXTURES / "adzuna_search.json").read_text(encoding="utf-8"))


@pytest.fixture
def seek_payload() -> dict:
    return json.loads((FIXTURES / "seek_v5_search.json").read_text(encoding="utf-8"))


@pytest.fixture
def cfg():
    from adelaide_jobs import config
    return config.load(ROOT / "config")


@pytest.fixture
def db(tmp_path):
    from adelaide_jobs.db import Database
    d = Database(tmp_path / "test.db")
    yield d
    d.close()
