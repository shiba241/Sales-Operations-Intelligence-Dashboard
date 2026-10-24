# app.py
# Sales & Operations Intelligence Dashboard
# Braahmam International Limited — Interview Prototype (synthetic data only)
#
# Structure:
#   Sidebar  → global filters (date, region, owner, stage, ops status)
#   Tab 1    → Sales dashboard  (KPIs + charts)
#   Tab 2    → Operations dashboard (KPIs + charts + combined sales-ops view)
#   Tab 3    → Analytical insights (rule-based flags)
#   Tab 4    → Data quality report + data dictionary

import os
import sys

# Make sure the src package resolves when running from any working directory
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import (
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
    chart_targets_vs_actuals,
    chart_workload_by_service,
    chart_workload_by_team,
)
from src.data_loader import load_all
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

# Minimal CSS — just the insight cards and a slightly tighter tab look.
# Keeping this small so it's easy to rip out or swap for a theme later.
st.markdown("""
<style>
    .insight-warning { background:#fff3cd; border-left:4px solid #ffc107; padding:12px 16px; border-radius:6px; margin:6px 0; }
    .insight-success { background:#d4edda; border-left:4px solid #28a745; padding:12px 16px; border-radius:6px; margin:6px 0; }
    .insight-info    { background:#d1ecf1; border-left:4px solid #17a2b8; padding:12px 16px; border-radius:6px; margin:6px 0; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_data():
    """Cache the loaded data for 5 minutes. Clear it with the Refresh button."""
    return load_all()


with st.spinner("Loading data..."):
    crm, ops, targets, joined, quality = get_data()


# ── Sidebar filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📊 Sales & Ops Dashboard")
    st.markdown("*Braahmam International Limited*")
    st.divider()

    st.markdown("### Filters")

    # Date range — defaults to the full span of CRM data
    min_date = crm["created_date"].min().date()
    max_date = crm["created_date"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Guard against a half-selected range (user picks start but not end yet)
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

    st.caption(f"Data loaded: **{quality['load_time']}**")
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

# The joined view follows ops date/status filter so the combined chart stays consistent
joined_f = joined[
    (joined["created_date"] >= d_start) &
    (joined["created_date"] <= d_end) &
    (joined["status"].isin(sel_ops_statuses))
].copy()


# ── Page header ───────────────────────────────────────────────────────────────

st.title("📊 Sales & Operations Intelligence Dashboard")
st.caption(
    f"Showing **{len(crm_f):,} leads** and **{len(ops_f):,} projects** for the selected filters  |  "
    f"Sources: CRM (CSV) · Operations (JSON) · Targets Sheet (CSV)  |  "
    f"Loaded: {quality['load_time']}  |  Synthetic data only"
)


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_sales, tab_ops, tab_insights, tab_quality = st.tabs([
    "🏆 Sales Dashboard",
    "⚙️ Operations Dashboard",
    "🤖 Insights",
    "🔍 Data Quality & Docs",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — SALES DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

with tab_sales:

    # Calculate the KPIs up front so the numbers and the charts use the same base
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
        st.plotly_chart(chart_leads_by_source(crm_f), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(chart_leads_by_stage(crm_f), use_container_width=True)
    with c4:
        st.plotly_chart(chart_leads_by_region(crm_f), use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        st.plotly_chart(chart_pipeline_value_by_owner(crm_f), use_container_width=True)
    with c6:
        st.plotly_chart(chart_stale_leads(crm_f), use_container_width=True)

    # Drilldown table for stale leads — lets a manager see exactly which ones need attention
    st.subheader("Stale Leads Detail (No Activity > 14 Days)")
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
    o2.metric("Active",             f"{op_active:,}")
    o3.metric("Overdue",            f"{op_overdue:,}", delta=f"-{op_overdue}", delta_color="inverse")
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
        st.plotly_chart(chart_workload_by_service(ops_f), use_container_width=True)

    p5, p6 = st.columns(2)
    with p5:
        st.plotly_chart(chart_sla_compliance(ops_f), use_container_width=True)
    with p6:
        st.plotly_chart(chart_targets_vs_actuals(crm_f, targets_f), use_container_width=True)

    # Combined Sales-to-Ops view
    # -----------------------------------------------------------------------
    # Join key: ops.client_id matched to crm.company by exact name.
    # Not all ops clients appear in the CRM - those are shown in red.
    # See the Data Quality tab for the full list of unmatched clients.
    st.subheader("Combined Sales-to-Operations View")
    st.info(
        f"Join key: **ops.client_id = crm.company** (exact name match). "
        f"**{quality['joined_matched']}** of **{quality['ops_total']}** ops projects "
        f"matched to a CRM account. "
        f"**{quality['joined_unmatched']}** are unmatched "
        f"(see Data Quality tab for details)."
    )
    st.plotly_chart(chart_sales_to_ops(joined_f), use_container_width=True)

    # Target vs Actuals breakdown table
    st.subheader("Targets vs Actuals — Owner Detail")
    crm_won = crm_f[crm_f["status"] == "Won"].copy()
    crm_won["month"] = crm_won["created_date"].dt.to_period("M").dt.to_timestamp()
    actuals = crm_won.groupby(["month", "owner"])["deal_value"].sum().reset_index(name="actual_revenue")
    tgt     = targets_f.groupby(["month", "owner"])["target_revenue"].sum().reset_index()

    tva = actuals.merge(tgt, on=["month", "owner"], how="outer").sort_values(["month", "owner"])
    tva["gap_usd"] = tva["actual_revenue"] - tva["target_revenue"]
    tva["gap_pct"] = (tva["gap_usd"] / tva["target_revenue"] * 100).round(1)

    if tva.empty:
        st.info("No matching data between won deals and targets for the selected filters.")
    else:
        st.dataframe(tva, use_container_width=True, height=300)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — INSIGHTS
# ═════════════════════════════════════════════════════════════════════════════

with tab_insights:
    st.subheader("Analytical Insights")
    st.markdown(
        "These insights are generated by rules applied to the filtered data — no LLM involved. "
        "Each one is tied to a specific metric. Observed facts and recommendations are kept separate."
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

    # Quick reference charts that always show the full dataset (not filtered)
    # so managers can see the bigger picture alongside the filtered insights
    st.markdown("#### Quick Reference (Full Dataset)")
    tr1, tr2 = st.columns(2)

    with tr1:
        st.markdown("**Lead Volume — Last 6 Months**")
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
    st.subheader("Data Quality Report")
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

    # Data dictionary — inline so the evaluator doesn't need to open a separate file
    st.subheader("Data Dictionary")
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
| `deal_value` | float USD | Blank for New Leads — not a data error |
| `status` | category | Open / Won / Lost |
| `last_activity_date` | date | Most recent contact |
| `account_segment` | category | Enterprise / Mid-Market / SMB |
| `days_since_activity` | int | Computed at load time |
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

    st.subheader("KPI Definitions")
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
    choice = st.selectbox("Dataset", ["CRM Leads", "Operations Projects", "Targets Sheet"])
    preview_map = {
        "CRM Leads":           crm,
        "Operations Projects": ops,
        "Targets Sheet":       targets,
    }
    st.dataframe(preview_map[choice].head(50), use_container_width=True)
