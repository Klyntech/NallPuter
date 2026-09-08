from __future__ import annotations

import hashlib
from typing import Optional

from .base import Persistence, ConflictError

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore


class S3Persistence(Persistence):
    """S3-compatible canonical store (011 row 1).

    Keys are `computers/cmp_abc/...` inside `bucket`.
    Provider is deployment config (endpoint_url/region). R2, S3, Ceph, MinIO all work
    via endpoint_url. No R2-specific code.

    ETag is S3's ETag (quoted md5 for single-part, or multipart ETag). We treat it as opaque.
    If-Match uses S3 Conditional Writes (PutObject IfMatch) when available (boto3>=1.34).
    Fallback: read-then-compare then put (not atomic but best-effort for older endpoints).
    """

    def __init__(
        self,
        bucket: str,
        *,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        prefix: str = "",
    ):
        if boto3 is None:
            raise ImportError("boto3 is required for S3Persistence (pip install boto3)")
        if not bucket:
            raise ValueError("bucket is required for S3Persistence")
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        kwargs: dict = {}
        if endpoint_url:
            # "mock" is handled by factory via moto; here endpoint_url is real URL or None
            if endpoint_url != "mock":
                kwargs["endpoint_url"] = endpoint_url
        if region_name:
            kwargs["region_name"] = region_name
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key
        self.s3 = boto3.client("s3", **kwargs)

    def _full_key(self, key: str) -> str:
        k = key.lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{k}"
        return k

    def get(self, key: str) -> tuple[Optional[bytes], Optional[str]]:
        fk = self._full_key(key)
        try:
            resp = self.s3.get_object(Bucket=self.bucket, Key=fk)
            data = resp["Body"].read()
            etag = resp.get("ETag", "").strip('"')
            return data, etag
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("NoSuchKey", "404", "NoSuchBucket"):
                return None, None
            raise
        except self.s3.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            return None, None

    def _ensure_bucket(self) -> None:
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchBucket", "NoSuchKey"):
                try:
                    kwargs: dict = {"Bucket": self.bucket}
                    # Region handling: us-east-1 has no LocationConstraint
                    region = getattr(self.s3, "meta", {}).get("region_name") if hasattr(self.s3, "meta") else None
                    if region and region != "us-east-1":
                        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
                    self.s3.create_bucket(**kwargs)
                except ClientError:
                    pass
            else:
                # Re-raise if not bucket missing
                pass

    def put(self, key: str, data: bytes, if_match: Optional[str] = None) -> str:
        fk = self._full_key(key)
        # Try conditional write if IfMatch supported
        # boto3 S3 put_object supports IfMatch param (Conditional Writes)
        # If endpoint doesn't support it, fallback to read-then-put with check.
        # Also handle NoSuchBucket by auto-creating bucket (for moto/localstack)
        def _do_put(if_match_val: Optional[str] = None):
            if if_match_val is not None:
                return self.s3.put_object(Bucket=self.bucket, Key=fk, Body=data, IfMatch=if_match_val)
            return self.s3.put_object(Bucket=self.bucket, Key=fk, Body=data)

        try:
            if if_match is not None:
                try:
                    resp = _do_put(if_match)
                    etag = resp.get("ETag", "").strip('"')
                    if not etag:
                        etag = hashlib.md5(data).hexdigest()
                    return etag
                except ClientError as e:
                    err = e.response.get("Error", {})
                    code = err.get("Code")
                    if code == "NoSuchBucket":
                        self._ensure_bucket()
                        # Retry once
                        resp = _do_put(if_match)
                        etag = resp.get("ETag", "").strip('"')
                        return etag or hashlib.md5(data).hexdigest()
                    # Conditional check failed or not supported
                    if code in ("PreconditionFailed", "412", "ConditionalRequestConflict"):
                        _, actual = self.get(key)
                        raise ConflictError(key, if_match, actual) from e
                    if code not in ("400", "NotImplemented", "InvalidRequest"):
                        raise
                    _, actual = self.get(key)
                    if actual != if_match:
                        raise ConflictError(key, if_match, actual) from e
                    resp = _do_put(None)
                    etag = resp.get("ETag", "").strip('"')
                    return etag or hashlib.md5(data).hexdigest()
            else:
                try:
                    resp = _do_put(None)
                except ClientError as e:
                    if e.response.get("Error", {}).get("Code") == "NoSuchBucket":
                        self._ensure_bucket()
                        resp = _do_put(None)
                    else:
                        raise
                etag = resp.get("ETag", "").strip('"')
                return etag or hashlib.md5(data).hexdigest()
        except ConflictError:
            raise
        except ClientError:
            raise

    def delete(self, key: str) -> None:
        fk = self._full_key(key)
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=fk)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("NoSuchKey", "404"):
                return
            raise

    def list(self, prefix: str) -> list[str]:
        pref = self._full_key(prefix.lstrip("/"))
        out: list[str] = []
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=pref):
            for obj in page.get("Contents", []):
                k = obj["Key"]
                # Strip prefix back to logical key
                if self.prefix and k.startswith(self.prefix + "/"):
                    k = k[len(self.prefix) + 1 :]
                out.append(k)
        out.sort()
        return out

    def exists(self, key: str) -> bool:
        fk = self._full_key(key)
        try:
            self.s3.head_object(Bucket=self.bucket, Key=fk)
            return True
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code in ("404", "NoSuchKey", "NoSuchBucket", "403"):
                # 404/403 treated as not exists for our purposes (private bucket may 403 on missing)
                # To be safe, check via get
                if code == "403":
                    _, etag = self.get(key)
                    return etag is not None
                return False
            raise
