from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Profile(StrEnum):
    LEGACY = "LEGACY"
    HYBRID = "HYBRID"
    PQC = "PQC"


class Finding(BaseModel):
    id: int | None = None
    asset: str
    file: str
    line: int
    evidence: str
    algorithm: str
    category: str
    role: str
    parameter: str | None = None
    risk: str
    risk_reason: str
    recommended_replacement: str
    recommendation_reason: str
    migration_action: str
    priority: str
    status: str = "Not Started"


class ScanRequest(BaseModel):
    path: str | None = None


class ScanResponse(BaseModel):
    scanned_files: int
    findings: list[Finding]


class Recommendation(BaseModel):
    inventory_id: int
    current_algorithm: str
    cryptographic_role: str
    risk: str
    recommended_algorithm: str
    reason: str
    migration_action: str
    priority: str
    alternative_algorithms: list[str] = Field(default_factory=list)


class MigrationTask(BaseModel):
    id: int | None = None
    inventory_id: int
    asset: str
    current_algorithm: str
    cryptographic_role: str
    target_algorithm: str
    reason: str
    priority: str
    dependencies: list[str] = Field(default_factory=list)
    status: str = "Not Started"


class MigrationUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, value: str) -> str:
        allowed = {"Not Started", "Planned", "In Progress", "Migrated", "Verified"}
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class ProfileUpdate(BaseModel):
    profile: Profile


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000)


class VerifyRequest(MessageRequest):
    signature: str
    public_key: str
    algorithm: str


class DemoResult(BaseModel):
    success: bool
    profile: Profile
    algorithm: str
    detail: str
    data: dict[str, Any] = Field(default_factory=dict)
