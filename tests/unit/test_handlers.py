from typing import Any

from tests.conftest import ACCOUNT_ID, SCAN_ID
from tests.unit.test_pipeline import VALID, MemoryImages

from pantry_scanner.handlers.sweeper import run_sweeper
from pantry_scanner.handlers.worker import handle_event


class Context:
    def get_remaining_time_in_millis(self) -> int:
        return 150_000


def test_malformed_sqs_record_is_dropped(settings, memory_repository) -> None:
    from pantry_scanner.pipeline import ScanWorker
    from pantry_scanner.vision.fake import FakeProvider

    result = handle_event(
        {"Records": [{"messageId": "bad", "body": "not-json"}]},
        Context(),
        ScanWorker(memory_repository, MemoryImages(), FakeProvider(VALID), settings),
    )
    assert result == {"batchItemFailures": []}


def test_json_array_is_dropped_as_malformed(settings, memory_repository) -> None:
    from pantry_scanner.pipeline import ScanWorker
    from pantry_scanner.vision.fake import FakeProvider

    result = handle_event(
        {"Records": [{"messageId": "bad-array", "body": "[]"}]},
        Context(),
        ScanWorker(memory_repository, MemoryImages(), FakeProvider(VALID), settings),
    )
    assert result == {"batchItemFailures": []}


def test_infrastructure_failure_is_returned_for_retry(settings, memory_repository) -> None:
    from pantry_scanner.pipeline import ScanWorker
    from pantry_scanner.vision.fake import FakeProvider

    def unavailable(scan_id, account_id):
        raise RuntimeError("database unavailable")

    memory_repository.claim_scan = unavailable  # type: ignore[method-assign]
    result = handle_event(
        {
            "Records": [
                {
                    "messageId": "retry-me",
                    "body": (f'{{"v":1,"scan_id":"{SCAN_ID}","account_id":"{ACCOUNT_ID}"}}'),
                }
            ]
        },
        Context(),
        ScanWorker(memory_repository, MemoryImages(), FakeProvider(VALID), settings),
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "retry-me"}]}


def test_sweeper_deletes_reported_objects() -> None:
    class Sweeper:
        def sweep(self) -> list[tuple[Any, Any, list[str]]]:
            return [(ACCOUNT_ID, SCAN_ID, [f"scan-temp/{ACCOUNT_ID}/{SCAN_ID}/0.jpg"])]

    images = MemoryImages()
    result = run_sweeper(Sweeper(), images)  # type: ignore[arg-type]
    assert result == {"deleted_objects": 1}
    assert images.deleted == [f"scan-temp/{ACCOUNT_ID}/{SCAN_ID}/0.jpg"]
