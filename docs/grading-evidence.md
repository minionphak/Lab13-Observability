# Evidence Collection Sheet

## Required screenshots

### 1. Langfuse trace list (≥10 traces)
![Trace list](evidence/01_trace_list.png)

### 2. Full trace waterfall
![Trace waterfall — run > retrieve > generate](evidence/02_trace_waterfall.png)

### 3. JSON logs showing correlation_id
![Log with correlation_id](evidence/04_correlation_id_log.png)

### 4. Log line with PII redaction
![PII redacted log](evidence/05_pii_redaction_log.png)

### 5. Dashboard with 6 panels
![6-panel dashboard](evidence/06_dashboard.png)

### 6. Alert rules with runbook link
![Alert rules yaml](evidence/07_alert_rules.png)

---

## Optional screenshots

### Incident before/after fix
![rag_slow incident — retrieve span 2.50s](evidence/03_incident_waterfall.png)

### validate_logs.py score
100/100 — all checks passed (correlation IDs, enrichment, PII scrubbing, JSON schema).
