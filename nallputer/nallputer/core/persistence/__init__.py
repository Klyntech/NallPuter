"""8A — Persistence adapter (S3-compatible, provider-neutral).

Interface is intentionally small: get/put_if_match/delete/list + etag.
Caller (8B sync engine) owns the computer prefix `computers/cmp_<id>/...`
and manifest semantics. This package only knows keys and etags.

No endpoint shape changes, no 003-009 reopen.
"""

from .base import Persistence, ConflictError
from .factory import get_persistence, reset_persistence

__all__ = ["Persistence", "ConflictError", "get_persistence", "reset_persistence"]
