# Production-Readiness Roadmap

## Phase 1 — Live Data Integration (Weeks 1–4)

### GHL (CRM) Integration
- Register OAuth2 app in GHL developer portal
- Implement authorization code flow; store tokens in secrets manager (not Git)
- Fetch contacts, opportunities and activities via GHL REST API v2
- Handle pagination (cursor-based), rate limits (429 backoff) and webhook events for real-time updates
- Incremental sync: store `lastUpdated` cursor in DB; fetch only changed records

### Google Sheets Integration
- Create GCP service account; grant read access to target spreadsheets
- Use Google Sheets API v4 to pull named ranges or full sheets
- Schedule hourly refresh via Cloud Scheduler → Cloud Run job
- Validate column schema on each pull; alert on breaking changes

### Operations System (Plunet)
- Evaluate REST vs SOAP API; generate client from WSDL if needed
- Authenticate with API key stored in Secret Manager
- Delta sync jobs triggered on project status change (webhook) or hourly poll

---

## Phase 2 — Data Infrastructure (Weeks 3–8)

### Canonical Data Model
- Define UUID-based entity identifiers across CRM, Ops and Sheets
- Maintain a mapping table: `crm_lead_id ↔ ops_client_id ↔ sheets_account_id`
- Version and document the canonical schema; enforce with schema registry

### Database / Data Warehouse
- **Operational DB**: PostgreSQL for normalized tables and FK integrity
- **Analytics layer**: BigQuery or DuckDB for aggregations and KPI calculations
- **dbt** for transformation, testing and lineage documentation

### Data Quality Pipeline
- Great Expectations (or dbt tests) on every ingested batch
- Alert on: null rates above threshold, schema drift, stale data, duplicate keys
- Data quality dashboard showing freshness, completeness, accuracy per source

---

## Phase 3 — Access Control & Security (Weeks 5–10)

### Role-Based Access
| Role | Access |
|---|---|
| Sales Rep | Own leads/pipeline; no other reps' data |
| Sales Manager | Full sales dashboard; all reps |
| Ops Team | Operations dashboard only |
| Admin | All data + quality reports + configuration |

- Implement via SSO (Google Workspace / Azure AD) + JWT claims
- Row-level security in PostgreSQL (RLS policies)

### Security Requirements
- All secrets (API keys, DB passwords, OAuth tokens) in GCP Secret Manager
- TLS everywhere; no HTTP endpoints
- Encryption at rest for all databases (AES-256)
- Audit log every data access and filter change (append-only table)
- GDPR/data retention: define retention periods per data type; auto-purge jobs
- Penetration test before production launch

---

## Phase 4 — Reliability & Observability (Weeks 8–12)

### Testing Strategy
- Unit tests for all KPI calculation functions (pytest)
- Integration tests for join correctness and deduplication
- Freshness tests: alert if source data > N hours old
- Access control tests: assert role restrictions hold
- Regression suite on KPI values after schema changes

### CI/CD
- GitHub Actions: lint → test → build Docker image → push to Artifact Registry
- Staging environment for review; production deploy requires passing tests + approval

### Monitoring
- Cloud Monitoring / Grafana: dashboard load time, data pipeline latency, error rates
- Alerts: PagerDuty/Slack for pipeline failures, SLA breach spikes, auth errors

### Performance
- Pre-aggregate heavy KPIs into materialized views (refresh every 15 min)
- CDN for static assets; Streamlit → React for sub-second filter response
- Horizontal scaling: Cloud Run min-instances > 0 to avoid cold starts

---

## Phase 5 — AI Governance (Ongoing)

- Only anonymised / synthetic KPI summaries sent to any LLM
- Log every LLM prompt and response; human review for flagged anomalies
- Uncertainty quantification: display confidence intervals, not point forecasts
- Safeguards: block LLM from inventing missing data; validate output against source records
- Quarterly model evaluation against business outcomes

---

## Phased Roadmap Summary

| Phase | Weeks | Milestone | Risk |
|---|---|---|---|
| 1 | 1–4 | Live GHL + Sheets + Plunet ingestion | API access delays |
| 2 | 3–8 | Canonical model, DWH, dbt | Schema conflicts between systems |
| 3 | 5–10 | RBAC, SSO, audit logs | Identity provider integration complexity |
| 4 | 8–12 | CI/CD, monitoring, performance | Infra cost and team capacity |
| 5 | Ongoing | AI governance, LLM insights | Data quality / hallucination risk |

**Indicative effort**: 2–3 engineers for 3 months to reach a dependable internal tool.

