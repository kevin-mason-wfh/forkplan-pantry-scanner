from decimal import Decimal
from io import BytesIO

from PIL import Image
from tests.conftest import ACCOUNT_ID, SCAN_ID

from pantry_scanner.domain.enums import (
    IngredientCategory,
    MatchSource,
    QuantityBasis,
    ScanErrorCode,
    ScanStatus,
    Unit,
)
from pantry_scanner.domain.models import ScanMessage
from pantry_scanner.pipeline import CatalogCache, ScanWorker
from pantry_scanner.vision.base import RawDetection, RawDetections
from pantry_scanner.vision.fake import FakeProvider

VALID = RawDetections(
    items=[
        RawDetection(
            name="milk",
            category=IngredientCategory.DAIRY,
            amount=Decimal("1"),
            unit=Unit.LITERS,
            basis=QuantityBasis.LABEL,
            confidence="high",
            is_lower_bound=True,
        )
    ]
)


class MemoryImages:
    def __init__(self, values: dict[str, bytes] | None = None) -> None:
        output = BytesIO()
        Image.new("RGB", (20, 10), "green").save(output, "JPEG")
        self.values = values or {"scan-temp/account/scan/0.jpg": output.getvalue()}
        self.deleted: list[str] = []

    def get(self, key: str) -> bytes:
        return self.values[key]

    def delete(self, key: str) -> None:
        self.deleted.append(key)


class SequenceProvider:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def analyse(self, images: list[bytes], location: str, timeout_s: float) -> object:
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def worker(repository, settings, provider, images=None) -> ScanWorker:
    return ScanWorker(repository, images or MemoryImages(), provider, settings)


def message() -> ScanMessage:
    return ScanMessage(v=1, scan_id=SCAN_ID, account_id=ACCOUNT_ID)


def test_success_claims_completes_and_deletes_photo(memory_repository, settings) -> None:
    images = MemoryImages()
    provider = FakeProvider(VALID)
    worker(memory_repository, settings, provider, images).process(message())

    assert memory_repository.scans[SCAN_ID].status == ScanStatus.COMPLETED
    assert memory_repository.scans[SCAN_ID].result is not None
    assert memory_repository.scans[SCAN_ID].provider == "claude"
    assert images.deleted == ["scan-temp/account/scan/0.jpg"]
    item = memory_repository.results[SCAN_ID].items[0]
    assert item.match.source == MatchSource.ACCOUNT
    assert item.quantity.amount == Decimal("1000")
    assert item.quantity.unit == Unit.MILLILITERS
    assert item.quantity.is_lower_bound is True


def test_duplicate_delivery_does_not_call_provider(memory_repository, settings) -> None:
    provider = FakeProvider(VALID)
    scan_worker = worker(memory_repository, settings, provider)
    scan_worker.process(message())
    scan_worker.process(message())
    assert len(provider.calls) == 1


def test_invalid_schema_retries_once(memory_repository, settings) -> None:
    provider = SequenceProvider([{"items": [{"name": "milk"}]}, VALID])
    worker(memory_repository, settings, provider).process(message())
    assert provider.calls == 2
    assert memory_repository.scans[SCAN_ID].status == ScanStatus.COMPLETED


def test_provider_timeout_fails_without_retry_and_deletes_photo(
    memory_repository, settings
) -> None:
    provider = SequenceProvider([TimeoutError()])
    images = MemoryImages()
    worker(memory_repository, settings, provider, images).process(message())
    assert provider.calls == 1
    assert memory_repository.scans[SCAN_ID].status == ScanStatus.FAILED
    assert memory_repository.errors[SCAN_ID] == ScanErrorCode.TIMEOUT
    assert memory_repository.scans[SCAN_ID].error_code == ScanErrorCode.TIMEOUT
    assert images.deleted


def test_unreadable_photo_fails_and_is_deleted(memory_repository, settings) -> None:
    images = MemoryImages({"scan-temp/account/scan/0.jpg": b"not a jpeg"})
    worker(memory_repository, settings, FakeProvider(VALID), images).process(message())
    assert memory_repository.errors[SCAN_ID] == ScanErrorCode.NO_IMAGES_USABLE
    assert images.deleted == ["scan-temp/account/scan/0.jpg"]


def test_conditional_completion_stops_after_mid_analysis_cancel(
    memory_repository, settings
) -> None:
    class CancellingProvider(FakeProvider):
        def analyse(self, images: list[bytes], location: str, timeout_s: float) -> RawDetections:
            memory_repository.scans[SCAN_ID] = memory_repository.scans[SCAN_ID].model_copy(
                update={"status": ScanStatus.CANCELLED}
            )
            return VALID

    image_source = MemoryImages()
    worker(memory_repository, settings, CancellingProvider(), image_source).process(message())
    assert memory_repository.scans[SCAN_ID].status == ScanStatus.CANCELLED
    assert SCAN_ID not in memory_repository.errors
    assert image_source.deleted


def test_unit_mismatch_is_preserved(memory_repository, settings) -> None:
    detections = RawDetections(
        items=[
            RawDetection(
                name="milk",
                category=IngredientCategory.DAIRY,
                amount=Decimal("2"),
                unit=Unit.EACH,
                confidence="medium",
            )
        ]
    )
    worker(memory_repository, settings, FakeProvider(detections)).process(message())
    quantity = memory_repository.results[SCAN_ID].items[0].quantity
    assert quantity.unit == Unit.EACH
    assert quantity.amount == Decimal("2")
    assert quantity.unit_mismatch is True


def test_empty_names_are_dropped(memory_repository, settings) -> None:
    detections = RawDetections(
        items=[
            RawDetection(name="  ", category=IngredientCategory.OTHER, confidence="low"),
        ]
    )
    worker(memory_repository, settings, FakeProvider(detections)).process(message())
    assert memory_repository.results[SCAN_ID].items == []


def test_duplicate_detections_merge_quantities(memory_repository, settings) -> None:
    detections = RawDetections(
        items=[
            RawDetection(
                name="milk",
                category=IngredientCategory.DAIRY,
                amount=Decimal("1"),
                unit=Unit.LITERS,
                confidence="medium",
                is_lower_bound=False,
            ),
            RawDetection(
                name="milk",
                category=IngredientCategory.DAIRY,
                amount=Decimal("500"),
                unit=Unit.MILLILITERS,
                confidence="high",
                is_lower_bound=True,
            ),
        ]
    )
    worker(memory_repository, settings, FakeProvider(detections)).process(message())
    items = memory_repository.results[SCAN_ID].items
    assert len(items) == 1
    assert items[0].quantity.amount == Decimal("1500")
    assert items[0].quantity.is_lower_bound is True


def test_catalog_cache_caches_empty_results() -> None:
    calls = 0

    def load():
        nonlocal calls
        calls += 1
        return []

    catalog = CatalogCache(load)
    assert catalog.get() == []
    assert catalog.get() == []
    assert calls == 1
