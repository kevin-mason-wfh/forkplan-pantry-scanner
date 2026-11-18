from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

# Reject decompression bombs well below Pillow's default (~89M pixels).
Image.MAX_IMAGE_PIXELS = 40_000_000


def prepare_image(data: bytes, max_edge: int = 1600, jpeg_quality: int = 85) -> bytes:
    if not data.startswith(b"\xff\xd8\xff"):
        raise ValueError("Image is not a JPEG")
    if max_edge < 1 or not 1 <= jpeg_quality <= 100:
        raise ValueError("Invalid image preparation settings")
    try:
        with Image.open(BytesIO(data)) as original:
            # Let the JPEG decoder downscale during decode to bound memory use.
            original.draft("RGB", (max_edge * 2, max_edge * 2))
            original.load()
            oriented = ImageOps.exif_transpose(original)
            image = oriented.convert("RGB")
            image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=jpeg_quality, exif=b"", optimize=True)
            return output.getvalue()
    except (
        OSError,
        ValueError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as error:
        raise ValueError("Image could not be decoded") from error
