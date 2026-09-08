from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .base import Persistence
from .local_fs import LocalFSPersistence
from .s3 import S3Persistence

_singleton: Optional[Persistence] = None


def get_persistence() -> Persistence:
    """Provider-neutral factory (011 row 1).

    - If `NALLPUTER_S3_BUCKET` is set (and endpoint/keys optionally), return `S3Persistence`.
    - If `NALLPUTER_S3_ENDPOINT == "mock"` and bucket set, still return `S3Persistence`
      (caller is expected to have `moto` mocking active in tests; no real creds needed).
    - Otherwise return `LocalFSPersistence` at `NALLPUTER_CANONICAL` or `CANONICAL_ROOT`.

    No new endpoint shape, no MachineProfile change — bucket is deployment config.
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    bucket = os.getenv("NALLPUTER_S3_BUCKET", "").strip()
    endpoint = os.getenv("NALLPUTER_S3_ENDPOINT", "").strip()
    region = os.getenv("NALLPUTER_S3_REGION", "").strip() or None
    access = os.getenv("NALLPUTER_S3_ACCESS_KEY", "").strip() or None
    secret = os.getenv("NALLPUTER_S3_SECRET_KEY", "").strip() or None
    prefix = os.getenv("NALLPUTER_S3_PREFIX", "").strip()

    # If bucket is set, prefer S3 even if endpoint is empty (real S3) or "mock" (moto)
    if bucket:
        # Allow local override for tests: NALLPUTER_S3_ENDPOINT can be empty for real S3
        # or "mock" for moto. For moto, we still need to create bucket lazily; S3Persistence will do.
        try:
            _singleton = S3Persistence(
                bucket=bucket,
                endpoint_url=endpoint or None,
                region_name=region,
                access_key=access,
                secret_key=secret,
                prefix=prefix,
            )
            # Ensure bucket exists (best-effort, no error if already exists)
            try:
                _singleton.s3.head_bucket(Bucket=bucket)  # type: ignore[attr-defined]
            except Exception:
                try:
                    # moto or fresh bucket — create
                    create_kwargs: dict = {"Bucket": bucket}
                    if region and region != "us-east-1":
                        create_kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
                    _singleton.s3.create_bucket(**create_kwargs)  # type: ignore[arg-type]
                except Exception:
                    pass
            return _singleton
        except Exception:
            # Fall back to local if S3 init fails (e.g., boto3 not installed)
            pass

    # Local fallback — canonical root from config
    from nallputer.app.config import CANONICAL_ROOT

    # Allow explicit override for tests: NALLPUTER_CANONICAL (file:// or path)
    canonical_env = os.getenv("NALLPUTER_CANONICAL", "").strip()
    if canonical_env:
        # Support s3://bucket/prefix already handled above; here it's a local path
        # Strip file:// prefix if present
        if canonical_env.startswith("file://"):
            canonical_env = canonical_env[len("file://") :]
        root = Path(canonical_env)
    else:
        root = Path(CANONICAL_ROOT)

    _singleton = LocalFSPersistence(root)
    return _singleton


def reset_persistence() -> None:
    """For tests only — clear singleton so env changes take effect."""
    global _singleton
    _singleton = None
