# NallPuter API Contract — Phase 3

**Spec:** `openapi.yaml` (OpenAPI 3.1)
**Depends on:** Decisions 003 (Machine Contract) + 004 (Persistent State)
**Auth:** `Authorization: Bearer <token>` — constant-time compare, pluggable to mTLS/JWT

## What this contract establishes

```
Identity → MachineProfile → Capabilities → Execution → Files → Process state → Errors → Persistence
```

See `003-machine-contract.md` for the provider-neutral `MachineProfile` and
`004-persistent-state.md` for why the runtime is disposable and the external
store is canonical.

## Quick start for NALLY

1. `GET /v1/machine` — cache `computer_id`, `persistence.*`, `capabilities`, `restart_behavior`, `ephemeral_paths`/`persistent_paths`.
2. `GET /v1/health` — assert `status: ok` and `sync_state: synced` before trusting workspace.
3. `POST /v1/exec` → `run_id`, then `GET /v1/exec/{run_id}?cursor=&limit=` polling. `DELETE /v1/exec/{run_id}` to cancel (kills process tree).
4. `POST /v1/files/{read,write,list}` — writes to `persistent_paths` are debounced → canonical store (004). Check `sync_pending` in run response.
5. If `persistence.packages == "reconstructible"`, write `environment.yaml` under `.nallputer/state/` and let the replay engine materialize packages on next `start`; see 004 § Environment.

## Stubbed endpoints (501)

These are present for forward-compat; v0.1 returns `501` with `capability` hint when `MachineProfile.capabilities.* == false`:

- `GET /v1/exec/{run_id}/stream` → `streaming_not_supported`
- `POST /v1/computer/{id}/pause|resume|snapshot` → `pause_not_supported` etc.

Do not retry with backoff; poll instead.

## Validation

```bash
# requires redocly or spectral
npx @redocly/cli lint docs/api/openapi.yaml
npx spectral lint docs/api/openapi.yaml
```
