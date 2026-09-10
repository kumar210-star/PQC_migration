from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import SAMPLE_ROOT
from .crypto_agility.factory import ProviderFactory
from .database.store import Store
from .migration.planner import MigrationPlanner
from .models import DemoResult, MigrationTask, MigrationUpdate, Profile, ProfileUpdate, Recommendation, ScanRequest, ScanResponse, VerifyRequest, MessageRequest
from .report.generator import generate_report
from .scanner.scanner import CryptoScanner

store = Store()


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    yield


app = FastAPI(title="UC-024 PQC Migration Platform", version="1.0.0", description="Educational prototype for crypto-agile government PQC migration.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "UC-024", "pqc_backend": "cryptography/OpenSSL ML-KEM + ML-DSA"}


@app.post("/api/scan", response_model=ScanResponse)
def scan(request: ScanRequest = ScanRequest()):
    if request.path not in {None, "", ".", "sample-project"}:
        raise HTTPException(400, "This educational prototype only scans the bundled sample-project")
    scanned, findings = CryptoScanner().scan(SAMPLE_ROOT)
    return ScanResponse(scanned_files=scanned, findings=store.replace_inventory(findings))


@app.get("/api/inventory")
def inventory(): return store.inventory()


@app.get("/api/risk-summary")
def risk_summary():
    items = store.inventory()
    counts = {key: sum(x.risk == key for x in items) for key in ("CRITICAL", "HIGH", "REVIEW", "LOWER")}
    return {"total": len(items), "quantum_vulnerable": counts["CRITICAL"] + counts["HIGH"], "counts": counts, "note": "Rule-based prioritization; no quantum-break date prediction."}


@app.get("/api/recommendations", response_model=list[Recommendation])
def recommendations():
    return [Recommendation(inventory_id=x.id or 0, current_algorithm=x.algorithm, cryptographic_role=x.role, risk=x.risk, recommended_algorithm=x.recommended_replacement, reason=x.recommendation_reason, migration_action=x.migration_action, priority=x.priority, alternative_algorithms=["SLH-DSA"] if x.recommended_replacement.startswith("ML-DSA") else []) for x in store.inventory()]


@app.get("/api/migration-plan", response_model=list[MigrationTask])
def migration_plan():
    existing = store.tasks()
    return existing or store.replace_tasks(MigrationPlanner().generate(store.inventory()))


@app.patch("/api/migration/{task_id}", response_model=MigrationTask)
def update_migration(task_id: int, update: MigrationUpdate):
    task = store.update_task(task_id, update.status)
    if not task: raise HTTPException(404, "Migration task not found")
    return task


@app.get("/api/crypto/profile")
def get_profile(): return {"profile": store.profile(), "profiles": [x.value for x in Profile], "hybrid_note": "HYBRID performs both classical and PQC operations and combines key-establishment secrets with HKDF-SHA-256."}


@app.post("/api/crypto/profile")
def set_profile(update: ProfileUpdate):
    store.set_profile(update.profile.value)
    return {"profile": update.profile, "message": "Provider factory configuration updated; application-level interfaces are unchanged."}


@app.post("/api/demo/sign", response_model=DemoResult)
def sign(request: MessageRequest):
    profile = store.profile(); provider = ProviderFactory.signature(profile)
    private, public = provider.generate_keypair(); signature = provider.sign(request.message.encode(), private)
    return DemoResult(success=True, profile=Profile(profile), algorithm=provider.name, detail="Message signed through the SignatureProvider interface.", data={"message": request.message, "signature": base64.b64encode(signature).decode(), "public_key": base64.b64encode(provider.public_bytes(public)).decode()})


@app.post("/api/demo/verify", response_model=DemoResult)
def verify(request: VerifyRequest):
    profile = store.profile(); provider = ProviderFactory.signature(profile)
    if request.algorithm != provider.name: raise HTTPException(400, "Signature algorithm does not match the active provider")
    try:
        ok = provider.verify(request.message.encode(), base64.b64decode(request.signature, validate=True), provider.public_from_bytes(base64.b64decode(request.public_key, validate=True)))
    except (ValueError, TypeError) as exc: raise HTTPException(400, "Invalid encoded key or signature") from exc
    if ok and profile == "PQC": store.mark_by_role("signature", "Verified")
    return DemoResult(success=ok, profile=Profile(profile), algorithm=provider.name, detail="Signature verified through the same high-level interface." if ok else "Signature verification failed.")


@app.post("/api/demo/key-exchange", response_model=DemoResult)
def key_exchange():
    profile = store.profile(); provider = ProviderFactory.key_exchange(profile)
    private, public = provider.generate_keypair(); sender_secret, ciphertext = provider.encapsulate(public); receiver_secret = provider.decapsulate(private, ciphertext)
    ok = sender_secret == receiver_secret
    if ok and profile == "PQC": store.mark_by_role("key establishment", "Verified")
    return DemoResult(success=ok, profile=Profile(profile), algorithm=provider.name, detail="Both parties derived the same shared secret through the KeyExchangeProvider interface.", data={"shared_secret_match": ok, "secret_length_bytes": len(sender_secret)})


@app.get("/api/report")
def report(): return generate_report(store.inventory(), store.tasks(), store.profile())
