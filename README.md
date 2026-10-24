# Sales & Operations Intelligence Dashboard

> **Braahmam International Limited — Intern Assignment Prototype**  
> 2-day scoped prototype · Synthetic data only · Not production-ready

---

## Live Demo & Repository

- **Public Demo**: https://sales-operations-intelligence-dashboard.streamlit.app/
- **Local URL**: `http://localhost:8501`
- **Video Demo Walkthrough Guide**: https://drive.google.com/file/d/1C2W-_FVJK0RMOE_tyW2F5dYZNkGmKTVW/view?usp=sharing

---

## What It Does

Combines data from three separate synthetic sources — a CRM system (GoHighLevel), an operations system (Plunet), and a planning spreadsheet (Google Sheets) — into a single interactive intelligence dashboard. The application demonstrates how multi-source business data can be extracted, normalised, joined, persisted in a lightweight relational database, and presented to sales reps and executive managers with zero LLM hallucination risk.

---

## Quick Start (Run Locally)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/sales-ops-dashboard.git
cd sales-ops-dashboard

# 2. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 3. Generate synthetic datasets (reproducible seed)
python generate_data.py

# 4. Launch the dashboard
streamlit run app.py
# Browser will open automatically at http://localhost:8501
```

---

## Project Structure

```text
.
├── app.py                    # Main Streamlit application (4 tabs, 5 filters, drilldowns)
├── generate_data.py          # Synthetic data generator (22-month realistic distribution)
├── test_all.py               # Smoke & regression test runner (34 automated checks)
├── requirements.txt          # Python dependencies
├── README.md                 # Setup guide, architecture, evaluation rubric
│
├── data/
│   ├── crm_leads.csv         # Source 1: CRM leads (200 records)
│   ├── ops_projects.json     # Source 2: Operations projects (150 records)
│   ├── targets_sheet.csv     # Source 3: Google Sheets targets/forecast (770 rows)
│   └── intelligence.db       # Relational storage: SQLite embedded database
│
├── src/
│   ├── data_loader.py        # Ingestion, date/type coercion, normalization, SQLite sync
│   ├── data_quality.py       # Auditing nulls, duplicates, and join match rates
│   ├── insights.py           # 8 rule-based analytical insights (including YoY trends)
│   ├── charts.py             # 16 Plotly chart builders with empty-state guards
│   └── __init__.py
│
├── docs/
│   ├── DATA_DICTIONARY.md    # Field-level dictionary and join specifications
│   ├── ARCHITECTURE.md       # Component diagrams, technology trade-offs, evolution
│   ├── PRODUCTION_ROADMAP.md # 5-phase path to an enterprise-grade internal tool
│   └── DEMO_SCRIPT.md        # 3–5 minute screen recording script & talking points
│
└── .streamlit/
    └── config.toml           # UI styling & color theme
