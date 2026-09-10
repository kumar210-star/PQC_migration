from __future__ import annotations

import json
from pathlib import Path


class RiskEngine:
    def __init__(self, rules_path: Path | None = None) -> None:
        path = rules_path or Path(__file__).with_name("rules.json")
        self.rules = json.loads(path.read_text(encoding="utf-8"))

    def assess(self, family: str, category: str) -> dict[str, str]:
        section = "public_key" if category.startswith("Public") else "symmetric" if category.startswith("Symmetric") else "hash"
        return self.rules.get(section, {}).get(
            family,
            {"risk": "REVIEW", "priority": "MEDIUM", "reason": "No explicit rule matched; a cryptography owner should review this use."},
        )

