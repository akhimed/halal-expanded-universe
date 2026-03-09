from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.app.core.config import settings


@dataclass
class StoredFile:
    original_filename: str | None
    mime_type: str | None
    storage_path: str


class FileStorage:
    async def save_upload(self, file: UploadFile) -> StoredFile:
        raise NotImplementedError


class LocalFileStorage(FileStorage):
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile) -> StoredFile:
        suffix = Path(file.filename or "").suffix
        target_name = f"{uuid4().hex}{suffix}"
        target_path = self.base / target_name
        content = await file.read()
        target_path.write_bytes(content)
        return StoredFile(
            original_filename=file.filename,
            mime_type=file.content_type,
            storage_path=str(target_path),
        )


storage_backend: FileStorage = LocalFileStorage(settings.verification_storage_dir)
