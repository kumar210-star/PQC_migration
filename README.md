# UC-024 — Post-Quantum Cryptography Migration Platform

> **Educational Prototype — Not a Production Government Security Assessment**

UC-024 is a complete local prototype showing how a government organization can **discover vulnerable cryptography → understand the risk → select a role-appropriate PQC replacement → migrate through a crypto-agile architecture → verify the migration → generate a report**.

The fictional **Citizen Secure Records** sample contains synthetic configuration only. No real citizen data, credentials, or private keys are stored.

## What works

- Configurable static scanner with exact file and line evidence
- SQLite cryptographic inventory and migration-task persistence
- Transparent, configurable quantum-risk rules
- Role-aware recommendations: key establishment → ML-KEM; signatures → ML-DSA
- Optional SLH-DSA recommendation context (not required by the first demo)
- Stable `KeyExchangeProvider` and `SignatureProvider` interfaces
- Real ECDH P-256 / ECDSA P-256 legacy providers
- Real ML-KEM-768 / ML-DSA-65 providers through `cryptography` 50 and OpenSSL
- Real hybrid mode: ECDH + ML-KEM secrets combined with HKDF-SHA-256; both ECDSA and ML-DSA signatures must verify
- FastAPI/OpenAPI API, React/Vite dashboard, migration verification, and Markdown report export
- Unit and end-to-end workflow tests

## Quick start

Requirements: Python 3.12+, Node.js 20+, npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd frontend
npm install
cd ..
```

Start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

In a second terminal, start the dashboard:

```powershell
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`. API documentation is at `http://127.0.0.1:8000/docs`.

## Required demo walkthrough

1. Open **Dashboard** and click **Scan Demo Government System**.
2. Review RSA-2048, ECDSA P-256, ECDH P-256, AES-256-GCM, and SHA-256 findings.
3. Open **Risk Analysis** to see why public-key, symmetric, and hashing risks differ.
4. Open **PQC Recommendations** to inspect role-aware mappings. The two RSA call sites demonstrate both mappings: signature → ML-DSA and key establishment → ML-KEM.
5. Open **Migration Plan** to review automatically generated tasks.
6. Open **Migration Demo**, switch from `LEGACY` to `PQC`, and run verification.
7. Signature and key-establishment tasks become `Verified` only after real provider operations succeed.
8. Open **Reports** and generate/download the assessment.

## Architecture

```text
React dashboard
      │
FastAPI + Pydantic
      │
Inventory scanner ─ Risk engine ─ Recommendation engine ─ Migration planner
      │                                                        │
    SQLite                                            Report generator
      │
ProviderFactory
  ├─ SignatureProvider ─ ECDSA / ML-DSA / hybrid
  └─ KeyExchangeProvider ─ ECDH / ML-KEM / hybrid
```

Application operations depend on interfaces, not algorithm classes. `POST /api/crypto/profile` changes the factory's selected provider while signing and key-establishment call sites remain unchanged.

## Cryptography and quantum risk

### What Shor's algorithm changes

RSA security depends on integer factorization. ECC, ECDH, and ECDSA depend on elliptic-curve discrete logarithms. A sufficiently large, fault-tolerant quantum computer running Shor's algorithm could solve these problems efficiently. This prototype does **not** predict when such a computer will exist.

Long-lived confidential data can face **harvest now, decrypt later** risk: an adversary records protected traffic today and waits for future quantum capability. Inventory and migration planning therefore matter before a quantum break occurs.

### What PQC means

Post-quantum cryptography uses mathematical problems believed resistant to known classical and quantum attacks while running on conventional computers. Migration still requires protocol, interoperability, implementation, side-channel, key-lifecycle, and operational validation.

### ML-KEM

ML-KEM is a NIST-standardized key-encapsulation mechanism:

1. The recipient generates a public/private keypair.
2. The sender encapsulates to the public key, producing a ciphertext and shared secret.
3. The recipient decapsulates the ciphertext with the private key.
4. Both sides obtain the same shared secret, which can feed a suitable key-derivation and symmetric-encryption design.

### ML-DSA

ML-DSA is a NIST-standardized digital-signature scheme:

1. The signer generates a public/private keypair.
2. The private key signs a message.
3. The public key verifies authenticity and integrity.

SLH-DSA is a standardized hash-based alternative signature family. It is an optional recommendation where its trade-offs are appropriate; this first demo uses ML-DSA.

### Important boundaries

- **KEM ≠ digital signature.** A KEM establishes key material; it does not authenticate a signed document.
- **KEM ≠ AES.** AES encrypts data symmetrically; ML-KEM helps establish the AES key.
- **ML-DSA ≠ encryption.** It authenticates and protects integrity.
- **AES-256-GCM ≠ PQC.** It is conventional symmetric authenticated encryption with a strong quantum security margin.
- **HKDF ≠ encryption.** It derives key material.
- **Hashing ≠ encryption.** Hashing is one-way and has no decryption key.

## Configurable rules

- Scanner patterns: `backend/app/scanner/rules.json`
- Risk classifications and explanations: `backend/app/risk/rules.json`
- Role mapping logic: `backend/app/recommendations/engine.py`

Rules are separated from scanning mechanics so new algorithms can be added without rewriting traversal and evidence reporting.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service and PQC backend status |
| POST | `/api/scan` | Scan the bundled synthetic project |
| GET | `/api/inventory` | Stored findings |
| GET | `/api/risk-summary` | Classification totals |
| GET | `/api/recommendations` | Role-aware actions |
| GET | `/api/migration-plan` | Generate/read tasks |
| PATCH | `/api/migration/{id}` | Update a task status |
| GET/POST | `/api/crypto/profile` | Read/change provider profile |
| POST | `/api/demo/sign` | Sign through the active provider |
| POST | `/api/demo/verify` | Verify through the active provider |
| POST | `/api/demo/key-exchange` | Exercise key establishment |
| GET | `/api/report` | Generate the current report |

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
cd frontend
npm run build
```

The suite covers scanner detections and locations, risk rules, role-aware mappings, task generation, legacy/PQC/hybrid providers, major APIs, and the complete scan-to-report workflow.

## Security boundaries and limitations

- This is a source/configuration scanner, not binary analysis, live network discovery, or a full cryptographic bill of materials tool.
- Findings depend on detectable text and contextual role inference; expert validation is required.
- The dashboard uses ephemeral demo keys only. It does not provide HSM/KMS integration, certificate lifecycle management, or production protocol negotiation.
- Real primitives do not automatically make the surrounding educational protocol production-safe.
- Production adoption requires approved modules, threat modeling, performance tests, side-channel review, interoperability testing, downgrade protection, operational controls, and applicable government accreditation.

