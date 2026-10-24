# test_all.py
# Basic smoke tests for the dashboard backend.
# Not a full test suite — just enough to catch obvious breakage before running the app.
# Run: python test_all.py

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

PASS = []
FAIL = []


def check(label, fn):
    try:
        result = fn()
        PASS.append(label)
        return result
    except Exception:
        FAIL.append(label)
        print(f"\n  [FAIL] {label}")
        traceback.print_exc()
        return None


# ── Data loading ──────────────────────────────────────────────────────────────

from src.data_loader import load_all, load_crm, load_ops, load_targets, build_joined, query_db

crm      = check("load_crm()",     load_crm)
ops      = check("load_ops()",     load_ops)
targets  = check("load_targets()", load_targets)

def _build_joined():
    return build_joined(crm, ops)

joined   = check("build_joined()", _build_joined)

def _load_all():
    c, o, t, j, q = load_all()
    assert len(c) > 0,   "CRM DataFrame is empty"
    assert len(o) > 0,   "Ops DataFrame is empty"
    assert len(t) > 0,   "Targets DataFrame is empty"
    assert len(j) > 0,   "Joined DataFrame is empty"
    assert "load_time" in q
    assert "sqlite_db" in q
    return c, o, t, j, q

all_data = check("load_all() + quality dict", _load_all)
if all_data:
    crm, ops, targets, joined, quality = all_data

def _sqlite_test():
    res = query_db("SELECT COUNT(*) AS total FROM crm_leads")
    assert res.iloc[0]["total"] == len(crm), "SQLite lead count mismatch"
    return res

check("SQLite intelligence.db query", _sqlite_test)

# ── Derived columns ───────────────────────────────────────────────────────────

def _crm_derived():
    assert "stale_lead" in crm.columns,           "Missing stale_lead column"
    assert "days_since_activity" in crm.columns,  "Missing days_since_activity column"
    assert crm["deal_value"].dtype.kind == "f",   "deal_value should be float"

def _ops_derived():
    assert "is_overdue" in ops.columns,           "Missing is_overdue column"
    assert ops["amount"].dtype.kind == "f",       "amount should be float"

def _join_quality():
    assert "crm_matched" in joined.columns,       "Missing crm_matched column"
    matched   = joined["crm_matched"].sum()
    unmatched = (~joined["crm_matched"]).sum()
    assert matched + unmatched == len(joined),    "matched + unmatched != total rows"
    assert unmatched > 0,                          "Expected some unmatched ops rows (3 ops-only clients)"

check("CRM derived columns",  _crm_derived)
check("Ops derived columns",  _ops_derived)
check("Join quality checks",  _join_quality)

# ── Data quality reports ──────────────────────────────────────────────────────

from src.data_quality import (
    crm_quality_report, ops_quality_report,
    targets_quality_report, join_quality_report,
)

def _dq_crm():
    r = crm_quality_report(crm)
    assert "Total Leads" in r
    assert r["Total Leads"] == len(crm)

def _dq_ops():
    r = ops_quality_report(ops)
    assert "Total Projects" in r

def _dq_targets():
    r = targets_quality_report(targets)
    assert "Month Range" in r

def _dq_join():
    r = join_quality_report(joined)
    assert "Match Rate" in r
    assert "Unmatched Client IDs" in r

check("crm_quality_report()",     _dq_crm)
check("ops_quality_report()",     _dq_ops)
check("targets_quality_report()", _dq_targets)
check("join_quality_report()",    _dq_join)

# ── Insights ──────────────────────────────────────────────────────────────────

from src.insights import get_all_insights

def _insights():
    results = get_all_insights(crm, ops, targets)
    assert isinstance(results, list),             "Expected a list"
    for item in results:
        assert "title"          in item,          f"Missing 'title' in insight: {item}"
        assert "severity"       in item,          f"Missing 'severity' in insight: {item}"
        assert "detail"         in item,          f"Missing 'detail' in insight: {item}"
        assert "recommendation" in item,          f"Missing 'recommendation' in insight: {item}"
        assert item["severity"] in ("warning", "success", "info"), \
            f"Unknown severity: {item['severity']}"
    return results

insights = check("get_all_insights()", _insights)

# ── Charts ────────────────────────────────────────────────────────────────────

from src.charts import (
    chart_leads_over_time, chart_leads_by_source, chart_leads_by_stage,
    chart_leads_by_region, chart_pipeline_value_by_owner, chart_stale_leads,
    chart_status_breakdown, chart_yoy_comparison,
    chart_projects_by_status, chart_projects_over_time, chart_workload_by_team,
    chart_workload_by_service, chart_client_workload, chart_sla_compliance,
    chart_targets_vs_actuals, chart_sales_to_ops,
)

sales_charts = [
    ("chart_leads_over_time",        lambda: chart_leads_over_time(crm)),
    ("chart_leads_by_source",        lambda: chart_leads_by_source(crm)),
    ("chart_leads_by_stage",         lambda: chart_leads_by_stage(crm)),
    ("chart_leads_by_region",        lambda: chart_leads_by_region(crm)),
    ("chart_pipeline_value_by_owner",lambda: chart_pipeline_value_by_owner(crm)),
    ("chart_stale_leads",            lambda: chart_stale_leads(crm)),
    ("chart_status_breakdown",       lambda: chart_status_breakdown(crm)),
    ("chart_yoy_comparison",         lambda: chart_yoy_comparison(crm)),
]

ops_charts = [
    ("chart_projects_by_status",  lambda: chart_projects_by_status(ops)),
    ("chart_projects_over_time",  lambda: chart_projects_over_time(ops)),
    ("chart_workload_by_team",    lambda: chart_workload_by_team(ops)),
    ("chart_workload_by_service", lambda: chart_workload_by_service(ops)),
    ("chart_client_workload",     lambda: chart_client_workload(ops)),
    ("chart_sla_compliance",      lambda: chart_sla_compliance(ops)),
    ("chart_targets_vs_actuals",  lambda: chart_targets_vs_actuals(crm, targets)),
    ("chart_sales_to_ops",        lambda: chart_sales_to_ops(joined)),
]

for name, fn in sales_charts + ops_charts:
    check(f"{name}()", fn)

# ── Empty data guard ──────────────────────────────────────────────────────────
# All chart functions should handle an empty DataFrame without crashing

import pandas as pd

empty_crm = crm.iloc[0:0].copy()
empty_ops = ops.iloc[0:0].copy()

check("chart_leads_over_time(empty)",        lambda: chart_leads_over_time(empty_crm))
check("chart_pipeline_value_by_owner(empty)",lambda: chart_pipeline_value_by_owner(empty_crm))
check("chart_sla_compliance(empty)",         lambda: chart_sla_compliance(empty_ops))
check("chart_workload_by_team(empty)",       lambda: chart_workload_by_team(empty_ops))

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'='*55}")
print(f"  Passed: {len(PASS)}   Failed: {len(FAIL)}")
print(f"{'='*55}")

if insights:
    print(f"\n  Insights generated ({len(insights)}):")
    for item in insights:
        print(f"    [{item['severity'].upper():8s}] {item['title']}")

print(f"\n  Quality snapshot:")
for k, v in quality.items():
    print(f"    {k}: {v}")

if FAIL:
    print(f"\n  FAILING CHECKS: {', '.join(FAIL)}")
    sys.exit(1)
else:
    print("\n  All checks passed.")
