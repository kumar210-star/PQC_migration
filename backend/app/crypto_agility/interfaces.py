from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KeyExchangeProvider(ABC):
    name: str
    @abstractmethod
    def generate_keypair(self) -> tuple[Any, Any]: ...
    @abstractmethod
    def encapsulate(self, public_key: Any) -> tuple[bytes, Any]: ...
    @abstractmethod
    def decapsulate(self, private_key: Any, ciphertext: Any) -> bytes: ...


class SignatureProvider(ABC):
    name: str
    @abstractmethod
    def generate_keypair(self) -> tuple[Any, Any]: ...
    @abstractmethod
    def sign(self, message: bytes, private_key: Any) -> bytes: ...
    @abstractmethod
    def verify(self, message: bytes, signature: bytes, public_key: Any) -> bool: ...
    @abstractmethod
    def public_bytes(self, public_key: Any) -> bytes: ...
    @abstractmethod
    def public_from_bytes(self, data: bytes) -> Any: ...

