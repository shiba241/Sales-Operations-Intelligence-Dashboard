# Architecture Summary

## Overview

The prototype follows a simple **single-process, file-based architecture** optimised for a two-day build.

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Browser UI               │
│  Sales Dashboard | Ops Dashboard | Insights | Docs  │
└─────────────────────────┬───────────────────────────┘
                          │ HTTP (localhost / Cloud)
┌─────────────────────────▼───────────────────────────┐
│               Streamlit App (app.py)                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │
│  │ data_loader│  │  insights  │  │    charts.py   │ │
│  │    .py     │  │    .py     │  │  (Plotly figs) │ │
│  └────────────┘  └────────────┘  └────────────────┘ │
│  ┌────────────┐                                      │
│  │data_quality│                                      │
│  │    .py     │                                      │
│  └────────────┘                                      │
└─────────────────────────┬───────────────────────────┘
                          │ File I/O (Pandas)
┌─────────────────────────▼───────────────────────────┐
│                  Data Layer (./data/)                │
│  crm_leads.csv │ ops_projects.json │ targets_sheet  │
└─────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| Entry point | `app.py` | Page layout, tabs, sidebar filters, KPIs |
| Data loading | `src/data_loader.py` | Parse, normalize, join, cache (5 min TTL) |
| Data quality | `src/data_quality.py` | Quality metrics for each source |
| Insights | `src/insights.py` | 7 rule-based analytical insights |
| Charts | `src/charts.py` | 13 Plotly chart builders |
| Data | `data/*.csv, *.json` | Static synthetic datasets |

## Data Flow

1. App starts → `load_all()` reads 3 files into Pandas DataFrames
2. `build_joined()` left-joins ops to CRM on `client_id = company`
3. Streamlit caches result for 5 minutes (`@st.cache_data(ttl=300)`)
4. User selects filters → DataFrames are sliced in-memory (no DB query)
5. Charts and insights receive filtered DataFrames and return Plotly figures

## Technology Choices and Trade-offs

### Streamlit
- **Pro**: Fastest path to a working Python dashboard; built-in widgets, caching, deployment
- **Con**: Not suited for enterprise RBAC or complex multi-page SPA experiences
- **Evolution**: Replace with React + FastAPI or Dash for production

### Pandas
- **Pro**: Expressive, well-known, handles CSV/JSON easily
- **Con**: Single-node, in-memory; won't scale beyond ~1M rows without chunking
- **Evolution**: dbt + DuckDB or Apache Spark for larger data

### File-based storage
- **Pro**: No server setup, version-controllable, portable
- **Con**: No ACID guarantees, no concurrent writes, no incremental refresh
- **Evolution**: PostgreSQL + SQLAlchemy or BigQuery for production

### Rule-based insights
- **Pro**: Deterministic, explainable, no LLM dependency or cost
- **Con**: Not adaptive; misses patterns not coded explicitly
- **Evolution**: Add LLM layer (Gemini / OpenAI) sending only synthetic KPI summaries

## Hosting

Streamlit Community Cloud — free tier, GitHub-backed, auto-deploys on push.

**Production alternatives**: GCP Cloud Run, AWS ECS, Azure Container Apps (containerise with Docker).

