from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite:///./backend/dev.db"
    )
    auth_secret_key: str = os.getenv("AUTH_SECRET_KEY", "dev-secret-change-me")
    auth_algorithm: str = os.getenv("AUTH_ALGORITHM", "HS256")
    verification_storage_dir: str = os.getenv("VERIFICATION_STORAGE_DIR", "backend/storage/verification_docs")


settings = Settings()
