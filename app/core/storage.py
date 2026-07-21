from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file: UploadFile, folder: str) -> str:
        """파일을 저장하고 외부에서 접근 가능한 URL을 반환한다."""


class LocalStorageBackend(StorageBackend):
    """로컬 디스크(media/ 폴더)에 저장. 개발 및 초기 서비스용."""

    def save(self, file: UploadFile, folder: str) -> str:
        ext = Path(file.filename or "").suffix
        filename = f"{uuid4().hex}{ext}"

        target_dir = Path(settings.media_root) / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / filename
        with target_path.open("wb") as out:
            out.write(file.file.read())

        return f"{settings.media_url_prefix}/{folder}/{filename}"


def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorageBackend()
    # S3StorageBackend은 이후 STORAGE_BACKEND=s3 로 전환 시 여기에 추가한다.
    raise NotImplementedError(f"Unknown storage backend: {settings.storage_backend}")
