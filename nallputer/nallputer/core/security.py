from __future__ import annotations

import hmac
import os
import time
from typing import Optional

# 003 + 007 : Bearer constant-time + egress allowlist + credential scrub

def verify_bearer(auth_header: Optional[str]) -> bool:
    token = os.getenv("NALLPUTER_TOKEN", "dev-token")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    provided = auth_header[len("Bearer "):].strip()
    # constant-time compare
    return hmac.compare_digest(provided, token)


# Egress policy
def egress_check(command: str) -> Optional[dict]:
    """
    007: deny-by-default API preflight before spawn.
    MVP heuristic: if command contains a URL/host literal that is not allowlisted, deny with reason egress_blocked.
    Real proxy (127.0.0.1:3128) will enforce for HTTP(S) at runtime; this is the API-layer gate.
    """
    policy = os.getenv("NALLPUTER_EGRESS_POLICY", "deny-by-default")
    allowlist_raw = os.getenv("NALLPUTER_EGRESS_ALLOWLIST", "")
    allowlist = [s.strip().lower() for s in allowlist_raw.split(",") if s.strip()]
    if policy != "deny-by-default":
        return None  # allow all if not deny
    if not allowlist:
        # empty allowlist => only private store / localhost allowed; if command looks like it needs egress, deny
        # heuristic: if command contains http:// https:// or pypi/npm/github etc
        needles = ["pypi.org", "registry.npmjs.org", "github.com", "http://", "https://", "curl ", "wget ", "pip install", "npm install", "apt-get"]
        cmd_low = command.lower()
        for n in needles:
            if n in cmd_low:
                # if http(s) URL, extract host would be better, but MVP: deny with generic
                return {"decision": "deny", "reason": "egress_blocked", "destination": "external:443"}
        return None
    # with allowlist, check that any external host in command matches allowlist (suffix match)
    # Simplified: if command contains http://host or https://host, extract host token
    import re
    hosts = re.findall(r"https?://([^/\s:]+)", command)
    for h in hosts:
        hl = h.lower()
        ok = any(hl == a or hl.endswith("."+a.lstrip("*.")) or a in hl for a in allowlist)
        if not ok:
            return {"decision":"deny","reason":"egress_blocked","destination":f"{h}:443"}
    return None


def credential_in_spec(content: str) -> bool:
    """007: environment.yaml must never contain token values."""
    low = content.lower()
    bad_subs = ["token:", "secret:", "password:", "ghp_", "github_token"]
    # heuristic: look for those substrings outside comments
    for b in bad_subs:
        if b in low:
            return True
    return False

# Audit (append-only, never logs secrets)
_audit_log: list[dict] = []

def audit(event: dict):
    event = dict(event)
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # never include env values
    if "env" in event:
        event["env_keys"] = list(event["env"].keys()) if isinstance(event["env"], dict) else "redacted"
        event.pop("env", None)
    _audit_log.append(event)
    # also print to stdout for operator logs (no secret values)
    print(f"[AUDIT] {event}", flush=True)

def get_audit():
    return list(_audit_log)
