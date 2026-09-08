from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ConflictError(Exception):
    """If-Match failed — stale manifest/object etag (caller should retry or surface degraded)."""

    def __init__(self, key: str, expected: Optional[str], actual: Optional[str]):
        super().__init__(f"If-Match failed for {key!r}: expected {expected!r} got {actual!r}")
        self.key = key
        self.expected = expected
        self.actual = actual


class Persistence(ABC):
    """Provider-neutral canonical store interface (8A).

    Keys are S3-style: `computers/cmp_abc/manifest.json`, `computers/cmp_abc/workspace/projects/foo.py`, etc.
    ETag is opaque (S3 ETag or local md5). `None` means object does not exist.
    """

    @abstractmethod
    def get(self, key: str) -> tuple[Optional[bytes], Optional[str]]:
        """Return (data, etag) or (None, None) if missing."""

    @abstractmethod
    def put(self, key: str, data: bytes, if_match: Optional[str] = None) -> str:
        """Atomic put. If `if_match` is not None, must match current etag or raise ConflictError.
        If `if_match` is None and object exists, unconditional overwrite (caller owns idempotency).
        Returns new_etag.
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete if exists; no error if missing."""

    @abstractmethod
    def list(self, prefix: str) -> list[str]:
        """List keys with given prefix (may be empty)."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check existence without fetching body."""
