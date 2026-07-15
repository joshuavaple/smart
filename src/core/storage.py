from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path

class ArtifactStore(ABC):
    @abstractmethod
    def write_csv(self, df: pd.DataFrame, filename: str) -> str:
        """Write df, return a path/URI the user can be told about."""

class LocalArtifactStore(ArtifactStore):
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_csv(self, df: pd.DataFrame, filename: str) -> str:
        safe_name = Path(filename).name  # strip any directory components
        path = self.base_dir / safe_name
        tmp = path.with_suffix(path.suffix + ".tmp")
        df.to_csv(tmp, index=False)
        tmp.replace(path)  # atomic on POSIX
        return str(path)

# class S3ArtifactStore(ArtifactStore):
#     def __init__(self, bucket: str, prefix: str = ""):
#         import boto3
#         self.s3 = boto3.client("s3")
#         self.bucket, self.prefix = bucket, prefix

#     def write_csv(self, df: pd.DataFrame, filename: str) -> str:
#         safe_name = Path(filename).name
#         key = f"{self.prefix}{safe_name}"
#         self.s3.put_object(Bucket=self.bucket, Key=key, Body=df.to_csv(index=False).encode())
#         return f"s3://{self.bucket}/{key}"
    
def get_store(settings) -> ArtifactStore:
    """Factory: build the configured ArtifactStore from Settings.

    Keeps the backend choice (local disk vs S3 vs whatever comes next)
    entirely in config — callers (smart_tools) never branch on it.
    """
    if settings.storage_backend == "local":
        return LocalArtifactStore(settings.export_path)

    # if settings.storage_backend == "s3":
    #     if not settings.s3_bucket:
    #         raise ValueError("STORAGE_BACKEND=s3 requires S3_BUCKET to be set in .env")
    #     return S3ArtifactStore(bucket=settings.s3_bucket, prefix=settings.s3_prefix)

    raise ValueError(f"unknown storage backend: {settings.storage_backend!r}")