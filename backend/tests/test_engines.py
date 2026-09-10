from app.migration.planner import MigrationPlanner
from app.models import Finding
from app.recommendations.engine import RecommendationEngine
from app.risk.engine import RiskEngine


def test_risk_rules_distinguish_algorithm_categories():
    engine = RiskEngine()
    assert engine.assess("RSA", "Public-key cryptography")["risk"] == "CRITICAL"
    assert engine.assess("AES-128", "Symmetric cryptography")["risk"] == "REVIEW"
    assert engine.assess("AES-256-GCM", "Symmetric cryptography")["risk"] == "LOWER"
    assert engine.assess("SHA-256", "Hashing")["risk"] == "LOWER"


def test_recommendations_are_role_aware():
    engine = RecommendationEngine()
    rsa_signature = engine.recommend("RSA-2048", "RSA", "Digital Signature", "Public-key cryptography", "CRITICAL")
    rsa_exchange = engine.recommend("RSA-2048", "RSA", "Key Establishment", "Public-key cryptography", "CRITICAL")
    aes = engine.recommend("AES-256-GCM", "AES-256-GCM", "Authenticated Encryption", "Symmetric cryptography", "LOWER")
    sha = engine.recommend("SHA-256", "SHA-256", "Hashing", "Hashing", "LOWER")
    assert rsa_signature["algorithm"] == "ML-DSA-65"
    assert rsa_exchange["algorithm"] == "ML-KEM-768"
    assert aes["algorithm"] == "Retain"
    assert sha["algorithm"] == "Retain / review usage"


def finding(**overrides):
    data = dict(asset="auth", file="a.py", line=1, evidence="", algorithm="ECDSA",
                category="Public-key cryptography", role="Digital Signature", risk="CRITICAL",
                risk_reason="reason", recommended_replacement="ML-DSA-65",
                recommendation_reason="why", migration_action="act", priority="CRITICAL")
    data.update(overrides)
    return Finding(**data)


def test_planner_excludes_retain_findings():
    vulnerable = finding(id=1)
    retained = finding(id=2, asset="data", algorithm="SHA-256", category="Hashing", role="Hashing",
                       risk="LOWER", recommended_replacement="Retain / review usage", priority="LOW")
    tasks = MigrationPlanner().generate([vulnerable, retained])
    assert len(tasks) == 1
    assert tasks[0].target_algorithm == "ML-DSA-65"
    assert tasks[0].status == "Planned"

