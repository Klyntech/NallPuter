"""8A — Persistence adapter tests (S3-compatible, provider-neutral).

No real bucket required. Uses local FS fallback by default, and moto S3 when
NALLPUTER_S3_* points at mock. Provider is deployment config (011 row 1).
"""

import os
import tempfile
from pathlib import Path

import pytest


def test_local_fs_persistence_basic(tmp_path: Path):
    from nallputer.core.persistence.local_fs import LocalFSPersistence

    p = LocalFSPersistence(tmp_path / "canonical")
    key = "computers/cmp_test/manifest.json"
    data = b'{"rev": 1}'
    etag = p.put(key, data)
    assert etag
    got, etag2 = p.get(key)
    assert got == data
    assert etag2 == etag
    assert p.exists(key)
    assert key in p.list("computers/cmp_test/")
    # If-Match success
    etag3 = p.put(key, b'{"rev": 2}', if_match=etag)
    assert etag3 != etag
    # If-Match stale -> ConflictError
    from nallputer.core.persistence import ConflictError

    with pytest.raises(ConflictError):
        p.put(key, b'{"rev": 3}', if_match=etag)
    p.delete(key)
    assert not p.exists(key)
    assert p.get(key) == (None, None)


def test_factory_local_fallback(monkeypatch, tmp_path: Path):
    # No S3 env -> local
    monkeypatch.delenv("NALLPUTER_S3_BUCKET", raising=False)
    monkeypatch.delenv("NALLPUTER_S3_ENDPOINT", raising=False)
    monkeypatch.setenv("NALLPUTER_CANONICAL", str(tmp_path / "canon"))
    from nallputer.core.persistence.factory import reset_persistence, get_persistence
    from nallputer.core.persistence.local_fs import LocalFSPersistence

    reset_persistence()
    pers = get_persistence()
    assert isinstance(pers, LocalFSPersistence)
    # cleanup
    reset_persistence()
    monkeypatch.delenv("NALLPUTER_CANONICAL", raising=False)


def test_factory_s3_with_moto(monkeypatch, tmp_path: Path):
    pytest.importorskip("moto")
    from moto import mock_aws

    monkeypatch.setenv("NALLPUTER_S3_BUCKET", "test-bucket-8a")
    monkeypatch.setenv("NALLPUTER_S3_ENDPOINT", "mock")
    monkeypatch.setenv("NALLPUTER_S3_REGION", "us-east-1")
    # Ensure factory picks S3
    from nallputer.core.persistence.factory import reset_persistence, get_persistence
    from nallputer.core.persistence.s3 import S3Persistence

    reset_persistence()
    with mock_aws():
        pers = get_persistence()
        assert isinstance(pers, S3Persistence)
        # Basic put/get with If-Match
        key = "computers/cmp_moto/manifest.json"
        data = b'{"rev": 1}'
        etag = pers.put(key, data)
        got, etag2 = pers.get(key)
        assert got == data
        assert etag == etag2
        # Conditional success
        etag3 = pers.put(key, b'{"rev": 2}', if_match=etag)
        assert etag3 != etag
        from nallputer.core.persistence import ConflictError

        with pytest.raises(ConflictError):
            pers.put(key, b'{"rev": 3}', if_match=etag)
        assert key in pers.list("computers/cmp_moto/")
        pers.delete(key)
        assert not pers.exists(key)
    reset_persistence()
    monkeypatch.delenv("NALLPUTER_S3_BUCKET", raising=False)
    monkeypatch.delenv("NALLPUTER_S3_ENDPOINT", raising=False)
    monkeypatch.delenv("NALLPUTER_S3_REGION", raising=False)


def test_s3_provider_neutral_no_r2_coupling():
    """011 row 1: S3-compatible, not R2-specific — provider is endpoint_url config."""
    from nallputer.core.persistence.s3 import S3Persistence
    import inspect

    src = inspect.getsource(S3Persistence)
    # Must not hard-code a provider endpoint (e.g., r2.cloudflarestorage.com)
    assert "r2.cloudflarestorage.com" not in src.lower()
    assert "cloudflare" not in src.lower() or "endpoint_url" in src.lower()
    # Provider is endpoint_url param, not hard-coded bucket logic
    assert "endpoint_url" in src
    # Docstring may mention R2 as example — that's allowed and correct per 011
    # The check is that there is no hard-coded R2 bucket/region logic
