# insights.py
# Rule-based analytical insights - no LLM involved.
# Each function checks one condition and returns a small dict, or None if not applicable.
# The dict shape is always: {title, severity, detail, recommendation}
# severity is one of: "warning", "success", "info"

import pandas as pd


STALE_THRESHOLD = 14       # days - matches data_loader
PIPELINE_CONCENTRATION_PCT = 40   # warn if one owner holds more than this % of pipeline
OVERDUE_RATE_THRESHOLD = 15       # warn if overdue projects exceed this % of active work
SLA_BREACH_THRESHOLD = 10         # warn if breach rate exceeds this % of completed projects
WIN_RATE_TARGET = 40              # below this % is considered underperforming


def _pct_change(new_val, old_val):
    """Simple month-over-month % change. Returns None if division by zero."""
    if not old_val:
        return None
    return round((new_val - old_val) / old_val * 100, 1)


# --- Sales insights ---

def insight_lead_volume_trend(crm: pd.DataFrame):
    """Flag if lead volume dropped or spiked significantly month-over-month."""
    df = crm.copy()
    df["month"] = df["created_date"].dt.to_period("M")
    monthly = df.groupby("month").size().sort_index()

    if len(monthly) < 2:
        return None

    last_count = int(monthly.iloc[-1])
    prev_count = int(monthly.iloc[-2])
    change = _pct_change(last_count, prev_count)

    if change is None:
        return None

    if change < -20:
        severity = "warning"
        rec = "Lead volume has dropped sharply. Check top-of-funnel activity and campaign spend."
    elif change > 20:
        severity = "success"
        rec = "Strong lead growth this month. Make sure follow-up capacity can keep pace."
    else:
        severity = "info"
        rec = "Lead volume is stable month-over-month."

    sign = "+" if change >= 0 else ""
    detail = (
        f"Leads in {monthly.index[-1]}: **{last_count}** "
        f"(vs {prev_count} last month, {sign}{change}%)"
    )
    return {"title": "Lead Volume Trend", "severity": severity, "detail": detail, "recommendation": rec}


def insight_pipeline_concentration(crm: pd.DataFrame):
    """Warn if one sales rep is holding a disproportionate share of open pipeline."""
    open_deals = crm[(crm["status"] == "Open") & (crm["deal_value"].notna())]
    if open_deals.empty:
        return None

    total_value = open_deals["deal_value"].sum()
    by_owner = open_deals.groupby("owner")["deal_value"].sum()
    top_owner = by_owner.idxmax()
    top_value = by_owner.max()
    top_share = top_value / total_value * 100

    severity = "warning" if top_share > PIPELINE_CONCENTRATION_PCT else "info"
    detail = (
        f"**{top_owner}** holds {top_share:.1f}% of open pipeline value "
        f"(${top_value:,.0f} of ${total_value:,.0f} total)."
    )

    if top_share > PIPELINE_CONCENTRATION_PCT:
        rec = "High concentration risk — consider redistributing leads or ensuring backup coverage."
    else:
        rec = "Pipeline is reasonably distributed across the team."

    return {"title": "Pipeline Concentration", "severity": severity, "detail": detail, "recommendation": rec}


def insight_stale_leads(crm: pd.DataFrame):
    """Report stale leads and which rep has the most."""
    stale = crm[crm["stale_lead"]]
    if stale.empty:
        return None

    count = len(stale)
    stale_by_owner = stale.groupby("owner").size()
    worst_owner = stale_by_owner.idxmax()
    worst_count = int(stale_by_owner.max())

    severity = "warning" if count > 20 else "info"
    detail = (
        f"**{count}** leads have had no activity in over {STALE_THRESHOLD} days. "
        f"Most stale: **{worst_owner}** ({worst_count} leads)."
    )
    rec = "Schedule follow-up calls. Prioritise high-value deals that have gone quiet."

    return {"title": f"Stale Leads (No Activity > {STALE_THRESHOLD} Days)", "severity": severity, "detail": detail, "recommendation": rec}


def insight_stage_conversion(crm: pd.DataFrame):
    """Report overall win rate among closed opportunities."""
    closed = crm[crm["pipeline_stage"].isin(["Closed Won", "Closed Lost"])]
    if closed.empty:
        return None

    won = int((closed["pipeline_stage"] == "Closed Won").sum())
    lost = int((closed["pipeline_stage"] == "Closed Lost").sum())
    total_closed = won + lost

    if total_closed == 0:
        return None

    win_rate = round(won / total_closed * 100, 1)
    severity = "success" if win_rate >= WIN_RATE_TARGET else "warning"
    detail = f"Win rate: **{win_rate}%** ({won} won, {lost} lost out of {total_closed} closed)."

    if win_rate >= WIN_RATE_TARGET:
        rec = "Win rate is healthy."
    else:
        rec = f"Win rate is below {WIN_RATE_TARGET}%. Worth reviewing proposal quality and negotiation-stage drop-offs."

    return {"title": "Stage Conversion (Win Rate)", "severity": severity, "detail": detail, "recommendation": rec}


