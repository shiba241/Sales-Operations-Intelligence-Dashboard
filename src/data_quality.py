# data_quality.py
# Produces per-source quality summaries used in the Data Quality tab.
# These are intentionally simple counts - the goal is transparency, not perfection.

import pandas as pd


def crm_quality_report(crm: pd.DataFrame) -> dict:
    return {
        "Total Leads":            len(crm),
        "Missing Deal Value":     int(crm["deal_value"].isna().sum()),
        "Missing Last Activity":  int(crm["last_activity_date"].isna().sum()),
        "Duplicate Lead IDs":     int(crm.duplicated(subset=["lead_id"]).sum()),
        "Stale Leads (>14 days)": int(crm["stale_lead"].sum()),
        "Status Breakdown":       crm["status"].value_counts().to_dict(),
        "Pipeline Stage Counts":  crm["pipeline_stage"].value_counts().to_dict(),
    }


def ops_quality_report(ops: pd.DataFrame) -> dict:
    return {
        "Total Projects":         len(ops),
        "Overdue Projects":       int(ops["is_overdue"].sum()),
        # completed_date is null for anything not yet done - expected, not missing data
        "Not Yet Completed":      int(ops["completed_date"].isna().sum()),
        "Duplicate Project IDs":  int(ops.duplicated(subset=["project_id"]).sum()),
        "SLA Status Breakdown":   ops["sla_status"].value_counts().to_dict(),
        "Status Breakdown":       ops["status"].value_counts().to_dict(),
    }


def targets_quality_report(targets: pd.DataFrame) -> dict:
    min_month = targets["month"].min().strftime("%Y-%m")
    max_month = targets["month"].max().strftime("%Y-%m")
    return {
        "Total Rows":              len(targets),
        "Missing Target Revenue":  int(targets["target_revenue"].isna().sum()),
        "Missing Forecast Revenue":int(targets["forecast_revenue"].isna().sum()),
        "Month Range":             f"{min_month} to {max_month}",
    }


def join_quality_report(joined: pd.DataFrame) -> dict:
    matched = int(joined["crm_matched"].sum())
    unmatched = int((~joined["crm_matched"]).sum())
    match_rate = f"{matched / len(joined) * 100:.1f}%" if len(joined) > 0 else "N/A"

    # List unmatched client IDs so they're visible and actionable
    unmatched_clients = (
        joined.loc[~joined["crm_matched"], "client_id"]
        .dropna()
        .unique()
        .tolist()
    )

    return {
        "Ops Rows Matched to CRM": matched,
        "Ops Rows Unmatched":      unmatched,
        "Match Rate":              match_rate,
        "Unmatched Client IDs":    unmatched_clients,
    }
