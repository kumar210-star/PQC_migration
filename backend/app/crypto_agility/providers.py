from __future__ import annotations

import json
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, mldsa, mlkem
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .interfaces import KeyExchangeProvider, SignatureProvider


class LegacyKeyExchangeProvider(KeyExchangeProvider):
    name = "ECDH P-256"
    def generate_keypair(self):
        private = ec.generate_private_key(ec.SECP256R1())
        return private, private.public_key()
    def encapsulate(self, public_key):
        ephemeral = ec.generate_private_key(ec.SECP256R1())
        secret = ephemeral.exchange(ec.ECDH(), public_key)
        return secret, ephemeral.public_key()
    def decapsulate(self, private_key, ciphertext):
        return private_key.exchange(ec.ECDH(), ciphertext)


class PQCKeyExchangeProvider(KeyExchangeProvider):
    name = "ML-KEM-768"
    def generate_keypair(self):
        private = mlkem.MLKEM768PrivateKey.generate()
        return private, private.public_key()
    def encapsulate(self, public_key):
        return public_key.encapsulate()
    def decapsulate(self, private_key, ciphertext):
        return private_key.decapsulate(ciphertext)


class LegacySignatureProvider(SignatureProvider):
    name = "ECDSA P-256"
    def generate_keypair(self):
        private = ec.generate_private_key(ec.SECP256R1())
        return private, private.public_key()
    def sign(self, message, private_key):
        return private_key.sign(message, ec.ECDSA(hashes.SHA256()))
    def verify(self, message, signature, public_key):
        try:
            public_key.verify(signature, message, ec.ECDSA(hashes.SHA256())); return True
        except InvalidSignature:
            return False
    def public_bytes(self, public_key):
        return public_key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    def public_from_bytes(self, data):
        return serialization.load_der_public_key(data)


class PQCSignatureProvider(SignatureProvider):
    name = "ML-DSA-65"
    def generate_keypair(self):
        private = mldsa.MLDSA65PrivateKey.generate()
        return private, private.public_key()
    def sign(self, message, private_key):
        return private_key.sign(message)
    def verify(self, message, signature, public_key):
        try:
            public_key.verify(signature, message); return True
        except InvalidSignature:
            return False
    def public_bytes(self, public_key):
        return public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    def public_from_bytes(self, data):
        return mldsa.MLDSA65PublicKey.from_public_bytes(data)


class HybridKeyExchangeProvider(KeyExchangeProvider):
    name = "ECDH P-256 + ML-KEM-768 (hybrid)"
    def __init__(self): self.legacy, self.pqc = LegacyKeyExchangeProvider(), PQCKeyExchangeProvider()
    def generate_keypair(self):
        lp, lu = self.legacy.generate_keypair(); qp, qu = self.pqc.generate_keypair()
        return (lp, qp), (lu, qu)
    @staticmethod
    def _combine(a: bytes, b: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"UC-024 hybrid key establishment").derive(a + b)
    def encapsulate(self, public_key):
        ls, lc = self.legacy.encapsulate(public_key[0]); qs, qc = self.pqc.encapsulate(public_key[1])
        return self._combine(ls, qs), (lc, qc)
    def decapsulate(self, private_key, ciphertext):
        return self._combine(self.legacy.decapsulate(private_key[0], ciphertext[0]), self.pqc.decapsulate(private_key[1], ciphertext[1]))


class HybridSignatureProvider(SignatureProvider):
    name = "ECDSA P-256 + ML-DSA-65 (hybrid)"
    def __init__(self): self.legacy, self.pqc = LegacySignatureProvider(), PQCSignatureProvider()
    def generate_keypair(self):
        lp, lu = self.legacy.generate_keypair(); qp, qu = self.pqc.generate_keypair()
        return (lp, qp), (lu, qu)
    def sign(self, message, private_key):
        return json.dumps([self.legacy.sign(message, private_key[0]).hex(), self.pqc.sign(message, private_key[1]).hex()]).encode()
    def verify(self, message, signature, public_key):
        try:
            a, b = json.loads(signature)
            return self.legacy.verify(message, bytes.fromhex(a), public_key[0]) and self.pqc.verify(message, bytes.fromhex(b), public_key[1])
        except (ValueError, TypeError, json.JSONDecodeError): return False
    def public_bytes(self, public_key):
        return json.dumps([self.legacy.public_bytes(public_key[0]).hex(), self.pqc.public_bytes(public_key[1]).hex()]).encode()
    def public_from_bytes(self, data):
        a, b = json.loads(data)
        return self.legacy.public_from_bytes(bytes.fromhex(a)), self.pqc.public_from_bytes(bytes.fromhex(b))

