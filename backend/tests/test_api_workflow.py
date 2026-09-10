def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_complete_migration_workflow(client):
    scan = client.post("/api/scan", json={})
    assert scan.status_code == 200
    algorithms = {item["algorithm"] for item in scan.json()["findings"]}
    assert {"RSA-2048", "ECDSA P-256", "ECDH P-256", "AES-256-GCM", "SHA-256"} <= algorithms
    inventory = client.get("/api/inventory").json()
    risk = client.get("/api/risk-summary").json()
    recommendations = client.get("/api/recommendations").json()
    plan = client.get("/api/migration-plan").json()
    assert len(inventory) == 6
    assert risk["quantum_vulnerable"] == 4
    assert any(x["current_algorithm"] == "RSA-2048" and x["cryptographic_role"] == "Digital Signature" and x["recommended_algorithm"] == "ML-DSA-65" for x in recommendations)
    assert any(x["current_algorithm"] == "RSA-2048" and x["cryptographic_role"] == "Key Establishment" and x["recommended_algorithm"] == "ML-KEM-768" for x in recommendations)
    assert len(plan) == 4
    switched = client.post("/api/crypto/profile", json={"profile": "PQC"})
    assert switched.json()["profile"] == "PQC"
    signed = client.post("/api/demo/sign", json={"message": "Citizen Secure Records verification challenge"}).json()
    verified = client.post("/api/demo/verify", json={**signed["data"], "algorithm": signed["algorithm"]})
    exchanged = client.post("/api/demo/key-exchange", json={})
    assert verified.json()["success"] is True
    assert exchanged.json()["success"] is True
    assert all(x["status"] == "Verified" for x in client.get("/api/migration-plan").json())
    report = client.get("/api/report").json()
    assert "Educational Prototype" in report["disclaimer"]
    assert "## 12. Limitations" in report["markdown"]

