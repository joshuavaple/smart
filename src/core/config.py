from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/core/config.py -> repo root

class Settings(BaseSettings):
    export_path: Path = PROJECT_ROOT / "exports"
    storage_backend: Literal["local", "s3"] = "local"
    s3_bucket: Optional[str] = None
    s3_prefix: str = ""

    class Config:
        env_file = PROJECT_ROOT / ".env"
        extra = "ignore" # root .env has unrelated keys (databricks_*, azure_*) — don't choke on them

settings = Settings()
settings.export_path.mkdir(parents=True, exist_ok=True)