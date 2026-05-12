"""R2 storage service implementation."""

import uuid
from pathlib import Path

import aioboto3

from src.application.i_storage_service import IStorageService
from src.core.config import Settings, settings as default_settings


class R2StorageService(IStorageService):
    """Storage implementation using Cloudflare R2 (S3 compatible) via aioboto3."""

    _CONTENT_TYPE_BY_SUFFIX: dict[str, str] = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }

    def __init__(
        self,
        settings: Settings = default_settings,
        key_prefix: str = "lost-reports",
    ) -> None:
        if not settings.R2_ACCOUNT_ID:
            raise ValueError("R2_ACCOUNT_ID is required")
        if not settings.R2_ACCESS_KEY_ID:
            raise ValueError("R2_ACCESS_KEY_ID is required")
        if not settings.R2_SECRET_ACCESS_KEY:
            raise ValueError("R2_SECRET_ACCESS_KEY is required")
        if not settings.R2_BUCKET:
            raise ValueError("R2_BUCKET is required")
        if not settings.R2_PUBLIC_URL:
            raise ValueError("R2_PUBLIC_URL is required")

        self._access_key_id = settings.R2_ACCESS_KEY_ID
        self._secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self._bucket = settings.R2_BUCKET
        self._public_base_url = settings.R2_PUBLIC_URL.rstrip("/")
        self._key_prefix = key_prefix.strip("/")
        self._endpoint_url = (
            f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        )
        self._session = aioboto3.Session()

    async def upload_photo(self, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        key = (
            f"{self._key_prefix}/{uuid.uuid4().hex}{suffix}"
            if self._key_prefix
            else f"{uuid.uuid4().hex}{suffix}"
        )
        content_type = self._CONTENT_TYPE_BY_SUFFIX.get(
            suffix, "application/octet-stream"
        )

        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name="auto",
        ) as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )

        return f"{self._public_base_url}/{key}"

    async def delete_photo(self, photo_url: str) -> None:
        key = self._key_from_url(photo_url)
        if key is None:
            return

        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            region_name="auto",
        ) as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)

    def _key_from_url(self, photo_url: str) -> str | None:
        """Strip the public base URL prefix to recover the R2 object key."""
        prefix = f"{self._public_base_url}/"
        if not photo_url.startswith(prefix):
            return None
        key = photo_url[len(prefix) :]
        return key or None
