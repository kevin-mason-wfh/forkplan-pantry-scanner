import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    scan_bucket: str
    ssm_prefix: str
    max_image_edge: int
    jpeg_quality: int
    provider_timeout_seconds: float
    result_ttl_hours: int
    statement_timeout_ms: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            provider=os.getenv("PROVIDER", "claude"),
            model=os.getenv("MODEL", ""),
            scan_bucket=os.getenv("SCAN_BUCKET", ""),
            ssm_prefix=os.getenv("SSM_PREFIX", "/forkplan/pantry-scanner/beta"),
            max_image_edge=int(os.getenv("MAX_IMAGE_EDGE", "1600")),
            jpeg_quality=int(os.getenv("JPEG_QUALITY", "85")),
            provider_timeout_seconds=float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "90")),
            result_ttl_hours=int(os.getenv("RESULT_TTL_HOURS", "24")),
            statement_timeout_ms=int(os.getenv("STATEMENT_TIMEOUT_MS", "5000")),
        )


def provider_timeout(configured: float, remaining_ms: int) -> float:
    return max(0.0, min(configured, remaining_ms / 1000 - 20))
