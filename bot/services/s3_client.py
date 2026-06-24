import logging
import mimetypes
import posixpath
import uuid
from typing import Any
from urllib.parse import urlparse

import aioboto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from bot.config import settings

logger = logging.getLogger(__name__)

_session = aioboto3.Session()
_s3_config = Config(s3={"addressing_style": "path"})


def _normalize_prefix(prefix: str) -> str:
    return prefix.strip().strip("/")


def build_photo_key(user_id: int, extension: str = ".jpg") -> str:
    prefix = _normalize_prefix(settings.S3_KEY_PREFIX)
    ext = extension if extension.startswith(".") else f".{extension}"
    filename = f"{uuid.uuid4()}{ext.lower()}"
    parts = [part for part in (prefix, str(user_id), filename) if part]
    return posixpath.join(*parts)


def build_public_url(key: str) -> str:
    if settings.S3_PUBLIC_BASE_URL:
        return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{key}"
    return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET}/{key}"


def extract_key_from_url(url: str | None) -> str | None:
    if not url or not url.startswith(("http://", "https://")):
        return None

    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    bucket_prefix = f"{settings.S3_BUCKET}/"

    if path.startswith(bucket_prefix):
        return path[len(bucket_prefix):] or None

    public_base = settings.S3_PUBLIC_BASE_URL
    if public_base:
        public_path = urlparse(public_base).path.strip("/")
        if public_path and path.startswith(f"{public_path}/"):
            return path[len(public_path) + 1:] or None
        if not public_path and path:
            return path

    return None


def _guess_content_type(filename: str | None) -> str:
    if filename:
        content_type, _ = mimetypes.guess_type(filename)
        if content_type:
            return content_type
    return "image/jpeg"


def _guess_extension(filename: str | None, content_type: str) -> str:
    if filename and "." in filename:
        return f".{filename.rsplit('.', 1)[-1].lower()}"

    guessed = mimetypes.guess_extension(content_type)
    return guessed or ".jpg"


async def _get_client() -> Any:
    return _session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=_s3_config,
    )


async def upload_photo(photo_bytes: bytes, user_id: int, filename: str | None = None) -> str | None:
    """Загружает фото в S3-совместимое хранилище и возвращает публичный URL."""
    content_type = _guess_content_type(filename)
    key = build_photo_key(user_id, _guess_extension(filename, content_type))

    try:
        async with await _get_client() as s3:
            await s3.put_object(
                Bucket=settings.S3_BUCKET,
                Key=key,
                Body=photo_bytes,
                ContentType=content_type,
                ContentLength=len(photo_bytes),
                CacheControl="public, max-age=31536000",
                Metadata={"user_id": str(user_id)},
            )
    except (BotoCoreError, ClientError) as exc:
        logger.error("S3 upload failed for user_id=%d key=%s: %s", user_id, key, exc)
        return None

    url = build_public_url(key)
    logger.info("Photo uploaded to S3: key=%s user_id=%d", key, user_id)
    return url


async def delete_photo(photo_url: str | None) -> bool:
    """Удаляет ранее загруженный S3-объект, если URL относится к нашему бакету."""
    key = extract_key_from_url(photo_url)
    if not key:
        return False

    try:
        async with await _get_client() as s3:
            await s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Failed to delete S3 object key=%s: %s", key, exc)
        return False

    logger.info("Photo deleted from S3: key=%s", key)
    return True
