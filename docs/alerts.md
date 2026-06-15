# Alert Rules and Runbooks

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95_ms > 5000 for 30m`
- Impact: tail latency breaches SLO
- First checks:
  1. Open top slow traces in the last 1h
  2. Compare RAG span vs LLM span
  3. Check if incident toggle `rag_slow` is enabled
- Mitigation:
  - truncate long queries
  - fallback retrieval source
  - lower prompt size

## 2. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 5 for 5m`
- Impact: users receive failed responses
- First checks:
  1. Group logs by `error_type`
  2. Inspect failed traces
  3. Determine whether failures are LLM, tool, or schema related
- Mitigation:
  - rollback latest change
  - disable failing tool
  - retry with fallback model

## 3. Cost budget spike
- Severity: P2
- Trigger: `hourly_cost_usd > 2x_baseline for 15m`
- Impact: burn rate exceeds budget
- First checks:
  1. Split traces by feature and model
  2. Compare tokens_in/tokens_out
  3. Check if `cost_spike` incident was enabled
- Mitigation:
  - shorten prompts
  - route easy requests to cheaper model
  - apply prompt cache

## 4. Low quality score
- Severity: P2
- Trigger: `quality_score_avg < 0.6 for 15m`
- Impact: users receive low-quality or irrelevant responses
- First checks:
  1. Review recent traces in Langfuse for low `quality_score` metadata
  2. Check if RAG retrieval is returning matched docs (`doc_count > 0`)
  3. Inspect `query_preview` in trace metadata for off-topic requests
  4. Verify no `[REDACTED` tokens leaked into the answer (score penalty)
- Mitigation:
  - expand CORPUS keywords in mock_rag.py to improve retrieval hit rate
  - add fallback answer quality check before returning response
  - if PII redaction is corrupting answers, review scrub_text patterns
