from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database.store import Store
from app import main


@pytest.fixture
def client(tmp_path):
    main.store = Store(tmp_path / "test.db")
    with TestClient(main.app) as test_client:
        yield test_client

