from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROOT = PROJECT_ROOT / "sample-project"
DATA_DIR = PROJECT_ROOT / "backend" / "data"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", DATA_DIR / "pqc.db"))
DEFAULT_PROFILE = os.getenv("CRYPTO_PROFILE", "LEGACY").upper()
ALLOWED_PROFILES = {"LEGACY", "HYBRID", "PQC"}

