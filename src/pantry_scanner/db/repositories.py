from typing import Protocol
from uuid import UUID

from pantry_scanner.domain.enums import ScanErrorCode
from pantry_scanner.domain.models import Ingredient, IngredientAlias, ScanRecord, ScanResult


class ScanRepository(Protocol):
    def claim_scan(self, scan_id: UUID, account_id: UUID) -> ScanRecord | None: ...

    def account_ingredients(self, account_id: UUID) -> list[Ingredient]: ...

    def catalog_ingredients(self) -> list[Ingredient]: ...

    def aliases(self, account_id: UUID) -> list[IngredientAlias]: ...

    def complete_scan(
        self,
        scan_id: UUID,
        result: ScanResult,
        warnings: list[str],
        provider: str,
        model: str,
        prompt_version: str,
        ttl_hours: int,
    ) -> bool: ...

    def fail_scan(self, scan_id: UUID, error_code: ScanErrorCode) -> bool: ...


class SweeperRepository(Protocol):
    def sweep(self) -> list[tuple[UUID, UUID, list[str]]]: ...
