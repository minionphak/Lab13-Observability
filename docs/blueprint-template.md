# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Solo — Phạm Hoàng Anh Kiệt
- [REPO_URL]: https://github.com/VinUni-AI20k/Lab13-Observability
- [MEMBERS]:
  - Member A: Phạm Hoàng Anh Kiệt (2A202600797) | Role: All — Logging, PII, Tracing, SLO & Alerts, Load Test, Dashboard, Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 10+
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: See data/logs.jsonl — every API log line contains a unique `correlation_id` in format `req-<8hex>`
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: See data/logs.jsonl — email addresses appear as `[REDACTED_EMAIL]`, credit cards as `[REDACTED_CREDIT_CARD]`
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: Langfuse trace waterfall (requires LANGFUSE keys)
- [TRACE_WATERFALL_EXPLANATION]: The `LabAgent.run` span is decorated with `@observe()`. It shows two child spans: RAG retrieval (mock_rag.retrieve) and LLM generation (FakeLLM.generate), with metadata including doc_count, token usage, and hashed user_id.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: Dashboard built from /metrics endpoint (6 panels: Latency P50/P95/P99, Traffic, Error Rate, Cost over time, Tokens in/out, Quality Score)
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | ~120ms (mock) |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | ~$0.0001 (mock) |
| Quality Score Avg | > 0.75 | 28d | ~0.8 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: See config/alert_rules.yaml — 4 alert rules configured (high_latency_p95, high_error_rate, cost_budget_spike, low_quality_score)
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#1-high-latency-p95

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Latency P95 exceeds 5000ms; traces show RAG retrieval span taking >4s; high_latency_p95 alert fires
- [ROOT_CAUSE_PROVED_BY]: Langfuse trace waterfall — RAG span latency spike visible vs baseline; log lines show `latency_ms > 5000` on request_received events with correlation_id
- [FIX_ACTION]: Disable rag_slow incident toggle via POST /incidents/rag_slow/disable; reduce retrieval timeout; add fallback retrieval source
- [PREVENTIVE_MEASURE]: Add circuit breaker on RAG retrieval; set hard timeout of 2s; alert fires within 30m of sustained P95 breach

---

## 5. Individual Contributions & Evidence

### Phạm Hoàng Anh Kiệt — 2A202600797 (Solo — All Roles)

**Logging & PII (app/middleware.py, app/logging_config.py, app/pii.py)**
- [TASKS_COMPLETED]: Implemented CorrelationIdMiddleware (clear_contextvars, req-<8hex> generation, bind_contextvars, X-Correlation-ID + X-Response-Time-Ms response headers); enabled scrub_event PII processor in logging_config.py; added email, credit card, phone, passport, and Vietnamese address regex patterns to pii.py; verified PII_LEAKS_FOUND: 0
- [EVIDENCE_LINK]: See app/middleware.py, app/logging_config.py, app/pii.py

**Tracing & Enrichment (app/main.py, app/agent.py, app/tracing.py)**
- [TASKS_COMPLETED]: Added bind_contextvars enrichment in main.py chat endpoint (user_id_hash, session_id, feature, model, env); verified @observe() decorator on LabAgent.run with langfuse_context metadata (user_id, session_id, tags, usage_details); tracing_enabled() gracefully falls back to no-op without Langfuse keys
- [EVIDENCE_LINK]: See app/main.py, app/agent.py, app/tracing.py

**SLO & Alerts (config/slo.yaml, config/alert_rules.yaml, docs/alerts.md)**
- [TASKS_COMPLETED]: Finalized config/slo.yaml with 4 SLIs (latency_p95, error_rate, daily_cost, quality_score_avg); added 4th alert rule low_quality_score to alert_rules.yaml; wrote runbook entries in docs/alerts.md for all 4 alert rules
- [EVIDENCE_LINK]: See config/slo.yaml, config/alert_rules.yaml, docs/alerts.md

**Load Test & Dashboard (scripts/, /metrics endpoint)**
- [TASKS_COMPLETED]: Ran scripts/load_test.py --concurrency 5 (all 200 OK); injected rag_slow scenario via scripts/inject_incident.py; observed /metrics for 6-panel dashboard data (latency P50/P95/P99, traffic, errors, cost, tokens in/out, quality score)
- [EVIDENCE_LINK]: See scripts/load_test.py, scripts/inject_incident.py

**Demo & Report (docs/, data/logs.jsonl)**
- [TASKS_COMPLETED]: Completed this blueprint report; ran scripts/validate_logs.py to verify 100/100 score; prepared incident response analysis for rag_slow scenario; maintained LAB_SUMMARY.md command reference
- [EVIDENCE_LINK]: See docs/blueprint-template.md, data/logs.jsonl, LAB_SUMMARY.md

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: FakeLLM uses claude-sonnet-4-5 pricing model; cost estimation via _estimate_cost() at $3/M input and $15/M output tokens; total cost tracked in /metrics snapshot; evidence: GET /metrics shows total_cost_usd
- [BONUS_AUDIT_LOGS]: AUDIT_LOG_PATH=data/audit.jsonl configured in .env; can be extended with a separate JsonlFileProcessor routing security events (incident toggles, auth failures) to audit.jsonl
- [BONUS_CUSTOM_METRIC]: Added 4th alert rule low_quality_score (quality_score_avg < 0.6 for 15m) as custom quality proxy metric beyond the required 3 alert rules
