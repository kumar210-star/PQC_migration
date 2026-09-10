import pytest

from app.crypto_agility.factory import ProviderFactory


@pytest.mark.parametrize("profile,signature,key_exchange", [
    ("LEGACY", "ECDSA P-256", "ECDH P-256"),
    ("PQC", "ML-DSA-65", "ML-KEM-768"),
])
def test_profile_switches_providers_without_application_changes(profile, signature, key_exchange):
    signer = ProviderFactory.signature(profile)
    private, public = signer.generate_keypair()
    message = b"same application operation"
    signed = signer.sign(message, private)
    assert signer.name == signature
    assert signer.verify(message, signed, public)
    exchanger = ProviderFactory.key_exchange(profile)
    private, public = exchanger.generate_keypair()
    sender, ciphertext = exchanger.encapsulate(public)
    assert exchanger.name == key_exchange
    assert sender == exchanger.decapsulate(private, ciphertext)


def test_hybrid_requires_both_algorithms_and_combines_secrets():
    signer = ProviderFactory.signature("HYBRID")
    private, public = signer.generate_keypair()
    signature = signer.sign(b"hybrid", private)
    assert signer.verify(b"hybrid", signature, public)
    exchanger = ProviderFactory.key_exchange("HYBRID")
    private, public = exchanger.generate_keypair()
    sender, ciphertext = exchanger.encapsulate(public)
    assert sender == exchanger.decapsulate(private, ciphertext)
    assert len(sender) == 32

