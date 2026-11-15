import time
from collections.abc import Callable
from threading import Lock
from uuid import UUID

from pydantic import ValidationError

from pantry_scanner.config import Settings, provider_timeout
from pantry_scanner.db.repositories import ScanRepository
from pantry_scanner.domain.enums import (
    MatchConfidence,
    ScanErrorCode,
)
from pantry_scanner.domain.models import (
    Ingredient,
    Match,
    Quantity,
    ScanItem,
    ScanMessage,
    ScanRecord,
    ScanResult,
)
from pantry_scanner.domain.units import convert_amount, unit_family
from pantry_scanner.errors import (
    InvalidProviderOutputError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ScanProcessingError,
)
from pantry_scanner.logging import logger, metrics
from pantry_scanner.matching.matcher import match_ingredient
from pantry_scanner.matching.normalize import normalize
from pantry_scanner.storage.images import ImageSource
from pantry_scanner.storage.prepare import prepare_image
from pantry_scanner.vision.base import RawDetection, RawDetections, VisionProvider

PROMPT_VERSION = "system_v1"


class CatalogCache:
    def __init__(self, loader: Callable[[], list[Ingredient]], ttl_seconds: float = 600.0) -> None:
        self.loader = loader
        self.ttl_seconds = ttl_seconds
        self._catalog: list[Ingredient] = []
        self._loaded_at = 0.0
        self._has_loaded = False
        self._lock = Lock()

    def get(self) -> list[Ingredient]:
        now = time.monotonic()
        with self._lock:
            if not self._has_loaded or now - self._loaded_at >= self.ttl_seconds:
                self._catalog = self.loader()
                self._loaded_at = now
                self._has_loaded = True
            return list(self._catalog)


def _quantity(detection: RawDetection, match: Match) -> Quantity:
    amount = detection.amount
    unit = detection.unit
    mismatch = False
    target = match.unit
    if unit is not None and target is not None and unit != target:
        if unit_family(unit) == unit_family(target) and unit_family(unit) != "discrete":
            try:
                if amount is not None:
                    amount = convert_amount(amount, unit, target)
                unit = target
            except ValueError:
                mismatch = True
        else:
            mismatch = True
    return Quantity(
        amount=amount,
        unit=unit,
        basis=detection.basis,
        confidence=detection.confidence,
        is_lower_bound=detection.is_lower_bound,
        unit_mismatch=mismatch,
    )


def _item_key(item: ScanItem) -> tuple[str, str]:
    match = item.match
    if match.ingredient_id is not None:
        return "account", str(match.ingredient_id)
    if match.catalog_ingredient_id is not None:
        return "catalog", str(match.catalog_ingredient_id)
    return "unmatched", normalize(item.detected_name)


def _confidence_score(confidence: MatchConfidence) -> int:
    return {
        MatchConfidence.NONE: 0,
        MatchConfidence.LOW: 1,
        MatchConfidence.MEDIUM: 2,
        MatchConfidence.HIGH: 3,
    }[confidence]


def _merge_items(items: list[ScanItem]) -> list[ScanItem]:
    merged: dict[tuple[str, str], ScanItem] = {}
    for item in items:
        key = _item_key(item)
        existing = merged.get(key)
        if existing is None:
            merged[key] = item
            continue
        current_quantity = existing.quantity
        next_quantity = item.quantity
        amount = current_quantity.amount
        if (
            amount is not None
            and next_quantity.amount is not None
            and current_quantity.unit == next_quantity.unit
            and not current_quantity.unit_mismatch
            and not next_quantity.unit_mismatch
        ):
            amount += next_quantity.amount
        confidence = max(
            (current_quantity.confidence, next_quantity.confidence),
            key=_confidence_score,
        )
        merged[key] = existing.model_copy(
            update={
                "quantity": current_quantity.model_copy(
                    update={
                        "amount": amount,
                        "is_lower_bound": (
                            current_quantity.is_lower_bound or next_quantity.is_lower_bound
                        ),
                        "unit_mismatch": (
                            current_quantity.unit_mismatch or next_quantity.unit_mismatch
                        ),
                        "confidence": confidence,
                    }
                )
            }
        )
    return list(merged.values())


def _map_detections(
    detections: RawDetections,
    scan: ScanRecord,
    repository: ScanRepository,
    catalog: list[Ingredient],
) -> list[ScanItem]:
    account_ingredients = repository.account_ingredients(scan.account_id)
    aliases = repository.aliases(scan.account_id)
    items: list[ScanItem] = []
    for detection in detections.items:
        name = detection.name.strip()
        if not name:
            continue
        match = match_ingredient(
            name,
            detection.unit,
            scan.account_id,
            account_ingredients,
            catalog,
            aliases,
        )
        items.append(
            ScanItem(
                detected_name=name,
                match=match,
                suggested_category=detection.category,
                quantity=_quantity(detection, match),
                notes=detection.notes,
            )
        )
    return _merge_items(items)


