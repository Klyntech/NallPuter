# 9B — E2E Deployment Validation Specification

**Status:** PLANNED
**Depends on:** Slices 1–4 frozen (`519009d→f3a764a→a5c65e4→d4c7cb5`)
**Purpose:** Prove NALLY can actually operate a NallPuter computer end-to-end

---

## What 9B Must Prove

Not "can NALLY reach NallPuter" — but:

> **Can an actual NALLY reasoning turn cause a real computer action in NallPuter and receive the observation back into the same reasoning loop?**

That is the single success criterion. Everything else is infrastructure to reach it.

---

## Configuration

### Required environment

```
NALLPUTER_URL     — e.g., http://localhost:8000/v1 (local) or https://nallputer.internal/v1 (Render private)
NALLPUTER_TOKEN   — Bearer token for NallPuter auth
NALLPUTER_STARTUP_GRACE_MS — optional, default 30000
```

### Missing-config behavior

- If `NALLPUTER_URL` missing: `ComputerClient` defaults to `http://localhost:8000/v1`
- If `NALLPUTER_TOKEN` missing: requests fail with 401
- `ComputerAdapter.preflight()` returns `ComputerError(code="config_missing")` if URL unreachable
- No silent fallback to local execution — if adapter is wired, it uses NallPuter or fails loud

### Config loading

NALLY config (`nally/config.py`) must gain:

```python
NALLPUTER_URL: str = os.getenv("NALLPUTER_URL", "")
NALLPUTER_TOKEN: str = os.getenv("NALLPUTER_TOKEN", "")
NALLPUTER_STARTUP_GRACE_MS: int = int(os.getenv("NALLPUTER_STARTUP_GRACE_MS", "30000"))
```

No provider-specific flags. No Docker leakage.

---

## Deployment Topology

### Local development

```
NALLY (port 3000)  ←→  NallPuter (port 8000)
  same machine, localhost
```

### Render production

```
NALLY (public service)
  ↓ private networking
NallPuter (private service)
```

### 9B scope

Local only. Render deployment is Phase 10+.

---

## 9B Gate — Concrete Steps

### Step 1: NallPuter running

- NallPuter server started (`uvicorn nallputer.app.main:app`)
- `GET /v1/machine` returns `200` with `MachineProfile`
- `GET /v1/health` returns `200` with `status: "ok"`

### Step 2: NALLY config wired

- `NALLPUTER_URL=http://localhost:8000/v1` set in env
- `NALLPUTER_TOKEN` set to match NallPuter's expected token
- `nally/config.py` reads these values

### Step 3: Adapter initialization

```python
from nally.computer import ComputerAdapter, ComputerClient

client = ComputerClient()  # reads NALLPUTER_URL, NALLPUTER_TOKEN from env
adapter = ComputerAdapter(client)
result = adapter.preflight()

assert isinstance(result, PreflightResult)
assert result.machine is not None
assert result.health is not None
assert result.health.status == "ok"
```

### Step 4: Computer exists and is running

```python
assert adapter.computer_id != ""
assert adapter.describe()["ready"] is True
```

If no computer exists:
```python
from nally.computer import ComputerClient
client.create_computer()  # creates with default resources
# re-run preflight
```

### Step 5: Real exec through adapter

```python
result = adapter.exec("echo hello-from-nally")

assert isinstance(result, RunResult)
assert result.status == "succeeded"
assert "hello-from-nally" in result.stdout
assert result.exit_code == 0
```

This proves:
- POST /exec → run_id
- Poll GET /exec/{run_id} → terminal
- stdout returned correctly

### Step 6: Real file write through adapter

```python
result = adapter.file_write(
    "/home/nally/workspace/test-9b.txt",
    "written by NALLY via ComputerAdapter"
)

assert isinstance(result, dict)
assert result["bytes_written"] > 0
```

### Step 7: Real file read through adapter

```python
result = adapter.file_read("/home/nally/workspace/test-9b.txt")

assert isinstance(result, dict)
assert "written by NALLY via ComputerAdapter" in result["content"]
```

### Step 8: Tool routing verification

```python
from nally.tools.registry import registry
from nally.tools.adapter_holder import get_adapter

# Wire adapter
registry.set_computer_adapter(adapter)
assert get_adapter() is adapter

# RunCommand routes through adapter
result = registry.execute_result("run_command", {"command": "echo routed-through-adapter"})
assert "routed-through-adapter" in result.to_llm_text()

# Clear adapter — falls back to local
registry.set_computer_adapter(None)
assert get_adapter() is None
```

### Step 9: Reasoning loop integration

The critical test. This requires NALLY's agent to actually use the adapter:

```
User: "Write 'hello world' to test.txt on the computer, then read it back"
  ↓
NALLY reasoning: I need to use the computer. Let me preflight first.
  ↓
Tool call: computer_preflight → PreflightResult (ready)
  ↓
NALLY reasoning: Computer is ready. Write the file.
  ↓
Tool call: file_write(path="test.txt", content="hello world") → success
  ↓
NALLY reasoning: File written. Now read it back to confirm.
  ↓
Tool call: file_read(path="test.txt") → content="hello world"
  ↓
NALLY reasoning: The file was written and read back successfully.
  ↓
Response: "Done. I wrote 'hello world' to test.txt and verified it by reading it back."
```

**This is the real proof.** Not a unit test. Not a mock. An actual reasoning loop that touches a real computer.

---

## Success Criteria

| # | Criterion | How verified |
|---|-----------|--------------|
| 1 | NallPuter reachable | `GET /v1/machine` returns 200 |
| 2 | Config loaded | `NALLPUTER_URL` and `NALLPUTER_TOKEN` read from env |
| 3 | Preflight passes | `adapter.preflight()` returns `PreflightResult` with `health.status == "ok"` |
| 4 | Computer running | `adapter.describe()["ready"] == True` |
| 5 | Real exec works | `adapter.exec("echo test")` returns `RunResult` with `status == "succeeded"` |
| 6 | Real file write works | `adapter.file_write(...)` returns `bytes_written > 0` |
| 7 | Real file read works | `adapter.file_read(...)` returns correct content |
| 8 | Tool routing works | `RunCommand`/`ReadFile`/`FileOps` route through adapter when wired |
| 9 | **Reasoning loop works** | Agent writes file → reads it back → reports success in natural language |

**All 9 must pass.**

---

## Evidence Package

9B produces:

1. **`tests/results/9b/REPORT.md`** — step-by-step results with assertions
2. **`tests/results/9b/evidence/`** — screenshots or logs of each step
3. **Commit** — `9b: E2E deployment validation passed`
4. **README update** — Phase 9 status updated

---

## What 9B Does NOT Cover

- Render deployment (Phase 10)
- Multiple concurrent computers
- Snapshot/pause flows (501 in v0.1)
- Egress policy testing
- Package install durability
- Reconnect under failure (requires killing NallPuter mid-exec)

---

## Implementation Plan

### Pre-conditions

- NallPuter running locally on port 8000
- NALLY repo has Slices 1–4 committed
- `NALLPUTER_URL` and `NALLPUTER_TOKEN` set in environment

### Steps

1. Add `NALLPUTER_URL`/`NALLPUTER_TOKEN` to `nally/config.py`
2. Write `tests/test_9b_e2e.py` with steps 1–8 as test functions
3. Run tests against live NallPuter
4. Manual step 9: run NALLY agent with computer tools enabled, give it a write+read task
5. Capture evidence
6. Write REPORT.md
7. Commit

### Timeline

This is validation, not construction. Should complete in one session.
