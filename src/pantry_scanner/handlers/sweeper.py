from functools import lru_cache
from typing import Any
from uuid import UUID

from pantry_scanner.config import Settings
from pantry_scanner.db.connection import parameter
from pantry_scanner.db.postgres import PostgresRepository
from pantry_scanner.logging import logger, metrics
from pantry_scanner.storage.images import S3ImageSource


@lru_cache(maxsize=1)
def _runtime_dependencies() -> tuple[PostgresRepository, S3ImageSource]:
    settings = Settings.from_env()
    parameter("db-url", settings)
    return PostgresRepository(), S3ImageSource(settings.scan_bucket)


def run_sweeper(repository: Any, images: S3ImageSource) -> dict[str, int]:
    deleted_objects = 0
    for account_id, scan_id, keys in repository.sweep():
        logger.append_keys(scan_id=str(scan_id), account_id=str(account_id))
        for key in keys:
            try:
                images.delete(key)
                deleted_objects += 1
            except Exception:
                logger.error("Sweeper could not delete temporary image")
    metrics.add_metric(name="sweeper_objects_deleted", unit="Count", value=deleted_objects)
    return {"deleted_objects": deleted_objects}


@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, int]:
    repository, images = _runtime_dependencies()
    return run_sweeper(repository, images)


def scan_cleanup_tuple(
    account_id: UUID, scan_id: UUID, keys: list[str]
) -> tuple[UUID, UUID, list[str]]:
    return account_id, scan_id, keys
