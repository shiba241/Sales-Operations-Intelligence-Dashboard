# app.py
# Sales & Operations Intelligence Dashboard
# Braahmam International Limited — Interview Prototype (synthetic data only)
#
# Structure:
#   Sidebar  → global filters (date, region, owner, stage, ops status)
#   Tab 1    → Sales dashboard (KPIs + charts + conversion metrics + deal inspection)
#   Tab 2    → Operations dashboard (KPIs + charts + workload + combined view + overdue inspection)
#   Tab 3    → Analytical insights (rule-based flags + Year-over-Year comparison)
#   Tab 4    → Data quality report + SQLite database explorer + data dictionary

import os
import sys

# Make sure the src package resolves when running from any working directory
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import (
    chart_client_workload,
    chart_leads_by_region,
    chart_leads_by_source,
    chart_leads_by_stage,
    chart_leads_over_time,
    chart_pipeline_value_by_owner,
    chart_projects_by_status,
    chart_projects_over_time,
    chart_sales_to_ops,
    chart_sla_compliance,
    chart_stale_leads,
    chart_status_breakdown,
    chart_targets_vs_actuals,
    chart_workload_by_service,
    chart_workload_by_team,
    chart_yoy_comparison,
)
from src.data_loader import load_all, query_db
from src.data_quality import (
    crm_quality_report,
    join_quality_report,
    ops_quality_report,
    targets_quality_report,
)
from src.insights import get_all_insights

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sales & Ops Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .insight-warning { background:#fff3cd; border-left:4px solid #ffc107; padding:12px 16px; border-radius:6px; margin:6px 0; }
    .insight-success { background:#d4edda; border-left:4px solid #28a745; padding:12px 16px; border-radius:6px; margin:6px 0; }
    .insight-info    { background:#d1ecf1; border-left:4px solid #17a2b8; padding:12px 16px; border-radius:6px; margin:6px 0; }
    .stMetric { background-color: #fcfaff; padding: 10px; border-radius: 8px; border: 1px solid #ede8f5; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_data():
    """Cache the loaded data for 5 minutes. Clear it with the Refresh button."""
    return load_all()


with st.spinner("Loading data from sources..."):
    crm, ops, targets, joined, quality = get_data()


# ── Sidebar filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Sales & Ops Dashboard")
    st.caption("**Braahmam International Limited** — Scoped Prototype")
    st.divider()

    st.markdown("### 🔧 Global Filters")

    # Date range — defaults to the span of CRM data
    min_date = crm["created_date"].min().date()
    max_date = crm["created_date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_start = pd.Timestamp(date_range[0])
        d_end   = pd.Timestamp(date_range[1])
    else:
        d_start = pd.Timestamp(min_date)
        d_end   = pd.Timestamp(max_date)

    all_regions = sorted(crm["region"].dropna().unique())
    sel_regions = st.multiselect("Region", all_regions, default=all_regions)

    all_owners = sorted(crm["owner"].dropna().unique())
    sel_owners = st.multiselect("Owner / Sales Rep", all_owners, default=all_owners)

    all_stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
    sel_stages = st.multiselect("Pipeline Stage", all_stages, default=all_stages)

    all_ops_statuses = sorted(ops["status"].dropna().unique())
    sel_ops_statuses = st.multiselect("Ops Status", all_ops_statuses, default=all_ops_statuses)

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"📅 Data loaded: **{quality['load_time']}**")
    st.caption("💾 SQLite synced: `data/intelligence.db`")
    st.caption("⚠️ Synthetic sample data only")


# ── Apply filters ─────────────────────────────────────────────────────────────

crm_f = crm[
    (crm["created_date"] >= d_start) &
    (crm["created_date"] <= d_end) &
    (crm["region"].isin(sel_regions)) &
    (crm["owner"].isin(sel_owners)) &
    (crm["pipeline_stage"].isin(sel_stages))
].copy()

ops_f = ops[
    (ops["created_date"] >= d_start) &
    (ops["created_date"] <= d_end) &
    (ops["status"].isin(sel_ops_statuses))
].copy()

targets_f = targets[
    (targets["month"] >= d_start) &
    (targets["month"] <= d_end) &
    (targets["owner"].isin(sel_owners)) &
    (targets["region"].isin(sel_regions))
].copy()

joined_f = joined[
    (joined["created_date"] >= d_start) &
    (joined["created_date"] <= d_end) &
    (joined["status"].isin(sel_ops_statuses))
].copy()


# ── Page header ───────────────────────────────────────────────────────────────

st.title("📊 Sales & Operations Intelligence Dashboard")
st.caption(
    f"Active subset: **{len(crm_f):,} leads** & **{len(ops_f):,} projects**  |  "
    f"Sources: CRM (CSV) · Operations (JSON) · Targets (CSV) · Relational DB (SQLite)  |  "
    f"Loaded: {quality['load_time']}  |  Synthetic data only"
)


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_sales, tab_ops, tab_insights, tab_quality = st.tabs([
    "🏆 Sales Dashboard",
    "⚙️ Operations Dashboard",
    "🤖 Insights & Trends",
    "🔍 Data Quality & Docs",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — SALES DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

with tab_sales:

    open_deals  = crm_f[(crm_f["status"] == "Open") & (crm_f["deal_value"].notna())]
    won_deals   = crm_f[crm_f["status"] == "Won"]
    closed      = crm_f[crm_f["status"].isin(["Won", "Lost"])]

    win_rate  = (len(won_deals) / len(closed) * 100) if len(closed) > 0 else 0.0
    avg_deal  = open_deals["deal_value"].mean() if not open_deals.empty else 0.0
    pipe_val  = open_deals["deal_value"].sum()

    st.subheader("Sales KPIs")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Leads",           f"{len(crm_f):,}")
    col2.metric("Open Pipeline (USD)",   f"${pipe_val:,.0f}")
    col3.metric("Closed Won",            f"{len(won_deals):,}")
    col4.metric("Win Rate",              f"{win_rate:.1f}%")
    col5.metric("Avg Open Deal (USD)",   f"${avg_deal:,.0f}")

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_leads_over_time(crm_f), use_container_width=True)
    with c2:
        st.plotly_chart(chart_status_breakdown(crm_f), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(chart_leads_by_stage(crm_f), use_container_width=True)
    with c4:
        st.plotly_chart(chart_leads_by_source(crm_f), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(chart_pipeline_value_by_owner(crm_f), use_container_width=True)
    with c6:
        st.plotly_chart(chart_leads_by_region(crm_f), use_container_width=True)

    # Stage conversion table with explicitly defined denominators (PRD Section 6.2)
    st.subheader("Stage Conversion & Funnel Efficiency")
    st.caption("Denominator definitions: **Stage-to-Stage** = Count(Stage N) / Count(Stage N-1). **Funnel-to-Total** = Count(Stage N) / Total Leads.")

    stage_order = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Closed Won"]
    stage_counts = crm_f["pipeline_stage"].value_counts().reindex(stage_order, fill_value=0)
    total_leads_count = len(crm_f)

    conversion_rows = []
    prev_count = None
    for stage_name, count in stage_counts.items():
        step_conv = f"{(count / prev_count * 100):.1f}%" if prev_count and prev_count > 0 else "Baseline (100%)"
        overall_conv = f"{(count / total_leads_count * 100):.1f}%" if total_leads_count > 0 else "0.0%"
        conversion_rows.append({
            "Pipeline Stage": stage_name,
            "Lead Count": count,
            "Step Conversion (vs Previous)": step_conv,
            "Overall Conversion (vs Total Leads)": overall_conv,
            "Denominator Definition": f"Divided by {prev_count if prev_count else count} (Prior Stage)" if prev_count else f"Total Leads ({total_leads_count})",
        })
        prev_count = count

    st.dataframe(pd.DataFrame(conversion_rows), use_container_width=True)

    st.plotly_chart(chart_stale_leads(crm_f), use_container_width=True)

    # Record-level drilldown expanders (PRD Section 6.4)
    with st.expander("🔍 Inspect Open Opportunities & Pipeline Deals (Record Detail)"):
        st.caption("Drill down into individual open deals behind the Open Pipeline KPI.")
        if open_deals.empty:
            st.info("No open deals in the selected filter range.")
        else:
            st.dataframe(
                open_deals[[
                    "lead_id", "company", "owner", "region", "pipeline_stage",
                    "deal_value", "source", "last_activity_date", "days_since_activity"
                ]].sort_values("deal_value", ascending=False),
                use_container_width=True,
                height=250,
            )

    with st.expander("⚠️ Inspect Stale Leads Detail (No Activity > 14 Days)"):
        stale = crm_f[crm_f["stale_lead"]][[
            "lead_id", "company", "owner", "region",
            "pipeline_stage", "deal_value", "last_activity_date", "days_since_activity",
        ]].sort_values("days_since_activity", ascending=False)

        if stale.empty:
            st.success("No stale leads match the current filters.")
        else:
            st.dataframe(stale, use_container_width=True, height=250)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — OPERATIONS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

with tab_ops:

    op_active   = int(ops_f["status"].isin(["Open", "In Progress"]).sum())
    op_overdue  = int(ops_f["is_overdue"].sum())
    op_done     = int((ops_f["status"] == "Completed").sum())
    op_revenue  = ops_f["amount"].sum()

    st.subheader("Operations KPIs")
    o1, o2, o3, o4, o5 = st.columns(5)
    o1.metric("Total Projects",     f"{len(ops_f):,}")
    o2.metric("Active Projects",    f"{op_active:,}")
    o3.metric("Overdue Projects",   f"{op_overdue:,}", delta=f"-{op_overdue}", delta_color="inverse")
    o4.metric("Completed",          f"{op_done:,}")
    o5.metric("Total Revenue (USD)",f"${op_revenue:,.0f}")

    st.divider()

    p1, p2 = st.columns(2)
    with p1:
        st.plotly_chart(chart_projects_by_status(ops_f), use_container_width=True)
    with p2:
        st.plotly_chart(chart_projects_over_time(ops_f), use_container_width=True)

    p3, p4 = st.columns(2)
    with p3:
        st.plotly_chart(chart_workload_by_team(ops_f), use_container_width=True)
    with p4:
        st.plotly_chart(chart_client_workload(ops_f), use_container_width=True)

    p5, p6 = st.columns(2)
    with p5:
        st.plotly_chart(chart_workload_by_service(ops_f), use_container_width=True)
    with p6:
        st.plotly_chart(chart_sla_compliance(ops_f), use_container_width=True)

    st.plotly_chart(chart_targets_vs_actuals(crm_f, targets_f), use_container_width=True)

    # Combined Sales-to-Ops view
    st.subheader("Combined Sales-to-Operations View")
    st.info(
        f"Join key: **ops.client_id = crm.company** (exact name match). "
        f"**{quality['joined_matched']}** of **{quality['ops_total']}** ops projects "
        f"matched to a CRM account. "
        f"**{quality['joined_unmatched']}** are unmatched "
        f"(see Data Quality tab for details)."
    )
    st.plotly_chart(chart_sales_to_ops(joined_f), use_container_width=True)

    # Record inspection expanders (PRD Section 6.4)
    with st.expander("🚨 Inspect Overdue & High-Risk Projects (Record Detail)"):
        st.caption("Drill down into active projects that have passed their due dates.")
        overdue_records = ops_f[ops_f["is_overdue"]][[
            "project_id", "client_id", "service_type", "assigned_team",
            "amount", "created_date", "due_date", "sla_status"
        ]].sort_values("due_date", ascending=True)

        if overdue_records.empty:
            st.success("No overdue projects under current filter selection.")
        else:
            st.dataframe(overdue_records, use_container_width=True, height=220)

    # Target vs Actuals breakdown table
    st.subheader("Targets vs Forecast vs Actuals — Owner Detail")
    crm_won = crm_f[crm_f["status"] == "Won"].copy()
    crm_won["month"] = crm_won["created_date"].dt.to_period("M").dt.to_timestamp()
    actuals = crm_won.groupby(["month", "owner"])["deal_value"].sum().reset_index(name="actual_revenue")
    tgt     = targets_f.groupby(["month", "owner"])[["target_revenue", "forecast_revenue"]].sum().reset_index()

    tva = actuals.merge(tgt, on=["month", "owner"], how="outer").sort_values(["month", "owner"])
    tva["gap_usd"] = tva["actual_revenue"] - tva["target_revenue"]
    tva["gap_pct"] = (tva["gap_usd"] / tva["target_revenue"] * 100).round(1)

    if tva.empty:
        st.info("No matching data between won deals and targets for the selected filters.")
    else:
        st.dataframe(tva, use_container_width=True, height=260)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — INSIGHTS & TRENDS
# ═════════════════════════════════════════════════════════════════════════════

with tab_insights:
    st.subheader("🤖 Rule-Based Analytical Insights")
    st.markdown(
        "These deterministic insights are generated directly from the filtered datasets — no external LLM hallucination risk. "
        "Each insight separates **Observed Facts** from **Actionable Recommendations** and cites exact numbers."
    )

    ICONS = {"warning": "⚠️", "success": "✅", "info": "ℹ️"}

    insights = get_all_insights(crm_f, ops_f, targets_f)

    if not insights:
        st.success("No issues flagged for the current filters.")
    else:
        for item in insights:
            icon = ICONS.get(item["severity"], "ℹ️")
            css  = f"insight-{item['severity']}"
            st.markdown(
                f'<div class="{css}">'
                f"<strong>{icon} {item['title']}</strong><br>"
                f"<b>Observed:</b> {item['detail']}<br>"
                f"<b>Recommendation:</b> {item['recommendation']}"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # PRD Section 7 Question 5: Multi-Year Comparison
    st.subheader("📅 Previous Year Comparison (2025 vs 2026)")
    st.caption("Addressing PRD Question 5: Compare trends and volume against the previous year for strategic capacity planning.")
    st.plotly_chart(chart_yoy_comparison(crm), use_container_width=True)

    st.divider()

    st.markdown("#### Quick Reference Trends (Full Dataset)")
    tr1, tr2 = st.columns(2)

    with tr1:
        st.markdown("**Lead Volume — Trailing 6 Months**")
        df_mom = crm.copy()
        df_mom["month"] = df_mom["created_date"].dt.to_period("M").dt.to_timestamp()
        mom_data = df_mom.groupby("month").size().reset_index(name="leads").tail(6)
        fig_mom = px.bar(
            mom_data, x="month", y="leads",
            color_discrete_sequence=["#764ba2"],
            template="plotly_white",
            labels={"month": "Month", "leads": "Leads"},
        )
        st.plotly_chart(fig_mom, use_container_width=True)

    with tr2:
        st.markdown("**Ops Revenue by Service (All Time)**")
        svc_data = ops.groupby("service_type")["amount"].sum().reset_index()
        fig_svc = px.pie(
            svc_data, values="amount", names="service_type",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3,
            template="plotly_white",
        )
        st.plotly_chart(fig_svc, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — DATA QUALITY & DOCUMENTATION
# ═════════════════════════════════════════════════════════════════════════════

with tab_quality:
    st.subheader("Data Quality & Integrity Report")
    st.caption(f"Generated at load time: **{quality['load_time']}** — all data is static synthetic sample data.")

    dq_left, dq_right = st.columns(2)

    with dq_left:
        st.markdown("#### CRM — crm_leads.csv")
        crm_q = crm_quality_report(crm)
        for label, val in crm_q.items():
            if isinstance(val, dict):
                st.markdown(f"**{label}:**")
                st.json(val, expanded=False)
            else:
                st.markdown(f"- **{label}:** {val}")

        st.markdown("#### Join Quality (Ops → CRM)")
        join_q = join_quality_report(joined)
        for label, val in join_q.items():
            if isinstance(val, list):
                display = ", ".join(str(v) for v in val[:10])
                if len(val) > 10:
                    display += f" ... (+{len(val) - 10} more)"
                st.markdown(f"- **{label}:** {display if val else 'none'}")
            else:
                st.markdown(f"- **{label}:** {val}")

    with dq_right:
        st.markdown("#### Operations — ops_projects.json")
        ops_q = ops_quality_report(ops)
        for label, val in ops_q.items():
            if isinstance(val, dict):
                st.markdown(f"**{label}:**")
                st.json(val, expanded=False)
            else:
                st.markdown(f"- **{label}:** {val}")

        st.markdown("#### Targets Sheet — targets_sheet.csv")
        tgt_q = targets_quality_report(targets)
        for label, val in tgt_q.items():
            st.markdown(f"- **{label}:** {val}")

    st.divider()

    # PRD Section 4.1: Lightweight database demonstration
    st.subheader("💾 Lightweight Relational Database (SQLite: `data/intelligence.db`)")
    st.caption("Fulfilling PRD Section 4.1: In-memory tables are mirrored to an embedded SQLite database for relational joins and persistence.")

    sql_tab1, sql_tab2 = st.tabs(["Database Tables Status", "Live SQL Query Runner"])
    with sql_tab1:
        st.markdown("""
        The SQLite database stores the following normalized relational tables:
        - `crm_leads`: 200 records with parsed dates and numeric deal values
        - `ops_projects`: 150 records with SLA metrics and due dates
        - `targets_sheet`: 770 monthly target/forecast records
        - `sales_ops_joined`: Denormalized cross-source table linking CRM and Ops
        """)
        st.success(f"Database active at `{quality['sqlite_db']}`")

    with sql_tab2:
        default_query = "SELECT pipeline_stage, COUNT(*) AS lead_count, ROUND(SUM(deal_value), 2) AS total_val FROM crm_leads GROUP BY pipeline_stage"
        user_sql = st.text_area("Execute ad-hoc SQL query against SQLite:", value=default_query, height=80)
        if st.button("Run SQL Query"):
            try:
                sql_result = query_db(user_sql)
                st.dataframe(sql_result, use_container_width=True)
            except Exception as err:
                st.error(f"SQL Error: {err}")

    st.divider()

    # Data dictionary — inline so the evaluator doesn't need to open a separate file
    st.subheader("📖 Data Dictionary")
    st.markdown("""
**CRM Leads** (`data/crm_leads.csv`)

| Field | Type | Notes |
|---|---|---|
| `lead_id` | string | Primary key (CRM-XXXX) |
| `created_date` | date | Lead creation date |
| `source` | category | Referral / Website / LinkedIn / Cold Call etc. |
| `owner` | string | Assigned sales rep |
| `company` | string | **Join key to ops.client_id** |
| `region` | category | North / South / East / West / Central |
| `pipeline_stage` | category | New Lead → Qualified → Proposal Sent → Negotiation → Closed |
| `deal_value` | float USD | Blank for New Leads — expected domain rule, not a missing data error |
| `status` | category | Open / Won / Lost |
| `last_activity_date` | date | Most recent contact date |
| `account_segment` | category | Enterprise / Mid-Market / SMB |
| `days_since_activity` | int | Computed at load time relative to today |
| `stale_lead` | bool | True if days_since_activity > 14 |

**Operations Projects** (`data/ops_projects.json`)

| Field | Type | Notes |
|---|---|---|
| `project_id` | string | Primary key (OPS-XXXX) |
| `client_id` | string | **Join key to crm.company** |
| `status` | category | Open / In Progress / Completed / Overdue / On Hold |
| `service_type` | category | Translation / Localization / Transcription / Interpretation etc. |
| `created_date` | date | Project start |
| `due_date` | date | SLA deadline |
| `completed_date` | date | Actual completion (null if not done — expected) |
| `amount` | float USD | Project revenue |
| `assigned_team` | category | Team Alpha / Beta / Gamma / Delta |
| `sla_status` | category | Met / Breached / Pending |
| `is_overdue` | bool | Computed: due_date < today AND not Completed |

**Targets Sheet** (`data/targets_sheet.csv`)

| Field | Type | Notes |
|---|---|---|
| `month` | date YYYY-MM | Monthly planning row |
| `owner` | string | Sales rep |
| `region` | category | Sales region |
| `account_segment` | category | Enterprise / Mid-Market / SMB |
| `campaign` | string | Marketing campaign |
| `target_revenue` | float USD | Monthly revenue target |
| `forecast_revenue` | float USD | Forecasted revenue |

**Join strategy**

- Key: `ops.client_id = crm.company` (exact name match)
- Type: left outer join — all ops projects are kept
- Unmatched ops rows get `crm_matched = False` and are shown in red on the combined chart
- Production note: stable UUID foreign keys should replace name matching
- Double-counting: aggregations always use a single source table; the joined view is for display only
""")

    st.divider()

    st.subheader("📐 KPI Definitions")
    st.markdown("""
| KPI | Formula | Source | Caveat |
|---|---|---|---|
| Total Leads | COUNT(*) in filtered CRM | CRM | Respects all active filters |
| Open Pipeline (USD) | SUM(deal_value) WHERE status = Open | CRM | Excludes rows with no deal value |
| Win Rate | Won / (Won + Lost) × 100 | CRM | Closed stages only |
| Avg Open Deal | AVG(deal_value) WHERE status = Open | CRM | |
| Stale Lead | days_since_activity > 14 | CRM | Computed at load time |
| Overdue Project | due_date < today AND status != Completed | Ops | |
| SLA Breach Rate | Breached / Completed × 100 | Ops | Completed projects only |
| Ops Revenue | SUM(amount) | Ops | USD only |
| Target vs Actual | Won deal_value vs target_revenue by month+owner | CRM + Sheet | Joined on month and owner |
""")

    st.divider()

    st.subheader("Raw Data Preview")
    choice = st.selectbox("Dataset to preview:", ["CRM Leads", "Operations Projects", "Targets Sheet", "Joined Sales-to-Ops"])
    preview_map = {
        "CRM Leads":             crm,
        "Operations Projects":   ops,
        "Targets Sheet":         targets,
        "Joined Sales-to-Ops":   joined,
    }
    st.dataframe(preview_map[choice].head(50), use_container_width=True)
