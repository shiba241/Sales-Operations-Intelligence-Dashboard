# charts.py
# Plotly chart builders for the Sales and Operations dashboards.
# Each function takes a filtered DataFrame and returns a Plotly figure.
# Charts are intentionally kept simple - clear > clever.

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

TEMPLATE = "plotly_white"

# Consistent colour palette across all charts
COLOURS = px.colors.qualitative.Plotly

# Status colours used in the ops charts (kept consistent with the SLA pie)
STATUS_COLOUR_MAP = {
    "Completed":   "#2ECC71",
    "In Progress": "#3498DB",
    "Open":        "#F39C12",
    "Overdue":     "#E74C3C",
    "On Hold":     "#95A5A6",
}


def _empty_fig(message: str) -> go.Figure:
    """Return a blank figure with a centred message - used when filtered data is empty."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#888")
    )
    fig.update_layout(template=TEMPLATE, xaxis_visible=False, yaxis_visible=False)
    return fig


# ── Sales charts ──────────────────────────────────────────────────────────────

def chart_leads_over_time(crm: pd.DataFrame) -> go.Figure:
    if crm.empty:
        return _empty_fig("No leads in selected date range")

    df = crm.copy()
    df["month"] = df["created_date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("month").size().reset_index(name="leads")

    fig = px.line(
        monthly, x="month", y="leads",
        markers=True,
        title="Leads Created Over Time (Monthly)",
        labels={"month": "Month", "leads": "Leads"},
        template=TEMPLATE,
        color_discrete_sequence=COLOURS,
    )
    fig.update_layout(hovermode="x unified")
    return fig


def chart_leads_by_source(crm: pd.DataFrame) -> go.Figure:
    if crm.empty:
        return _empty_fig("No data")

    counts = crm["source"].value_counts().reset_index()
    counts.columns = ["source", "count"]

    fig = px.bar(
        counts, x="count", y="source",
        orientation="h",
        title="Leads by Source",
        labels={"count": "Leads", "source": "Source"},
        template=TEMPLATE,
        color="source",
        color_discrete_sequence=COLOURS,
    )
    fig.update_layout(showlegend=False)
    return fig


def chart_leads_by_stage(crm: pd.DataFrame) -> go.Figure:
    stage_order = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]

    if crm.empty:
        return _empty_fig("No data")

    counts = (
        crm["pipeline_stage"]
        .value_counts()
        .reindex(stage_order, fill_value=0)
        .reset_index()
    )
    counts.columns = ["stage", "count"]

    fig = px.funnel(
        counts, x="count", y="stage",
        title="Pipeline Funnel by Stage",
        labels={"count": "Leads", "stage": "Stage"},
        template=TEMPLATE,
    )
    return fig


def chart_leads_by_region(crm: pd.DataFrame) -> go.Figure:
    if crm.empty:
        return _empty_fig("No data")

    counts = crm.groupby("region").size().reset_index(name="leads")
    fig = px.pie(
        counts, values="leads", names="region",
        title="Leads by Region",
        template=TEMPLATE,
        color_discrete_sequence=COLOURS,
        hole=0.4,
    )
    return fig


def chart_pipeline_value_by_owner(crm: pd.DataFrame) -> go.Figure:
    open_deals = crm[(crm["status"] == "Open") & (crm["deal_value"].notna())]
    if open_deals.empty:
        return _empty_fig("No open pipeline data for current filters")

    by_owner = (
        open_deals.groupby("owner")["deal_value"]
        .sum()
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        by_owner, x="deal_value", y="owner",
        orientation="h",
        title="Open Pipeline Value by Owner (USD)",
        labels={"deal_value": "Pipeline Value (USD)", "owner": "Owner"},
        template=TEMPLATE,
        color="owner",
        color_discrete_sequence=COLOURS,
    )
    fig.update_layout(showlegend=False)
    return fig


def chart_stale_leads(crm: pd.DataFrame) -> go.Figure:
    if crm.empty:
        return _empty_fig("No data")

    # Count stale leads per owner (stale_lead is a bool column)
    stale_counts = (
        crm[crm["stale_lead"]]
        .groupby("owner")
        .size()
        .sort_values(ascending=False)
        .reset_index(name="stale_count")
    )

    if stale_counts.empty:
        return _empty_fig("No stale leads in current filters")

    fig = px.bar(
        stale_counts, x="owner", y="stale_count",
        title=f"Stale Leads by Owner (No Activity > 14 Days)",
        labels={"stale_count": "Stale Leads", "owner": "Owner"},
        template=TEMPLATE,
        color="stale_count",
        color_continuous_scale="Reds",
    )
    fig.update_layout(coloraxis_showscale=False)
    return fig


# ── Operations charts ──────────────────────────────────────────────────────────

def chart_projects_by_status(ops: pd.DataFrame) -> go.Figure:
    if ops.empty:
        return _empty_fig("No projects in selected filters")

    counts = ops["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]

    # Apply consistent status colours where possible
    colours = [STATUS_COLOUR_MAP.get(s, "#BDC3C7") for s in counts["status"]]

    fig = px.bar(
        counts, x="status", y="count",
        title="Projects by Status",
        labels={"count": "Projects", "status": "Status"},
        template=TEMPLATE,
        color="status",
        color_discrete_map=STATUS_COLOUR_MAP,
    )
    fig.update_layout(showlegend=False)
    return fig


def chart_projects_over_time(ops: pd.DataFrame) -> go.Figure:
    if ops.empty:
        return _empty_fig("No projects in selected filters")

    df = ops.copy()
    df["month"] = df["created_date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby(["month", "status"]).size().reset_index(name="count")

    fig = px.bar(
        monthly, x="month", y="count", color="status",
        title="Projects Created Over Time (by Status)",
        labels={"month": "Month", "count": "Projects"},
        template=TEMPLATE,
        color_discrete_map=STATUS_COLOUR_MAP,
    )
    return fig


def chart_workload_by_team(ops: pd.DataFrame) -> go.Figure:
    active = ops[ops["status"].isin(["Open", "In Progress"])]
    if active.empty:
        return _empty_fig("No active projects in current filters")

    by_team = (
        active.groupby("assigned_team")
        .size()
        .reset_index(name="open_projects")
    )

    fig = px.bar(
        by_team, x="assigned_team", y="open_projects",
        title="Active Workload by Team",
        labels={"open_projects": "Open Projects", "assigned_team": "Team"},
        template=TEMPLATE,
        color="assigned_team",
        color_discrete_sequence=COLOURS,
    )
    fig.update_layout(showlegend=False)
    return fig


def chart_workload_by_service(ops: pd.DataFrame) -> go.Figure:
    if ops.empty:
        return _empty_fig("No data")

    by_service = (
        ops.groupby("service_type")["amount"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        by_service, x="service_type", y="amount",
        title="Total Revenue by Service Type (USD)",
        labels={"amount": "Revenue (USD)", "service_type": "Service"},
        template=TEMPLATE,
        color="service_type",
        color_discrete_sequence=COLOURS,
    )
    fig.update_layout(showlegend=False)
    return fig


def chart_sla_compliance(ops: pd.DataFrame) -> go.Figure:
    completed = ops[ops["status"] == "Completed"]
    if completed.empty:
        return _empty_fig("No completed projects in current filters")

    sla_counts = completed["sla_status"].value_counts().reset_index()
    sla_counts.columns = ["sla_status", "count"]

    sla_colours = {"Met": "#2ECC71", "Breached": "#E74C3C", "Pending": "#F39C12"}

    fig = px.pie(
        sla_counts, values="count", names="sla_status",
        title="SLA Compliance (Completed Projects)",
        template=TEMPLATE,
        color="sla_status",
        color_discrete_map=sla_colours,
        hole=0.4,
    )
    return fig


def chart_targets_vs_actuals(crm: pd.DataFrame, targets: pd.DataFrame) -> go.Figure:
    if crm.empty or targets.empty:
        return _empty_fig("Insufficient data for target comparison")

    df = crm.copy()
    df["month"] = df["created_date"].dt.to_period("M").dt.to_timestamp()

    actuals = (
        df[df["status"] == "Won"]
        .groupby("month")["deal_value"]
        .sum()
        .reset_index(name="actual")
    )
    target_monthly = (
        targets.groupby("month")["target_revenue"]
        .sum()
        .reset_index(name="target")
    )

    merged = actuals.merge(target_monthly, on="month", how="outer").sort_values("month")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=merged["month"], y=merged["target"],
        name="Target",
        line=dict(color="#3498DB", dash="dash"),
        mode="lines+markers",
    ))
    fig.add_trace(go.Scatter(
        x=merged["month"], y=merged["actual"],
        name="Actual (Won Revenue)",
        line=dict(color="#2ECC71"),
        mode="lines+markers",
    ))
    fig.update_layout(
        title="Target vs Actual Revenue (Monthly)",
        xaxis_title="Month",
        yaxis_title="Revenue (USD)",
        template=TEMPLATE,
        hovermode="x unified",
    )
    return fig


def chart_sales_to_ops(joined: pd.DataFrame) -> go.Figure:
    """Show top clients by ops revenue, coloured by whether they matched a CRM account."""
    if joined.empty:
        return _empty_fig("No joined data available")

    df = joined.copy()
    df["match_label"] = df["crm_matched"].map({True: "Matched to CRM", False: "No CRM Match"})

    by_client = (
        df.groupby(["client_id", "match_label"])["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
        .head(20)
    )

    fig = px.bar(
        by_client, x="client_id", y="amount", color="match_label",
        title="Top 20 Clients by Ops Revenue (CRM Match Status)",
        labels={"amount": "Ops Revenue (USD)", "client_id": "Client"},
        template=TEMPLATE,
        color_discrete_map={"Matched to CRM": "#2ECC71", "No CRM Match": "#E74C3C"},
    )
    fig.update_xaxes(tickangle=45)
    return fig
