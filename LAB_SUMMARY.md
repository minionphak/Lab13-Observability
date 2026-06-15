# Lab 13 Observability — Command & Function Reference

> Solo project: **Phạm Hoàng Anh Kiệt (2A202600797)** | All commands run from the project root: `c:\VinUNI\day 13\Lab13-Observability`

---

## Verification Status

| Check | Result |
|---|---|
| `GET /health` | ✅ `ok: true` |
| `POST /chat` | ✅ Returns answer + `correlation_id` |
| `GET /metrics` | ✅ Latency / cost / token data |
| `POST /incidents/rag_slow/enable` | ✅ State toggles correctly |
| `scripts/load_test.py --concurrency 5` | ✅ All 200 OK |
| `scripts/validate_logs.py` | ✅ **100/100** |
| `pytest tests/ -v` | ✅ 2 passed |

---

## 0. Prerequisites

```powershell
# Activate virtual environment (Windows)
.venv\Scripts\Activate.ps1

# Or call executables directly without activating
.venv\Scripts\python.exe   # Python interpreter
.venv\Scripts\uvicorn.exe  # ASGI server
```

---

## 1. Start the Server

```powershell
# Foreground — see logs live in terminal
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload

# Background / silent (for scripting)
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --log-level warning

# With environment overrides
$env:APP_ENV = "prod"; $env:LOG_LEVEL = "DEBUG"
.venv\Scripts\uvicorn.exe app.main:app --port 8000
```

Server base URL: `http://127.0.0.1:8000`

---

## 2. API Endpoints

### GET `/health`
Returns service status, tracing toggle, and active incident flags.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```
```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "ok": true,
  "tracing_enabled": false,
  "incidents": { "rag_slow": false, "tool_fail": false, "cost_spike": false }
}
```

---

### GET `/metrics`
Live observability snapshot — latency percentiles, cost, tokens, quality, error breakdown.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/metrics
```
```bash
curl http://127.0.0.1:8000/metrics
```

**Response fields:**

| Field | Description |
|---|---|
| `traffic` | Total requests served |
| `latency_p50 / p95 / p99` | Latency percentiles (ms) |
| `avg_cost_usd` | Average cost per request |
| `total_cost_usd` | Cumulative cost |
| `tokens_in_total / tokens_out_total` | Token counters |
| `quality_avg` | Heuristic quality score (0–1) |
| `error_breakdown` | `{ "ErrorType": count }` |

---

### POST `/chat`
Main inference endpoint. Logs, traces, and updates metrics on every call.

```powershell
$body = @{
    user_id    = "student-001"
    session_id = "sess-abc"
    feature    = "rag"      # also: "qa", "summary"
    message    = "What is observability?"
} | ConvertTo-Json

Invoke-RestMethod http://127.0.0.1:8000/chat -Method POST `
    -Body $body -ContentType "application/json"
```
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"student-001","session_id":"sess-abc","feature":"rag","message":"What is observability?"}'
```

**Response fields:**

| Field | Description |
|---|---|
| `answer` | LLM response text |
| `correlation_id` | Unique request ID `req-<8hex>` — also in `X-Correlation-ID` response header |
| `latency_ms` | End-to-end latency |
| `tokens_in / tokens_out` | Token usage |
| `cost_usd` | Estimated cost |
| `quality_score` | Heuristic score (0–1) |

---

### POST `/incidents/{name}/enable`
Activates a chaos scenario.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/incidents/rag_slow/enable  -Method POST
Invoke-RestMethod http://127.0.0.1:8000/incidents/tool_fail/enable -Method POST
Invoke-RestMethod http://127.0.0.1:8000/incidents/cost_spike/enable -Method POST
```
```bash
curl -X POST http://127.0.0.1:8000/incidents/rag_slow/enable
```

### POST `/incidents/{name}/disable`
Deactivates a chaos scenario.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/incidents/rag_slow/disable -Method POST
```
```bash
curl -X POST http://127.0.0.1:8000/incidents/rag_slow/disable
```

---

## 3. Scripts

### Load Test
Sends concurrent chat requests and prints per-request status / latency.

```powershell
.venv\Scripts\python.exe scripts/load_test.py --concurrency 5
```

| Flag | Description |
|---|---|
| `--concurrency N` | Number of parallel workers (default: 1) |

---

