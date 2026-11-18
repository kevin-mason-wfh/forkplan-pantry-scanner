import json
from functools import lru_cache
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from pantry_scanner.config import Settings
from pantry_scanner.db.connection import parameter
from pantry_scanner.db.postgres import PostgresRepository
from pantry_scanner.domain.models import ScanMessage
from pantry_scanner.logging import logger, metrics
from pantry_scanner.pipeline import ScanWorker
from pantry_scanner.storage.images import S3ImageSource
from pantry_scanner.vision.factory import create_provider


def _safe_uuid(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return str(UUID(value))
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _runtime_worker() -> ScanWorker:
    settings = Settings.from_env()
    if not settings.model:
        raise RuntimeError("MODEL must be set")
    api_key_parameter = "anthropic-api-key" if settings.provider == "claude" else "openai-api-key"
    api_key = parameter(api_key_parameter, settings)
    parameter("db-url", settings)
    return ScanWorker(
        repository=PostgresRepository(),
        images=S3ImageSource(settings.scan_bucket),
        provider=create_provider(settings.provider, settings.model, api_key),
        settings=settings,
    )


def handle_event(
    event: dict[str, Any], context: Any, worker: ScanWorker
) -> dict[str, list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    for record in event.get("Records", []):
        message_id = str(record.get("messageId", ""))
        body = record.get("body", "")
        try:
            message = ScanMessage.model_validate(json.loads(body))
        except (json.JSONDecodeError, TypeError, ValidationError):
            try:
                body_object = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                body_object = {}
            if not isinstance(body_object, dict):
                body_object = {}
            metrics.add_metric(name="malformed_messages", unit="Count", value=1)
            logger.warning(
                "Dropping malformed SQS message",
                extra={
                    "message_id": message_id,
                    "scan_id": _safe_uuid(body_object.get("scan_id")),
                    "account_id": _safe_uuid(body_object.get("account_id")),
                },
            )
            continue
        try:
            remaining_ms = context.get_remaining_time_in_millis()
            worker.process(message, remaining_ms)
        except Exception:
            logger.error(
                "Worker failed before scan claim",
                extra={"scan_id": str(message.scan_id), "account_id": str(message.account_id)},
            )
            failures.append({"itemIdentifier": message_id})
    return {"batchItemFailures": failures}


@logger.inject_lambda_context(clear_state=True)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, list[dict[str, str]]]:
    return handle_event(event, context, _runtime_worker())
