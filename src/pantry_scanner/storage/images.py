from typing import Any, Protocol, cast

import boto3  # type: ignore[import-untyped]


class ImageSource(Protocol):
    def get(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class S3ImageSource:
    def __init__(self, bucket: str, client: Any | None = None) -> None:
        self.bucket = bucket
        self.client: Any = client or boto3.client("s3")

    def get(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]
        return cast(bytes, body.read())

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)