### Inject Incident
Toggles an incident flag through the API programmatically.

```powershell
# Enable
.venv\Scripts\python.exe scripts/inject_incident.py --scenario rag_slow

# Disable
.venv\Scripts\python.exe scripts/inject_incident.py --scenario rag_slow --disable
```

Available names: `rag_slow` · `tool_fail` · `cost_spike`

---

### Validate Logs
Parses `data/logs.jsonl` and grades output. No server needed — runs against the file directly.

```powershell
.venv\Scripts\python.exe scripts/validate_logs.py
```

**Checks performed:**

| Check | Pass condition |
|---|---|
| Basic JSON schema | Every record has `ts`, `level`, `event` |
| Correlation ID propagation | ≥ 2 unique `correlation_id` values |
| Log enrichment | API records include `user_id_hash`, `session_id`, `feature`, `model` |
| PII scrubbing | No raw `@` or credit card patterns (`4111`) in logs |

Score: **100/100** when all four pass.

---

## 4. Tests

```powershell
# Run all tests
.venv\Scripts\python.exe -m pytest tests/ -v

# Run one file
.venv\Scripts\python.exe -m pytest tests/test_pii.py -v
.venv\Scripts\python.exe -m pytest tests/test_metrics.py -v
```

| Test file | What it covers |
|---|---|
| `tests/test_pii.py` | `scrub_text` — email / credit-card redaction |
| `tests/test_metrics.py` | `_percentile` — latency percentile math |

---

## 5. Key Internal Functions

### `app/pii.py`

| Function | Signature | Description |
|---|---|---|
| `scrub_text` | `(text: str) -> str` | Replaces emails → `[REDACTED_EMAIL]`, credit cards → `[REDACTED_CREDIT_CARD]`, phones → `[REDACTED_PHONE_VN]`, etc. |
| `hash_user_id` | `(user_id: str) -> str` | SHA-256 hex of `user_id`, first 16 chars — never stores raw ID |
| `summarize_text` | `(text: str, max_len=80) -> str` | Truncates long strings for safe log previews |

---

### `app/logging_config.py`

| Symbol | Description |
|---|---|
| `configure_logging()` | Call once at startup; wires up structlog pipeline: `merge_contextvars → add_log_level → TimeStamper → scrub_event → JsonlFileProcessor → JSONRenderer` |
| `get_logger()` | Returns the bound structlog logger instance |
| `scrub_event(_, __, event_dict)` | Structlog processor — runs `scrub_text` on every `payload` string and the `event` field before writing |
| `JsonlFileProcessor` | Appends each log line as JSON to `data/logs.jsonl` |
| `LOG_PATH` | `Path(os.getenv("LOG_PATH", "data/logs.jsonl"))` |

---

### `app/middleware.py`

| Class | Description |
|---|---|
| `CorrelationIdMiddleware` | Per-request: calls `clear_contextvars()`, reads `x-request-id` header or generates `req-<8hex>`, binds it via `bind_contextvars`, sets `X-Correlation-ID` + `X-Response-Time-Ms` on response |

---

### `app/metrics.py`

| Function | Description |
|---|---|
| `record_request(latency_ms, cost_usd, tokens_in, tokens_out, quality_score)` | Appends one request's data to in-memory store |
| `record_error(error_type: str)` | Increments error counter for that type |
| `snapshot() -> dict` | Returns full metrics dict; computes percentiles on demand |

---

### `app/agent.py` — `LabAgent`

| Method | Description |
|---|---|
| `__init__(model="claude-sonnet-4-5")` | Initialises `FakeLLM` with the chosen model |
| `run(user_id, feature, session_id, message) -> AgentResult` | RAG → LLM pipeline; decorated with `@observe()` for Langfuse tracing |
| `_estimate_cost(tokens_in, tokens_out) -> float` | `(in / 1M × $3) + (out / 1M × $15)` |
| `_heuristic_quality(question, answer, docs) -> float` | Returns 0–1 score: +0.2 if docs present, +0.1 if answer > 40 chars, +0.1 keyword overlap, −0.2 if `[REDACTED` in answer |

---

### `app/incidents.py`

| Function | Description |
|---|---|
| `enable(name: str)` | Sets `STATE[name] = True`; raises `KeyError` for unknown names |
| `disable(name: str)` | Sets `STATE[name] = False` |
| `status() -> dict` | Returns `{ "rag_slow": bool, "tool_fail": bool, "cost_spike": bool }` |

