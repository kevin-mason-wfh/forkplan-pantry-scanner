from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from pantry_scanner.domain.enums import (
    IngredientCategory,
    MatchConfidence,
    MatchSource,
    QuantityBasis,
    ScanErrorCode,
    ScanStatus,
    Unit,
)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ScanMessage(ContractModel):
    v: Literal[1]
    scan_id: UUID
    account_id: UUID


class Match(ContractModel):
    source: MatchSource | None = None
    ingredient_id: UUID | None = None
    catalog_ingredient_id: UUID | None = None
    name: str | None = None
    unit: Unit | None = None
    confidence: MatchConfidence = MatchConfidence.NONE


class Quantity(ContractModel):
    amount: Decimal | None = None
    unit: Unit | None = None
    basis: QuantityBasis | None = None
    confidence: MatchConfidence = MatchConfidence.NONE
    is_lower_bound: bool = False
    unit_mismatch: bool = False


class ScanItem(ContractModel):
    temp_id: UUID = Field(default_factory=uuid4)
    detected_name: str
    match: Match = Field(default_factory=Match)
    suggested_category: IngredientCategory
    quantity: Quantity = Field(default_factory=Quantity)
    notes: str | None = None


class ScanResult(ContractModel):
    items: list[ScanItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScanRecord(ContractModel):
    id: UUID
    account_id: UUID
    user_id: str | None = None
    pantry_id: UUID | None = None
    location: str | None = None
    status: ScanStatus
    image_count: int = 0
    image_keys: list[str] = Field(default_factory=list)
    result: ScanResult | None = None
    warnings: list[str] = Field(default_factory=list)
    error_code: ScanErrorCode | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None


class Ingredient(ContractModel):
    id: UUID
    account_id: UUID | None = None
    name: str
    normalized_name: str
    unit: Unit | None = None
    size: Decimal | None = None
    category: IngredientCategory
    archived_at: datetime | None = None


class IngredientAlias(ContractModel):
    account_id: UUID
    normalized_alias: str
    ingredient_source: MatchSource
    ingredient_id: UUID | None = None
    catalog_ingredient_id: UUID | None = None
