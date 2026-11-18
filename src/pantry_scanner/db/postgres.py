from uuid import UUID

from pantry_scanner.db.repositories import ScanRepository, SweeperRepository
from pantry_scanner.domain.enums import ScanErrorCode
from pantry_scanner.domain.models import Ingredient, IngredientAlias, ScanRecord, ScanResult


class PostgresRepository(ScanRepository, SweeperRepository):
    def claim_scan(self, scan_id: UUID, account_id: UUID) -> ScanRecord | None:
        raise NotImplementedError("Postgres repositories are deferred")

    def account_ingredients(self, account_id: UUID) -> list[Ingredient]:
        raise NotImplementedError("Postgres repositories are deferred")

    def catalog_ingredients(self) -> list[Ingredient]:
        raise NotImplementedError("Postgres repositories are deferred")

    def aliases(self, account_id: UUID) -> list[IngredientAlias]:
        raise NotImplementedError("Postgres repositories are deferred")

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
        raise NotImplementedError("Postgres repositories are deferred")

    def fail_scan(self, scan_id: UUID, error_code: ScanErrorCode) -> bool:
        raise NotImplementedError("Postgres repositories are deferred")

    def sweep(self) -> list[tuple[UUID, UUID, list[str]]]:
        raise NotImplementedError("Sweeper SQL is deferred")