---

### `app/tracing.py`

| Symbol | Description |
|---|---|
| `observe()` | Decorator from `langfuse.decorators`; gracefully falls back to no-op when Langfuse keys are absent |
| `langfuse_context` | Used in `LabAgent.run` — `.update_current_trace(user_id, session_id, tags)` and `.update_current_observation(metadata, usage_details)` |
| `tracing_enabled() -> bool` | `True` only when both `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set |

---

## 6. Environment Variables

Defined in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `dev` | Environment tag injected into every log line |
| `APP_NAME` | `day13-observability-lab` | Service name in startup log |
| `LOG_LEVEL` | `INFO` | Python logging level: `DEBUG`, `INFO`, `WARNING` |
| `LOG_PATH` | `data/logs.jsonl` | JSONL log output file |
| `AUDIT_LOG_PATH` | `data/audit.jsonl` | Audit log path (bonus) |
| `LANGFUSE_PUBLIC_KEY` | _(empty)_ | Enables Langfuse tracing when set |
| `LANGFUSE_SECRET_KEY` | _(empty)_ | Enables Langfuse tracing when set |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse endpoint |

---

## 7. Full From-Scratch Walkthrough

```powershell
# Step 1 — Activate environment
.venv\Scripts\Activate.ps1

# Step 2 — Start the server (new terminal or background)
.venv\Scripts\uvicorn.exe app.main:app --port 8000 --reload

# Step 3 — Confirm it's alive
Invoke-RestMethod http://127.0.0.1:8000/health

# Step 4 — Send a single chat request
Invoke-RestMethod http://127.0.0.1:8000/chat -Method POST `
  -Body '{"user_id":"u1","session_id":"s1","feature":"qa","message":"What is tracing?"}' `
  -ContentType "application/json"

# Step 5 — Generate enough logs for grading
.venv\Scripts\python.exe scripts/load_test.py --concurrency 5

# Step 6 — Inject the rag_slow incident and observe
.venv\Scripts\python.exe scripts/inject_incident.py --scenario rag_slow
.venv\Scripts\python.exe scripts/load_test.py --concurrency 3
Invoke-RestMethod http://127.0.0.1:8000/metrics
.venv\Scripts\python.exe scripts/inject_incident.py --scenario rag_slow --disable

# Step 7 — Check full metrics snapshot
Invoke-RestMethod http://127.0.0.1:8000/metrics

# Step 8 — Validate logs (must be 100/100)
.venv\Scripts\python.exe scripts/validate_logs.py

# Step 9 — Run the test suite
.venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 8. Git Commit Log

> Updated each session. Run `git log --oneline` to refresh.

| Hash | Message | Author |
|---|---|---|
| `96a6003` | feat: implement observability lab — solo submission | **Phạm Hoàng Anh Kiệt** |
| `9ac5e22` | docs: update scoring metric to 60/40 split and update grading policy | Instructor |
| `350e2f0` | docs: update report template for machine-parsing and individual contribution | Instructor |
| `e3735b0` | feat: initial gapped template for observability lab | Instructor |

### Commits by This Student (Phạm Hoàng Anh Kiệt)

All implementation work below was committed on the `main` branch:

```powershell
# View full log with files changed
git log --stat

# View diff for a specific commit
git show <hash>

# Show only your commits (by author)
git log --author="Pham Hoang Anh Kiet" --oneline
```

### What each implementation commit covers

| Area | Files changed | Key behaviour added |
|---|---|---|
| Middleware | `app/middleware.py` | `clear_contextvars`, `req-<8hex>` ID, `bind_contextvars`, response headers |
| Logging | `app/logging_config.py` | `scrub_event` PII processor, `JsonlFileProcessor`, structlog pipeline |
| PII | `app/pii.py` | Regex scrubbers: email, credit card, VN phone, passport, address |
| Enrichment | `app/main.py` | `bind_contextvars` in `/chat`: user_id_hash, session_id, feature, model, env |
| Tracing | `app/tracing.py` | `@observe()` fallback no-op, `langfuse_context` helpers |
| Alerts | `config/alert_rules.yaml` | 4 rules: high_latency_p95, high_error_rate, cost_budget_spike, low_quality_score |
