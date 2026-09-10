from __future__ import annotations

from datetime import datetime, timezone

from ..models import Finding, MigrationTask


DISCLAIMER = "Educational Prototype — Not a Production Government Security Assessment"


def generate_report(inventory: list[Finding], tasks: list[MigrationTask], profile: str) -> dict:
    vulnerable = [x for x in inventory if x.risk in {"CRITICAL", "HIGH"}]
    verified = [x for x in tasks if x.status == "Verified"]
    remaining = [x for x in tasks if x.status != "Verified"]
    lines = [
        f"# UC-024 PQC Migration Report\n\n> **{DISCLAIMER}**",
        f"## 1. Executive Summary\nCitizen Secure Records has {len(inventory)} cryptographic findings; {len(vulnerable)} are quantum-vulnerable public-key uses. Current profile: **{profile}**.",
        "## 2. Cryptographic Inventory\n" + "\n".join(f"- {x.file}:{x.line} — {x.algorithm} ({x.role})" for x in inventory),
        "## 3. Detected Vulnerabilities\n" + "\n".join(f"- {x.algorithm}: {x.risk_reason}" for x in vulnerable),
        "## 4. Quantum Risk Assessment\nRisk is rule-based and does not predict when cryptographically relevant quantum computers will exist.",
        "## 5. PQC Recommendations\n" + "\n".join(f"- {x.algorithm} / {x.role} → {x.recommended_replacement}: {x.recommendation_reason}" for x in inventory),
        "## 6. Migration Priorities\n" + "\n".join(f"- [{x.priority}] {x.asset}: {x.current_algorithm} → {x.target_algorithm}" for x in tasks),
        "## 7. Crypto-Agility Architecture\nApplication operations call key-exchange and signature interfaces. A provider factory selects legacy, hybrid, or PQC implementations without changing business logic.",
        f"## 8. Migration Status\n{len(verified)} of {len(tasks)} tasks verified.",
        "## 9. Verification Results\n" + ("All planned migrations are verified." if tasks and not remaining else f"{len(remaining)} task(s) remain unverified."),
        "## 10. Remaining Risks\nOperational interoperability, certificate and key lifecycle, performance, protocol negotiation, side-channel resistance, and vendor readiness require production assessment.",
        "## 11. Recommendations\nPilot high-priority signature and key-establishment migrations; maintain algorithm inventories; add downgrade protection; rehearse rollback; validate with accredited implementations.",
        "## 12. Limitations\nThis is an educational source scanner and local demonstration. It is not a binary scanner, network discovery tool, compliance certification, or production security assessment.",
    ]
    return {"title": "UC-024 PQC Migration Report", "disclaimer": DISCLAIMER, "generated_at": datetime.now(timezone.utc).isoformat(), "profile": profile, "markdown": "\n\n".join(lines)}

