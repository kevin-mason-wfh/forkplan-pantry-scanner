from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from pantry_scanner.domain.enums import IngredientCategory, MatchConfidence, QuantityBasis, Unit


class RawDetection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: IngredientCategory
    amount: Decimal | None = None
    unit: Unit | None = None
    basis: QuantityBasis | None = None
    confidence: MatchConfidence
    is_lower_bound: bool = False
    notes: str | None = None


class RawDetections(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RawDetection] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class VisionProvider(Protocol):
    def analyse(self, images: list[bytes], location: str, timeout_s: float) -> RawDetections: ...