# --- Operations insights ---

def insight_overdue_spike(ops: pd.DataFrame):
    """Warn if the proportion of overdue projects is getting high."""
    active = ops[ops["status"].isin(["Open", "In Progress", "Overdue"])]
    if active.empty:
        return None

    overdue_count = int(ops["is_overdue"].sum())
    overdue_pct = overdue_count / len(active) * 100
    severity = "warning" if overdue_pct > OVERDUE_RATE_THRESHOLD else "info"

    detail = (
        f"**{overdue_count}** of {len(active)} active projects are overdue "
        f"({overdue_pct:.1f}%)."
    )

    if overdue_pct > OVERDUE_RATE_THRESHOLD:
        rec = "Overdue rate is elevated. Review team capacity and see if any deliverables need rescheduling."
    else:
        rec = "Overdue rate is within an acceptable range."

    return {"title": "Overdue Project Rate", "severity": severity, "detail": detail, "recommendation": rec}


def insight_sla_breaches(ops: pd.DataFrame):
    """Report how many completed projects breached their SLA."""
    completed = ops[ops["status"] == "Completed"]
    if completed.empty:
        return None

    breached = int((completed["sla_status"] == "Breached").sum())
    rate = breached / len(completed) * 100
    severity = "warning" if rate > SLA_BREACH_THRESHOLD else "success"

    detail = f"**{breached}** of {len(completed)} completed projects breached SLA ({rate:.1f}%)."

    if rate <= SLA_BREACH_THRESHOLD:
        rec = "SLA performance looks good."
    else:
        rec = "SLA breach rate is above target. Worth breaking down by team and service type to find the cause."

    return {"title": "SLA Breach Rate (Completed Projects)", "severity": severity, "detail": detail, "recommendation": rec}


def insight_target_vs_actual(crm: pd.DataFrame, targets: pd.DataFrame):
    """Compare closed-won revenue against the monthly target for the latest shared month."""
    df = crm.copy()
    df["month"] = df["created_date"].dt.to_period("M").dt.to_timestamp()

    actuals = (
        df[df["status"] == "Won"]
        .groupby("month")["deal_value"]
        .sum()
        .reset_index(name="actual")
    )

    if actuals.empty:
        return None

    monthly_targets = targets.groupby("month")["target_revenue"].sum().reset_index(name="target")
    merged = actuals.merge(monthly_targets, on="month", how="inner").sort_values("month")

    if merged.empty:
        return None

    latest = merged.iloc[-1]
    gap_pct = _pct_change(latest["actual"], latest["target"])

    if gap_pct is None:
        return None

    month_label = latest["month"].strftime("%Y-%m")
    sign = "+" if gap_pct >= 0 else ""
    severity = "warning" if gap_pct < -20 else ("success" if gap_pct >= 0 else "info")

    detail = (
        f"Latest month ({month_label}): "
        f"Actual ${latest['actual']:,.0f} vs Target ${latest['target']:,.0f} "
        f"({sign}{gap_pct}%)"
    )
    rec = "On track!" if gap_pct >= 0 else "Below target. Review the pipeline and look at deals that could close this month."

    return {"title": "Revenue: Target vs Actual", "severity": severity, "detail": detail, "recommendation": rec}


# --- Runner ---

def get_all_insights(crm: pd.DataFrame, ops: pd.DataFrame, targets: pd.DataFrame) -> list:
    """
    Run all insight checks and return a list of applicable results.
    Each check is paired explicitly with its required DataFrame(s).
    Errors in individual checks are isolated so one failure doesn't suppress the rest.
    """
    # Pair each single-source insight with its DataFrame directly — no guessing from names
    single_source_checks = [
        (insight_lead_volume_trend,      crm),
        (insight_pipeline_concentration, crm),
        (insight_stale_leads,            crm),
        (insight_stage_conversion,       crm),
        (insight_overdue_spike,          ops),
        (insight_sla_breaches,           ops),
    ]

    results = []

    for fn, df in single_source_checks:
        try:
            result = fn(df)
            if result:
                results.append(result)
        except Exception as e:
            results.append({
                "title": f"Insight error: {fn.__name__}",
                "severity": "info",
                "detail": str(e),
                "recommendation": "Check the data for this metric.",
            })

    # target_vs_actual joins CRM won revenue against the targets sheet
    try:
        result = insight_target_vs_actual(crm, targets)
        if result:
            results.append(result)
    except Exception as e:
        results.append({
            "title": "Target vs Actual error",
            "severity": "info",
            "detail": str(e),
            "recommendation": "",
        })

    return results
