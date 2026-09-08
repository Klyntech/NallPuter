"""8D — Security proxy enforcement (real, not just env var).

Old test: evil.com -> 403, pypi.org -> allowed via API preflight.
New requirement (011 8D): request must actually pass through 127.0.0.1:3128 proxy
and proxy must produce audit decision.
"""

import os
import socket
import time
import http.client


def _ensure_proxy():
    from nallputer.core.egress_proxy import start_proxy, is_running, clear_proxy_audit

    if not is_running():
        assert start_proxy(), "proxy failed to start"
        time.sleep(0.2)
    else:
        clear_proxy_audit()
    # Also clear audit
    clear_proxy_audit()
    return True


def _request_via_proxy(host: str, port: int = 80, path: str = "/", method: str = "GET") -> tuple[int, str]:
    """Make a request via proxy at 127.0.0.1:3128. Returns (status, body)."""
    conn = http.client.HTTPConnection("127.0.0.1", 3128, timeout=5)
    # For proxy, path is full URL
    url = f"http://{host}:{port}{path}" if port != 80 else f"http://{host}{path}"
    try:
        conn.request(method, url, headers={"Host": host})
        resp = conn.getresponse()
        body = resp.read().decode(errors="ignore")
        return resp.status, body
    finally:
        conn.close()


def test_proxy_blocks_evil():
    _ensure_proxy()
    from nallputer.core.egress_proxy import get_proxy_audit, clear_proxy_audit

    clear_proxy_audit()
    status, body = _request_via_proxy("evil.com", 80, "/")
    assert status == 403, f"evil.com should be blocked via proxy, got {status} {body}"
    assert "egress_blocked" in body or "not in allowlist" in body
    audit = get_proxy_audit()
    assert any(a["host"] == "evil.com" and a["decision"] == "deny" for a in audit), f"audit missing deny for evil.com: {audit}"


def test_proxy_allows_pypi():
    _ensure_proxy()
    from nallputer.core.egress_proxy import get_proxy_audit, clear_proxy_audit

    clear_proxy_audit()
    status, body = _request_via_proxy("pypi.org", 443, "/simple/")
    # Our proxy for allowed hosts returns 200 (dummy, not real fetch) — that's correct for enforcement test
    assert status == 200, f"pypi.org should be allowed via proxy, got {status} {body}"
    assert "proxy allowed" in body or "allow" in body.lower()
    audit = get_proxy_audit()
    assert any(a["host"] == "pypi.org" and a["decision"] == "allow" for a in audit), f"audit missing allow for pypi.org: {audit}"


def test_proxy_audit_trail_no_secrets():
    _ensure_proxy()
    from nallputer.core.egress_proxy import get_proxy_audit, clear_proxy_audit

    clear_proxy_audit()
    # Make both blocked and allowed
    _request_via_proxy("evil.com", 80, "/")
    _request_via_proxy("github.com", 443, "/")
    audit = get_proxy_audit()
    # Should have at least 2 entries
    assert len(audit) >= 2
    # No bodies/secrets in audit
    for entry in audit:
        assert "body" not in entry
        assert "token" not in str(entry).lower()
        assert "secret" not in str(entry).lower()
        assert "host" in entry
        assert "decision" in entry
        assert entry["decision"] in ("allow", "deny")


def test_proxy_connect_tunnel():
    """CONNECT for HTTPS should also be enforced."""
    _ensure_proxy()
    from nallputer.core.egress_proxy import get_proxy_audit, clear_proxy_audit
    import socket

    clear_proxy_audit()
    # Use raw socket to send CONNECT
    s = socket.create_connection(("127.0.0.1", 3128), timeout=5)
    try:
        s.sendall(b"CONNECT evil.com:443 HTTP/1.1\r\nHost: evil.com:443\r\n\r\n")
        resp = s.recv(4096).decode(errors="ignore")
        assert "403" in resp or "egress_blocked" in resp, f"CONNECT evil.com should be blocked, got {resp}"
        audit = get_proxy_audit()
        assert any(a["host"] == "evil.com" and a["decision"] == "deny" for a in audit)
    finally:
        s.close()

    clear_proxy_audit()
    s = socket.create_connection(("127.0.0.1", 3128), timeout=5)
    try:
        s.sendall(b"CONNECT pypi.org:443 HTTP/1.1\r\nHost: pypi.org:443\r\n\r\n")
        resp = s.recv(4096).decode(errors="ignore")
        assert "200" in resp, f"CONNECT pypi.org should be allowed, got {resp}"
        audit = get_proxy_audit()
        assert any(a["host"] == "pypi.org" and a["decision"] == "allow" for a in audit)
    finally:
        s.close()