```

---

## Technology Stack & Rationale

| Layer | Technology | Rationale & Trade-offs |
|---|---|---|
| **Dashboard UI** | **Streamlit** | Rapid prototyping; native reactive state; zero-boilerplate interactive widgets. Replaced by React/Next.js in long-term enterprise phase. |
| **Data Processing** | **Pandas** | In-memory joins, groupings, and temporal aggregations. Scales efficiently for scoped datasets; evolution path to dbt + DuckDB/BigQuery. |
| **Chart Visualisation** | **Plotly Express & Graph Objects** | Interactive zoom/hover, consistent responsive layouts, and unified color palettes. |
| **Relational Storage** | **SQLite (`intelligence.db`)** | Embedded SQL database satisfying PRD Section 4.1 lightweight DB requirements with zero server configuration. |
| **AI / Insights** | **Deterministic Rule Engine** | 100% explainable, zero API cost, transparent thresholds, and completely guarded against LLM hallucinations. |
| **Hosting** | **Streamlit Community Cloud** | Free, GitHub-backed, automatic CI/CD deployment on push. |

---

## Data Sources & Join Strategy

| Source | File | Format | Records | Represents |
|---|---|---|---|---|
| **CRM** | `data/crm_leads.csv` | CSV | 200 leads | GoHighLevel CRM |
| **Operations** | `data/ops_projects.json` | JSON | 150 projects | Plunet Operations System |
| **Targets Sheet** | `data/targets_sheet.csv` | CSV | 770 rows | Google Sheets monthly planning export |
| **Relational DB** | `data/intelligence.db` | SQLite | 4 tables | Embedded relational store (PRD 4.1) |

### Join Strategy
- **Bridge Key**: `ops_projects.client_id == crm_leads.company` (exact string match).
- **Join Type**: Left outer join — all operations records are preserved.
- **Intentional Gaps**: 3 operations clients (`Zenith Consulting`, `Arc Analytics`, `Prism Solutions`) are purposefully omitted from CRM data (~19% unmatched rate) to simulate real-world data discrepancies.
- **Double-Counting Prevention**: Single-source domain tables are used for all dashboard KPIs; the joined table is reserved exclusively for the combined sales-to-ops view.

---

## Dashboard Features

### 1. Sales Dashboard (Tab 1)
- **Top KPIs**: Total Leads, Open Pipeline Value (USD), Closed Won, Win Rate (%), and Average Deal Value.
- **Visualisations**:
  - Monthly lead acquisition curve
  - Opportunity Status Breakdown (Won vs Lost vs Open)
  - Pipeline Funnel by Stage
  - Channel distribution by Source
  - Open pipeline value by Sales Rep
  - Regional market breakdown (donut)
  - Stale leads breakdown by Owner (>14 days inactive)
- **Stage Conversion Efficiency Table**: Displays stage-to-stage step drop-off and overall conversion with explicitly defined denominators (PRD Section 6.2).
- **Record Inspection Drawer**: Expandable table allowing managers to inspect individual open opportunities behind the pipeline KPI (PRD Section 6.4).

### 2. Operations Dashboard (Tab 2)
- **Top KPIs**: Total Projects, Active Projects, Overdue Count, Completed Count, Total Revenue (USD).
- **Visualisations**:
  - Project volume by status and stacked timeline
  - Active workload by Team (Alpha, Beta, Gamma, Delta)
  - Active workload by Client (Top 10 accounts)
  - Revenue distribution by Service Type (Translation, Localization, etc.)
  - SLA Compliance (Met vs Breached vs Pending)
  - Target vs Forecast vs Actual Revenue timeline (PRD Section 6.3)
- **Combined Sales-to-Ops View**: Highlights revenue by client with color-coded CRM match indicators (Green = CRM matched, Red = Unmatched client).
- **Record Inspection Drawer**: Expandable table for overdue and at-risk project drilldown.

### 3. Insights & Multi-Year Trends (Tab 3)
- **8 Rule-Based Analytical Insights**:
  1. Lead Volume MoM Trajectory
  2. Year-over-Year Lead Comparison (2025 vs 2026 across matching months)
  3. Pipeline Concentration Risk (>40% held by a single rep)
  4. Stale Leads Alert (inactive deals requiring follow-up)
  5. Stage Win Rate Benchmarking (vs 40% threshold)
  6. Overdue Project Rate Warning (>15% active work)
  7. SLA Breach Rate Alert (>10% completed work)
  8. Target vs Won Revenue Gap
- **Multi-Year Trend Analysis**: Grouped bar chart comparing 2025 vs 2026 month-for-month inbound leads (PRD Section 7 Question 5).

### 4. Data Quality & SQLite Explorer (Tab 4)
- **Auditing**: Missing values, duplicates, and unmatched record lists per source.
- **Embedded SQLite Integration**: Status of tables in `intelligence.db` plus a **Live SQL Query Runner** allowing evaluators to execute ad-hoc SQL queries directly inside the browser.
- **Documentation**: Inline Data Dictionary and KPI mathematical formulas.
- **Raw Data Preview**: Sample tables for all source datasets.

### 5. Interactive Filtering (Sidebar)
- 5 simultaneous global filters: **Date Range**, **Region**, **Owner / Sales Rep**, **Pipeline Stage**, and **Operations Status**.
- Instant cascading updates across all charts, KPIs, and insight engines.

---

## Assumptions, Completed Features, Known Defects & AI Dependencies
*(Required by PRD Section 13 & Candidate Submission Checklist)*

### Assumptions
1. **Synthetic Environment**: All client, prospect, employee, and financial records are entirely synthetic.
2. **Identifier Consistency**: In this prototype, company names serve as the foreign key between CRM and Ops. Production requires canonical UUID mapping.
3. **Currency & Locale**: All amounts are assumed to be USD. Multi-currency conversions are excluded.
4. **Stale Threshold**: 14 calendar days of inactivity constitutes a stale lead requiring sales follow-up.
5. **Win Rate Denominator**: Defined strictly as `Closed Won / (Closed Won + Closed Lost)`. Open stages are excluded.

### Completed Features
- [x] Three separately identifiable sample datasets (CRM CSV, Ops JSON, Sheets CSV).
- [x] Embedded lightweight database (SQLite `intelligence.db`) with live query execution.
- [x] Dedicated Sales and Management/Operations dashboard views.
- [x] Combined Sales-to-Operations cross-source reconciliation view.
- [x] Target vs. Forecast vs. Actual multi-line variance visualization.
- [x] Five reactive sidebar filters with cache-clearing refresh mechanism.
- [x] Eight deterministic analytical insights separating observed metrics from recommendations.
- [x] Multi-year (2025 vs 2026) Year-over-Year trend comparison.
- [x] Record-level inspection expanders for open deals and overdue projects.
- [x] Data quality audits, data dictionary, architecture summary, and production roadmap.

### Incomplete / Out-of-Scope Features (as defined in PRD Section 4.2)
- Direct OAuth2 connection to live GoHighLevel, Plunet, or Google accounts.
- Automated ML predictive forecasting models (replaced by explainable rule-based insights).
- Enterprise multi-tenant Role-Based Access Control (RBAC) and SSO.

### Known Defects / Technical Trade-offs
- **Single-Process Streamlit State**: Slicing happens in-memory via Pandas; concurrent enterprise workloads will require migration to FastAPI + Postgres.
- **Join Key Fragility**: Client name matching is susceptible to typos in real-world scenarios without fuzzy matching or UUID normalization.

### AI & API Dependencies
- **Zero External API Dependencies**: The prototype runs fully offline without relying on OpenAI, Anthropic, or external LLM APIs.
- **Governance Alignment**: Complies with PRD Section 6.5 and Section 9 by guaranteeing zero data leakage, zero hallucinations, and 100% data traceability.

---

## Automated Smoke Tests

```bash
python test_all.py
```
**Test Coverage (34 Checks)**:
- Ingestion of CRM, Ops, Targets, and Joined tables.
- Derived columns (`stale_lead`, `days_since_activity`, `is_overdue`).
- SQLite table creation and SQL query execution.
- Quality report calculation and non-zero unmatched record verification.
- Output integrity for all 8 analytical insights.
- Generation of all 16 Plotly chart figures.
- Empty-DataFrame edge-case resilience testing for charts.

---

## Deployment (Streamlit Community Cloud)

1. Push this repository to GitHub:
   ```bash
   git add -A
   git commit -m "feat: complete sales & operations dashboard prototype"
   git push origin main
   ```
2. Navigate to [share.streamlit.io](https://share.streamlit.io) and log in.
3. Select **Create app** → connect your GitHub repository.
4. Set **Main file path** to `app.py`.
5. Click **Deploy**.

---

*Submitted for the Braahmam International Limited Intern Assignment.* 
                 BY  SHIBA PRASAD SAHU 
