# data_loader.py
# Handles loading, normalising, and joining the three synthetic datasets.
# Each source keeps its own DataFrame - they're only joined when explicitly needed.

import os
import json
import pandas as pd
from datetime import datetime, date

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

STALE_THRESHOLD_DAYS = 14  # leads with no activity beyond this are flagged as stale


def _coerce_dates(df, columns):
    """Parse date strings to datetime, silently coercing bad values to NaT."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _coerce_numeric(df, columns):
    """Parse string columns to float, silently coercing bad values to NaN."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_crm() -> pd.DataFrame:
    """
    Load CRM leads from crm_leads.csv.
    Normalises column names, dates, numeric fields, and derives stale-lead flag.
    Missing deal_value is expected for New Leads (not a data error).
    """
    path = os.path.join(DATA_DIR, "crm_leads.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()

    df = _coerce_dates(df, ["created_date", "last_activity_date"])
    df = _coerce_numeric(df, ["deal_value"])

    # Trim whitespace on all string-ish columns
    for col in ["source", "owner", "company", "region", "pipeline_stage", "status", "account_segment"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    # Stale-lead flag: computed relative to today at load time.
    # Note: Streamlit caches this result, so "today" is fixed until the cache
    # expires or the user clicks Refresh Data.
    today = pd.Timestamp(date.today())
    df["days_since_activity"] = (today - df["last_activity_date"]).dt.days
    df["stale_lead"] = df["days_since_activity"] > STALE_THRESHOLD_DAYS

    return df


def load_ops() -> pd.DataFrame:
    """
    Load operations projects from ops_projects.json.
    Flags projects as overdue if the due date has passed and they aren't completed.
    completed_date being null for non-completed rows is expected, not missing data.
    """
    path = os.path.join(DATA_DIR, "ops_projects.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    df = pd.DataFrame(raw)
    df = _coerce_dates(df, ["created_date", "due_date", "completed_date"])
    df = _coerce_numeric(df, ["amount", "sla_days"])

    for col in ["status", "service_type", "assigned_team", "sla_status"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    today = pd.Timestamp(date.today())
    df["is_overdue"] = (df["due_date"] < today) & (~df["status"].isin(["Completed"]))

    return df


def load_targets() -> pd.DataFrame:
    """
    Load the targets/forecast sheet from targets_sheet.csv.
    This simulates a Google Sheets CSV export with monthly planning data.
    Month is parsed as first-of-month timestamp for easy date filtering.
    """
    path = os.path.join(DATA_DIR, "targets_sheet.csv")
    df = pd.read_csv(path, dtype=str)
    df.columns = df.columns.str.strip().str.lower()

    df = _coerce_numeric(df, ["target_revenue", "forecast_revenue"])
    df["month"] = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")

    for col in ["owner", "region", "account_segment", "campaign"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    return df


def build_joined(crm: pd.DataFrame, ops: pd.DataFrame) -> pd.DataFrame:
    """
    Left-join ops projects to CRM accounts using company name as the bridge key.

    Join key: ops.client_id == crm.company (exact string match)

    Assumption: In this prototype, company names are consistent across both
    systems. Production should use stable UUID foreign keys instead.

    All ops rows are kept. Unmatched rows (no CRM company found) get NaN for
    the CRM fields and crm_matched=False, which surfaces them in the quality tab.
    """
    # Build a deduplicated lookup: one row per unique CRM company
    crm_lookup = (
        crm[["company", "owner", "region", "account_segment"]]
        .drop_duplicates(subset=["company"])
        .rename(columns={"company": "client_id"})
    )

    joined = ops.merge(crm_lookup, on="client_id", how="left", suffixes=("", "_crm"))
    joined["crm_matched"] = joined["owner"].notna()
    return joined


def load_all():
    """
    Load all three sources, build the joined view, and return a quality summary dict.
    Called once per Streamlit session (cached). Use the Refresh button to reload.

    Returns: crm, ops, targets, joined DataFrames + quality dict
    """
    crm = load_crm()
    ops = load_ops()
    targets = load_targets()
    joined = build_joined(crm, ops)

    quality = {
        "crm_total":             len(crm),
        "crm_missing_deal_val":  int(crm["deal_value"].isna().sum()),
        "crm_stale_leads":       int(crm["stale_lead"].sum()),
        "ops_total":             len(ops),
        "ops_overdue":           int(ops["is_overdue"].sum()),
        "ops_missing_completed": int(ops["completed_date"].isna().sum()),
        "joined_matched":        int(joined["crm_matched"].sum()),
        "joined_unmatched":      int((~joined["crm_matched"]).sum()),
        "targets_total":         len(targets),
        "load_time":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return crm, ops, targets, joined, quality
