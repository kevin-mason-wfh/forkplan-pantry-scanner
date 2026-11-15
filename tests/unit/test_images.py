from io import BytesIO

import boto3
import pytest
from moto import mock_aws
from PIL import Image

from pantry_scanner.storage.images import S3ImageSource
from pantry_scanner.storage.prepare import prepare_image


def jpeg(size: tuple[int, int] = (100, 50)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, "red").save(output, "JPEG")
    return output.getvalue()


def test_prepare_image_resizes_and_strips_metadata() -> None:
    prepared = prepare_image(jpeg((300, 200)), max_edge=100)
    with Image.open(BytesIO(prepared)) as image:
        assert image.format == "JPEG"
        assert max(image.size) == 100
        assert not image.getexif()


@pytest.mark.parametrize("data", [b"", b"\x89PNG\r\n\x1a\n"])
def test_prepare_image_rejects_non_jpeg(data: bytes) -> None:
    with pytest.raises(ValueError):
        prepare_image(data)


def test_prepare_image_rejects_invalid_jpeg() -> None:
    with pytest.raises(ValueError):
        prepare_image(b"\xff\xd8\xffbroken")


@mock_aws
def test_s3_image_source_downloads_and_deletes() -> None:
    client = boto3.client("s3", region_name="us-east-1")
    client.create_bucket(Bucket="test-bucket")
    client.put_object(Bucket="test-bucket", Key="scan-temp/a/b/0.jpg", Body=b"photo")
    source = S3ImageSource("test-bucket", client)
    assert source.get("scan-temp/a/b/0.jpg") == b"photo"
    source.delete("scan-temp/a/b/0.jpg")
    with pytest.raises(client.exceptions.NoSuchKey):
        source.get("scan-temp/a/b/0.jpg")
