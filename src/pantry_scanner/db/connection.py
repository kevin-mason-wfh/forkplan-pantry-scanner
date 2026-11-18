from threading import Lock
from typing import Any

import psycopg
from aws_lambda_powertools.utilities import parameters

from pantry_scanner.config import Settings

_connection: Any = None
_connection_lock = Lock()


def parameter(name: str, settings: Settings | None = None) -> str:
    config = settings or Settings.from_env()
    value = parameters.get_parameter(f"{config.ssm_prefix}/{name}", decrypt=True)
    if not value:
        raise RuntimeError(f"Missing required parameter: {name}")
    return value


def get_connection(settings: Settings | None = None) -> Any:
    global _connection
    with _connection_lock:
        if _connection is None or _connection.closed:
            config = settings or Settings.from_env()
            _connection = psycopg.connect(
                parameter("db-url", config),
                prepare_threshold=None,
            )
            # Not a startup option: transaction poolers reject those. Repositories behind a
            # transaction pooler should additionally use SET LOCAL per transaction.
            timeout_ms = int(config.statement_timeout_ms)
            _connection.execute(f"SET statement_timeout = {timeout_ms}")
            _connection.commit()
        return _connection


def reconnect(settings: Settings | None = None) -> Any:
    global _connection
    with _connection_lock:
        if _connection is not None:
            _connection.close()
        _connection = None
    return get_connection(settings)
