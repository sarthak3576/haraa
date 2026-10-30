"""
Normalizes any uploaded photo (HEIC, WebP, PNG, JPEG, ...) into an RGB PIL
Image plus re-encoded JPEG bytes, resizing anything oversized. Used before
handing the image to either the local ML classifier or Rekognition, so
both always see the same clean JPEG input.
"""
import base64
import io

from PIL import Image, UnidentifiedImageError

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # HEIC support simply won't be available; other formats still work

MAX_DIMENSION = 1600
JPEG_QUALITY = 90


class InvalidImageError(Exception):
    pass


def load_and_normalize_image(raw_bytes: bytes) -> tuple[Image.Image, bytes]:
    if not raw_bytes:
        raise InvalidImageError("No image data was received.")

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(
            "That file doesn't look like a supported image (JPEG, PNG, WebP, or HEIC)."
        ) from exc

    image = image.convert("RGB")

    if max(image.size) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(image.size)
        new_size = (max(1, int(image.size[0] * ratio)), max(1, int(image.size[1] * ratio)))
        image = image.resize(new_size, Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return image, buffer.getvalue()


def make_thumbnail_b64(image: Image.Image, size: int = 96) -> str:
    """Small enough (a few KB) to store inline in DynamoDB for scan history
    -- no S3 bucket needed."""
    thumb = image.copy()
    thumb.thumbnail((size, size), Image.LANCZOS)
    buffer = io.BytesIO()
    thumb.save(buffer, format="JPEG", quality=70)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
