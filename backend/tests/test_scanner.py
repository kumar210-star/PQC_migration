from pathlib import Path

from app.scanner.scanner import CryptoScanner


def test_detects_required_algorithms_and_locations(tmp_path: Path):
    source = tmp_path / "crypto.py"
    source.write_text('\n'.join([
        'sig = "ECDSA P-256"', 'exchange = "ECDH P-256"', 'key = "RSA-2048 signature"',
        'cipher = "AES-256-GCM"', 'digest = "SHA-256"'
    ]), encoding="utf-8")
    scanned, findings = CryptoScanner().scan(tmp_path)
    by_algorithm = {item.algorithm: item for item in findings}
    assert scanned == 1
    assert {"ECDSA P-256", "ECDH P-256", "RSA-2048", "AES-256-GCM", "SHA-256"} <= set(by_algorithm)
    assert by_algorithm["ECDSA P-256"].file == "crypto.py"
    assert by_algorithm["ECDSA P-256"].line == 1
    assert by_algorithm["RSA-2048"].role == "Digital Signature"


def test_detects_rsa_key_establishment_by_context(tmp_path: Path):
    (tmp_path / "keys.conf").write_text("archive_key_transport = RSA-3072 encryption", encoding="utf-8")
    _, findings = CryptoScanner().scan(tmp_path)
    assert findings[0].role == "Key Establishment"
    assert findings[0].recommended_replacement == "ML-KEM-768"

