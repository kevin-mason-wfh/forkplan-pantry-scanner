from datetime import UTC, datetime, timedelta
from uuid import UUID

from pantry_scanner.domain.enums import ScanErrorCode, ScanStatus
from pantry_scanner.domain.models import (
    Ingredient,
    IngredientAlias,
    ScanRecord,
    ScanResult,
)


class MemoryRepository:
    def __init__(
        self,
        scans: list[ScanRecord] | None = None,
        ingredients: list[Ingredient] | None = None,
        catalog: list[Ingredient] | None = None,
        aliases: list[IngredientAlias] | None = None,
    ) -> None:
        self.scans = {scan.id: scan for scan in scans or []}
        self.ingredients = ingredients or []
        self.catalog = catalog or []
        self.saved_aliases = aliases or []
        self.results: dict[UUID, ScanResult] = {}
        self.warnings: dict[UUID, list[str]] = {}
        self.errors: dict[UUID, ScanErrorCode] = {}
        self.provider_metadata: dict[UUID, tuple[str, str, str]] = {}

    def claim_scan(self, scan_id: UUID, account_id: UUID) -> ScanRecord | None:
        scan = self.scans.get(scan_id)
        if scan is None or scan.account_id != account_id or scan.status != ScanStatus.QUEUED:
            return None
        claimed = scan.model_copy(
            update={"status": ScanStatus.ANALYSING, "started_at": datetime.now(UTC)}
        )
        self.scans[scan_id] = claimed
        return claimed

    def account_ingredients(self, account_id: UUID) -> list[Ingredient]:
        return [
            ingredient
            for ingredient in self.ingredients
            if ingredient.account_id == account_id and ingredient.archived_at is None
        ]

    def catalog_ingredients(self) -> list[Ingredient]:
        return list(self.catalog)

    def aliases(self, account_id: UUID) -> list[IngredientAlias]:
        return [alias for alias in self.saved_aliases if alias.account_id == account_id]

    def complete_scan(
        self,
        scan_id: UUID,
        result: ScanResult,
        warnings: list[str],
        provider: str,
        model: str,
        prompt_version: str,
        ttl_hours: int,
    ) -> bool:
        scan = self.scans.get(scan_id)
        if scan is None or scan.status != ScanStatus.ANALYSING:
            return False
        completed_at = datetime.now(UTC)
        self.scans[scan_id] = scan.model_copy(
            update={
                "status": ScanStatus.COMPLETED,
                "result": result,
                "warnings": warnings,
                "provider": provider,
                "model": model,
                "prompt_version": prompt_version,
                "completed_at": completed_at,
                "expires_at": completed_at + timedelta(hours=ttl_hours),
            }
        )
        self.results[scan_id] = result
        self.warnings[scan_id] = warnings
        self.provider_metadata[scan_id] = (provider, model, prompt_version)
        return True

    def fail_scan(self, scan_id: UUID, error_code: ScanErrorCode) -> bool:
        scan = self.scans.get(scan_id)
        if scan is None or scan.status != ScanStatus.ANALYSING:
            return False
        self.scans[scan_id] = scan.model_copy(
            update={"status": ScanStatus.FAILED, "error_code": error_code}
        )
        self.errors[scan_id] = error_code
        return True


class MemorySweeperRepository:
    def __init__(self, objects_to_delete: list[tuple[UUID, UUID, list[str]]] | None = None) -> None:
        self.objects_to_delete = objects_to_delete or []
        self.called = False

    def sweep(self) -> list[tuple[UUID, UUID, list[str]]]:
        self.called = True
        return list(self.objects_to_delete)
