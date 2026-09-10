from .interfaces import KeyExchangeProvider, SignatureProvider
from .providers import HybridKeyExchangeProvider, HybridSignatureProvider, LegacyKeyExchangeProvider, LegacySignatureProvider, PQCKeyExchangeProvider, PQCSignatureProvider


class ProviderFactory:
    @staticmethod
    def key_exchange(profile: str) -> KeyExchangeProvider:
        return {"LEGACY": LegacyKeyExchangeProvider, "HYBRID": HybridKeyExchangeProvider, "PQC": PQCKeyExchangeProvider}[profile]()
    @staticmethod
    def signature(profile: str) -> SignatureProvider:
        return {"LEGACY": LegacySignatureProvider, "HYBRID": HybridSignatureProvider, "PQC": PQCSignatureProvider}[profile]()

