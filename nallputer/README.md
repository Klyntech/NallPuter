# NallPuter runtime — MVP v0.1

Disposable FastAPI runtime implementing the frozen contract:

`003 Machine Contract + 004 Persistent State + 005 Workspace + 006 Runtime (cgroup v2) + 007 Security + 008 Lifecycle + 009 NALLY Adapter + docs/api/openapi.yaml`

## Run locally

```bash
python -m venv .venv && .\.venv\Scripts\activate  # Windows
pip install -e ".[dev]"
set NALLPUTER_TOKEN=dev-token & uvicorn nallputer.app.main:app --reload --port 8000
# Bearer dev-token
```

Health: `GET http://localhost:8000/v1/health`
Machine: `GET http://localhost:8000/v1/machine`

## Docker (Lab Rat)

```bash
docker build -t nallputer:0.1 -f nallputer/Dockerfile .
docker run -p 8000:8000 -e NALLPUTER_TOKEN=dev-token nallputer:0.1
```

## Render (private service)

See `render.yaml` at repo root. Private networking only, `NALLPUTER_TOKEN` env.

## Notes

- cgroup v2 detection at boot, no silent v1 fallback (006).
- Egress is deny-by-default via in-container forward proxy + HTTP_PROXY injection (007) — stub in MVP, allowlist in `NALLPUTER_EGRESS_ALLOWLIST`.
- Workspace at `/home/nally/workspace` (005), sync engine is debounced + flush + restore against canonical store (004) — local FS cache in MVP, S3 swap is config-only.
- Lifecycle `creating→running→idle→stopping→stopped→starting→recovering→destroyed` with auto-stop 900s (008).
