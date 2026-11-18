from datetime import UTC, datetime
from uuid import UUID

import pytest

from pantry_scanner.config import Settings
from pantry_scanner.db.memory import MemoryRepository
from pantry_scanner.domain.enums import IngredientCategory, ScanStatus, Unit
from pantry_scanner.domain.models import Ingredient, ScanRecord

ACCOUNT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
SCAN_ID = UUID("11111111-2222-4333-8444-555555555555")
INGREDIENT_ID = UUID("33333333-4444-4555-8666-777777777777")
KEY = f"scan-temp/{ACCOUNT_ID}/{SCAN_ID}/0.jpg"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        provider="claude",
        model="test-model",
        scan_bucket="test-bucket",
        ssm_prefix="/test/pantry",
        max_image_edge=1600,
        jpeg_quality=85,
        provider_timeout_seconds=90,
        result_ttl_hours=24,
        statement_timeout_ms=5000,
    )


@pytest.fixture
def queued_scan() -> ScanRecord:
    return ScanRecord(
        id=SCAN_ID,
        account_id=ACCOUNT_ID,
        status=ScanStatus.QUEUED,
        location="fridge",
        image_keys=[KEY],
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def account_ingredient() -> Ingredient:
    return Ingredient(
        id=INGREDIENT_ID,
        account_id=ACCOUNT_ID,
        name="Milk",
        normalized_name="milk",
        unit=Unit.MILLILITERS,
        category=IngredientCategory.DAIRY,
    )


@pytest.fixture
def memory_repository(queued_scan: ScanRecord, account_ingredient: Ingredient) -> MemoryRepository:
    return MemoryRepository(scans=[queued_scan], ingredients=[account_ingredient])
