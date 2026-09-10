from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import Finding
from ..recommendations.engine import RecommendationEngine
from ..risk.engine import RiskEngine


class CryptoScanner:
    EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".java", ".go", ".cs", ".conf", ".ini", ".yaml", ".yml", ".json", ".env", ".txt"}

    def __init__(self, rules_path: Path | None = None) -> None:
        path = rules_path or Path(__file__).with_name("rules.json")
        self.rules = json.loads(path.read_text(encoding="utf-8"))
        self.risk = RiskEngine()
        self.recommendations = RecommendationEngine()

    def scan(self, root: Path) -> tuple[int, list[Finding]]:
        findings: list[Finding] = []
        scanned = 0
        for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in self.EXTENSIONS):
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="ignore")
            for number, line in enumerate(text.splitlines(), 1):
                occupied: list[tuple[int, int]] = []
                for rule in self.rules:
                    for match in re.finditer(rule["pattern"], line):
                        if any(match.start() < end and match.end() > start for start, end in occupied):
                            continue
                        occupied.append(match.span())
                        role = self.recommendations.infer_role(rule["role"], line, rule["family"])
                        assessment = self.risk.assess(rule["family"], rule["category"])
                        rec = self.recommendations.recommend(rule["name"], rule["family"], role, rule["category"], assessment["risk"])
                        rel = path.relative_to(root).as_posix()
                        findings.append(Finding(
                            asset=rel.split("/")[0], file=rel, line=number, evidence=line.strip()[:240],
                            algorithm=rule["name"], category=rule["category"], role=role,
                            parameter=rule.get("parameter"), risk=assessment["risk"], risk_reason=assessment["reason"],
                            recommended_replacement=rec["algorithm"], recommendation_reason=rec["reason"],
                            migration_action=rec["action"], priority=assessment["priority"],
                        ))
        return scanned, findings

