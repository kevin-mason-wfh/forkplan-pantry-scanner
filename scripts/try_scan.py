"""Exercise the SQS worker with in-memory dependencies and the fake provider."""

import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from pantry_scanner.config import Settings
from pantry_scanner.db.memory import MemoryRepository
from pantry_scanner.domain.enums import ScanStatus
from pantry_scanner.domain.models import ScanMessage, ScanRecord
from pantry_scanner.handlers.worker import handle_event
from pantry_scanner.pipeline import ScanWorker
from pantry_scanner.vision.fake import FakeProvider


class LocalImages:
    def __init__(self) -> None:
        image = BytesIO()
        Image.new("RGB", (64, 48), "white").save(image, "JPEG")
        self.content = image.getvalue()

    def get(self, key: str) -> bytes:
        return self.content

    def delete(self, key: str) -> None:
        return None


class LocalContext:
    def get_remaining_time_in_millis(self) -> int:
        return 150_000


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: try_scan.py events/sqs_scan.json")
    event_path = Path(sys.argv[1])
    event: dict[str, Any] = json.loads(event_path.read_text(encoding="utf-8"))
    message = ScanMessage.model_validate(json.loads(event["Records"][0]["body"]))
    image_keys = [
        f"scan-temp/{message.account_id}/{message.scan_id}/0.jpg",
    ]
    repository = MemoryRepository(
        scans=[
            ScanRecord(
                id=message.scan_id,
                account_id=message.account_id,
                status=ScanStatus.QUEUED,
                location="fridge",
                image_keys=image_keys,
            )
        ]
    )
    worker = ScanWorker(
        repository,
        LocalImages(),
        FakeProvider(),
        Settings.from_env(),
    )
    response = handle_event(event, LocalContext(), worker)
    final_scan = repository.scans[message.scan_id]
    result = repository.results.get(message.scan_id)
    item_count = len(result.items) if result is not None else 0
    print(
        f"status={final_scan.status} "
        f"result_items={item_count} "
        f"batch_failures={len(response['batchItemFailures'])}"
    )


if __name__ == "__main__":
    main()
