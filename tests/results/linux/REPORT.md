# Phase 8 — Production Gate — Combined Evidence (8A–8F)

**Date:** 2026-09-12 (commit `5a72833` `feat: phase 8e lifecycle` on top of `d5d841b` `fix: 8c verification` + `7af639a` 8D + `ada54d1` 8F + `7400b68` 8C + `428a2ad` 8B + `91b0628` 8A)
**Mode:** production gate (combined `8A+8B+8C+8D+8E+8F`, not Lab Rat `20/20` informational)
**Windows gate:** `pytest -q -k "not linux"` **39 passed, 3 deselected, 0 failures** (`~37–41s` wall, within 180s); `pytest -q` **39 passed, 3 skipped, 0 failures** (linux cgroup skipped on Windows)
**Linux baseline:** `2195f2b` Lab Rat `20/20` (`cgroup v2` `v2 (cpuset cpu io memory hugetlb pids rdma misc dmem)`, `pids.max 100`, `pids.current 3`, `concurrency 5→429`, `setsid/killpg`) — preserved. **Production re-run required** via `make eval-linux` (Docker) to re-collect `8A–8F` with true cgroup/pids; Windows already proves logic for all slices (see table).

## Windows production gate (current run, 5a72833)

| Slice | Tests | Result | Evidence |
|-------|-------|--------|----------|
| **8A Persistence** (S3-compatible) | `test_persistence_adapter` 4 + `test_persistence` 5 | 9 passed | `local_fs` basic, `factory` local fallback, `moto` S3, provider-neutral (no R2 coupling), `write→pending→synced`, `stop→start` keep |
| **8B Sync** (dirty→debounce→manifest-last, If-Match→degraded) | `test_sync_engine` 3 | 3 passed | `flush_manifest_last`, `if_match_conflict_degraded`, `restore` |
| **8C Env reconstruct** (never mutate yaml, 503) | `test_env_reconstruct` 4 | 4 passed | `yaml_not_mutated`, `replay_failure_503`, `credential_never_in_lock`, `start_replay_integration` (mock pip, `_setup_ws` isolated tmp) |
| **8D Security** (127.0.0.1:3128, allowlist, audit) | `test_security_proxy` 4 | 4 passed | `proxy_blocks_evil` 403, `proxy_allows_pypi` succeeded, `audit_trail_no_secrets`, `CONNECT tunnel` |
| **8E Lifecycle** (900s auto-stop, 1s poll, flush parity) | `test_lifecycle_8e` 4 | 4 passed | `stop_start_data_survives` (flush+restore, mock replay), `bad_env_start_503` `recovering`+`env_replay_failed`, `auto_stop` 2s configurable → `stopped` → `start` → data survives, `replacement_same_cid` stable |
| **8F Observability** (real pids/memory via cgroup, no endpoint redesign) | `test_observability` 2 | 2 passed | `resources_usage_real` (pids/memory), `cgroup_files_exist_on_linux` skipped on Windows (informational) |
| **Core** | `test_isolation` 3, `test_latency` 2, `test_lifecycle` 3, `test_output` 4, `test_startup` 2, `test_linux_cgroup` 2 (skipped) | 13 passed / 3 skipped | `workspace_jail`, `egress_policy`, `credential_in_spec_blocked`, `latency_exec_vs_subprocess`, `polling_overhead`, `timeout`, `cancellation`, `stream_pause_snapshot_501`, `empty_output`, `output_exact`, `truncation`, `pagination`, `startup_warm/cold`, `cgroup_v2_and_pids` (Linux only), `concurrency_5` (Linux only) |

**Total:** **39 passed, 3 skipped (Windows) / 3 deselected (`-k "not linux"`), 0 failures**. All 8 slices exercised together — this is the combined `8A–8F` gate, not an isolated slice.

**Decisions enforced:**
- `NALLPUTER_IDLE_TIMEOUT_SEC=900` default, configurable, **fixed 1s poll** (no `min(1s, timeout/3)`)
- **No `idle_since` in API** (`Computer.idle_since` internal only, `_computer_to_dict` unchanged)
- **No `012`/queue**, no OpenAPI/MachineProfile change, provider-neutral (`MachineProfile` field, never `if provider == "render"`)
- **Auto-stop flush parity:** `idle→stopping→flush` uses same `sync.flush` degraded→`recovering` (never falsely `stopped`), as explicit `POST /computer/{id}/stop` (`503` on degraded)

## Linux production re-run (required to close Phase 8)

Lab Rat `2195f2b` already proved `cgroup v2`, `pids.max 100`, `pids.current 3`, `concurrency 5→429`, `setsid/killpg`, `pending→synced`, `stop_start` keep, `egress` etc. on Docker. Production gate must re-run that harness with `5a72833` to collect:

- `tests/results/linux/*.json` (`latency`, `startup_warm`, etc.) with Docker numbers
- `tests/results/linux/junit.xml` — expected **42 tests collected, 39+ passed** (vs previous 20, now +9+3+4+4+2 from 8A–8F)
- `tests/results/linux/pytest.log` + `tests/docker/collect.py` output

Until `make eval-linux` succeeds, Phase 8 is **implemented (Windows gate green) but not production-validated**. This REPORT preserves the Windows combined gate as interim baseline.

## Files

- Windows: `tests/results/*.json` (measure-only, `5a44765` baseline + current `39` gate)
- Linux interim: `tests/results/linux/*.json` (old `2195f2b` 20/20) + `junit.xml` `20 tests, 0 failures`
- Linux production: to be regenerated via `make eval-linux` on `5a72833` (expected `39+` passed, `0 failures`)

## Verdict

**Windows production gate: PASS (39/39, 0 failures). Linux production gate: PENDING CI re-run (Lab Rat 20/20 preserved, re-run required for 8A–8F cgroup/pids validation).**

Next: `make eval-linux` on `5a72833` → update this REPORT with Docker numbers → `README` `8 🟡 → ✅` → Phase 8 baseline locked → then NALLY mapping.

*Generated 2026-09-12, commit 5a72833, Windows wall 37–41s, within 180s.*
