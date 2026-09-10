from __future__ import annotations


class RecommendationEngine:
    def recommend(self, algorithm: str, family: str, role: str, category: str, risk: str) -> dict[str, str]:
        role_lower = role.lower()
        if category == "Public-key cryptography" and ("signature" in role_lower or family == "ECDSA"):
            return {"algorithm": "ML-DSA-65", "reason": "ML-DSA is a NIST-standardized post-quantum digital-signature scheme and preserves the signature role.", "action": "Introduce the signature-provider interface, issue ML-DSA credentials, update trust stores, and verify signatures end to end."}
        if category == "Public-key cryptography" and ("key" in role_lower or "encrypt" in role_lower or family in {"ECDH", "DH"}):
            return {"algorithm": "ML-KEM-768", "reason": "ML-KEM is a NIST-standardized post-quantum key-encapsulation mechanism and matches the key-establishment role.", "action": "Introduce the key-exchange-provider interface, negotiate ML-KEM, rotate dependent keys, and verify shared-secret agreement."}
        if category == "Public-key cryptography" and family == "RSA":
            return {"algorithm": "Role review required", "reason": "RSA can serve encryption/key establishment or signatures; the replacement depends on the actual cryptographic role.", "action": "Confirm the call site's role, then select ML-KEM for key establishment or ML-DSA for signatures."}
        if category == "Symmetric cryptography":
            target = "AES-256-GCM" if algorithm == "AES-128" else "Retain"
            return {"algorithm": target, "reason": "Symmetric encryption is not replaced by a KEM or signature algorithm; retain strong configurations and review key management.", "action": "Review key length, nonce discipline, rotation, and the public-key mechanism that protects symmetric keys."}
        return {"algorithm": "Retain / review usage", "reason": "Hashing is a distinct role and should not be replaced with ML-KEM or ML-DSA.", "action": "Document the hash purpose and retain unless protocol or assurance requirements call for a change."}

    @staticmethod
    def infer_role(configured_role: str, line: str, family: str) -> str:
        if configured_role != "Contextual":
            return configured_role
        text = line.lower()
        if any(word in text for word in ("sign", "signature", "certificate", "auth")):
            return "Digital Signature"
        if any(word in text for word in ("encrypt", "wrap", "transport", "exchange", "establish", "kem")):
            return "Key Establishment"
        return "Role Review Required" if family in {"RSA", "ECC"} else configured_role