def _analyse_with_schema_retry(
    provider: VisionProvider, images: list[bytes], location: str, timeout_s: float
) -> RawDetections:
    for attempt in range(2):
        try:
            response = provider.analyse(images, location, timeout_s)
            return RawDetections.model_validate(response)
        except ValidationError:
            if attempt == 1:
                raise InvalidProviderOutputError() from None
        except (TimeoutError, ProviderTimeoutError):
            raise ProviderTimeoutError() from None
        except ScanProcessingError:
            raise
        except Exception as error:
            raise ProviderUnavailableError() from error
    raise InvalidProviderOutputError()


class ScanWorker:
    def __init__(
        self,
        repository: ScanRepository,
        images: ImageSource,
        provider: VisionProvider,
        settings: Settings,
        catalog_cache: CatalogCache | None = None,
    ) -> None:
        self.repository = repository
        self.images = images
        self.provider = provider
        self.settings = settings
        self.catalog_cache = catalog_cache or CatalogCache(repository.catalog_ingredients)

    def process(self, message: ScanMessage, remaining_ms: int = 150_000) -> None:
        logger.append_keys(scan_id=str(message.scan_id), account_id=str(message.account_id))
        scan = self.repository.claim_scan(message.scan_id, message.account_id)
        if scan is None:
            logger.info("Scan was not claimable")
            return

        try:
            if not scan.image_keys:
                raise ScanProcessingError(ScanErrorCode.NO_IMAGES_USABLE)
            prepared_images: list[bytes] = []
            try:
                for key in scan.image_keys:
                    prepared_images.append(
                        prepare_image(
                            self.images.get(key),
                            self.settings.max_image_edge,
                            self.settings.jpeg_quality,
                        )
                    )
            except Exception:
                raise ScanProcessingError(ScanErrorCode.NO_IMAGES_USABLE) from None

            timeout_s = provider_timeout(
                self.settings.provider_timeout_seconds,
                remaining_ms,
            )
            if timeout_s <= 0:
                raise ProviderTimeoutError()
            started = time.monotonic()
            try:
                detections = _analyse_with_schema_retry(
                    self.provider, prepared_images, scan.location or "", timeout_s
                )
            finally:
                metrics.add_metric(
                    name="provider_latency_ms",
                    unit="Milliseconds",
                    value=(time.monotonic() - started) * 1000,
                )
            items = _map_detections(
                detections,
                scan,
                self.repository,
                self.catalog_cache.get(),
            )
            result = ScanResult(items=items, warnings=detections.warnings)
            completed = self.repository.complete_scan(
                scan.id,
                result,
                detections.warnings,
                self.settings.provider,
                self.settings.model,
                PROMPT_VERSION,
                self.settings.result_ttl_hours,
            )
            if completed:
                metrics.add_metric(name="scans_completed", unit="Count", value=1)
                metrics.add_metric(name="items_detected", unit="Count", value=len(items))
                logger.info("Scan completed")
            else:
                logger.info("Scan completion skipped because its status changed")
        except ScanProcessingError as error:
            try:
                error_code = ScanErrorCode(error.error_code)
            except ValueError:
                error_code = ScanErrorCode.INTERNAL_ERROR
            self._fail(scan.id, error_code)
        except Exception:
            logger.error("Scan processing failed")
            self._fail(scan.id, ScanErrorCode.INTERNAL_ERROR)
        finally:
            for key in scan.image_keys:
                try:
                    self.images.delete(key)
                except Exception:
                    logger.error("Temporary image cleanup failed")

    def _fail(self, scan_id: UUID, error_code: ScanErrorCode) -> None:
        try:
            self.repository.fail_scan(scan_id, error_code)
        except Exception:
            logger.error("Could not persist scan failure")
        metrics.add_metric(name="scans_failed", unit="Count", value=1)
        logger.warning("Scan failed", extra={"error_code": error_code.value})


def process_scan(
    message: ScanMessage,
    repository: ScanRepository,
    images: ImageSource,
    provider: VisionProvider,
    settings: Settings,
    remaining_ms: int = 150_000,
) -> None:
    worker = ScanWorker(repository, images, provider, settings)
    worker.process(message, remaining_ms)
