# generate_data.py
# Creates all three synthetic datasets used by the dashboard.
# Run this once before starting the app: python generate_data.py
#
# All data is entirely made up. It's designed to look plausible but
# deliberately includes ~20% unmatched ops clients to simulate real-world
# data gaps between systems.

import csv
import json
import os
import random
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATE_START = datetime(2024, 1, 1)
DATE_END   = datetime(2025, 9, 30)

# Reference data
REGIONS   = ["North", "South", "East", "West", "Central"]
SOURCES   = ["Referral", "Website", "Cold Call", "LinkedIn", "Trade Show", "Email Campaign", "Partner"]
STAGES    = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Closed Won", "Closed Lost"]
OWNERS    = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Lee", "Emily Chen", "Frank Wilson", "Grace Kim"]
SEGMENTS  = ["Enterprise", "Mid-Market", "SMB"]
CAMPAIGNS = ["Q1 Push", "Q2 Growth", "Q3 Scale", "Q4 Close", "Always-On", "Partner Enablement"]
SERVICES  = ["Translation", "Localization", "Transcription", "Interpretation", "Voiceover", "Subtitling", "DTP"]
TEAMS     = ["Team Alpha", "Team Beta", "Team Gamma", "Team Delta"]

# Companies used in CRM (all 20 will appear in crm_leads)
CRM_COMPANIES = [
    "Apex Corp", "BlueSky Ltd", "Cascade Inc", "Delta Partners", "Everest Solutions",
    "Frontier Tech", "Global Reach", "Horizon Group", "Infinity Co", "Jetstream LLC",
    "KineTech", "Luminary Ventures", "Momentum Ltd", "Nova Dynamics", "Orbit Systems",
    "Pinnacle Works", "Quasar Group", "Radiant Corp", "Summit Strategies", "Titan Group",
]

# Ops uses 12 CRM companies + 3 that don't exist in CRM (intentional mismatch)
OPS_CLIENTS = CRM_COMPANIES[:12] + ["Zenith Consulting", "Arc Analytics", "Prism Solutions"]


def rand_date(start: datetime, end: datetime) -> datetime:
    return start + timedelta(days=random.randint(0, (end - start).days))


def fmt_date(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def write_csv(path: str, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ── CRM Leads ─────────────────────────────────────────────────────────────────

def generate_crm(n: int = 200) -> None:
    rows = []
    for i in range(1, n + 1):
        created = rand_date(DATE_START, DATE_END)
        stage   = random.choice(STAGES)

        if stage == "Closed Won":
            status = "Won"
        elif stage == "Closed Lost":
            status = "Lost"
        else:
            status = "Open"

        # New Leads don't have a deal value yet — this is normal, not missing data
        deal_value = (
            round(random.uniform(2000, 120_000), 2)
            if stage != "New Lead"
            else ""
        )

        last_activity = min(created + timedelta(days=random.randint(0, 60)), DATE_END)

        rows.append({
            "lead_id":            f"CRM-{i:04d}",
            "created_date":       fmt_date(created),
            "source":             random.choice(SOURCES),
            "owner":              random.choice(OWNERS),
            "company":            random.choice(CRM_COMPANIES),
            "region":             random.choice(REGIONS),
            "pipeline_stage":     stage,
            "deal_value":         deal_value,
            "status":             status,
            "last_activity_date": fmt_date(last_activity),
            "account_segment":    random.choice(SEGMENTS),
        })

    write_csv(os.path.join(OUTPUT_DIR, "crm_leads.csv"), rows)
    print(f"  crm_leads.csv        {n} rows")


# ── Operations Projects ───────────────────────────────────────────────────────

def generate_ops(n: int = 150) -> None:
    projects = []
    for i in range(1, n + 1):
        created = rand_date(DATE_START, DATE_END)
        due     = created + timedelta(days=random.randint(7, 90))

        status = random.choices(
            ["Open", "In Progress", "Completed", "Overdue", "On Hold"],
            weights=[20, 30, 35, 10, 5],
            k=1,
        )[0]

        completed_date = None
        if status == "Completed":
            # Completed a few days before or on the due date
            completed_date = fmt_date(due - timedelta(days=random.randint(0, 5)))

        if status == "Completed":
            sla_status = "Breached" if random.random() < 0.15 else "Met"
        elif status == "Overdue":
            sla_status = "Breached"
        else:
            sla_status = "Pending"

        projects.append({
            "project_id":     f"OPS-{i:04d}",
            "client_id":      random.choice(OPS_CLIENTS),
            "status":         status,
            "service_type":   random.choice(SERVICES),
            "created_date":   fmt_date(created),
            "due_date":       fmt_date(due),
            "completed_date": completed_date,
            "amount":         round(random.uniform(500, 80_000), 2),
            "assigned_team":  random.choice(TEAMS),
            "sla_status":     sla_status,
            "sla_days":       (due - created).days,
            "currency":       "USD",
        })

    with open(os.path.join(OUTPUT_DIR, "ops_projects.json"), "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2)
    print(f"  ops_projects.json    {n} records")


# ── Targets Sheet ─────────────────────────────────────────────────────────────

def generate_targets() -> None:
    """
    Produces one row per owner per region per month — mimicking a Google Sheets
    planning export. Forecast is allowed to differ from target by up to 25%
    to give the dashboard something interesting to show.
    """
    rows = []

    # Build month list from Jan 2024 to Sep 2025
    months = []
    d = datetime(2024, 1, 1)
    while d <= datetime(2025, 9, 1):
        months.append(d)
        month = d.month + 1
        year  = d.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        d = datetime(year, month, 1)

    for month in months:
        for owner in OWNERS:
            for region in REGIONS:
                target   = round(random.uniform(10_000, 60_000), 2)
                forecast = round(target * random.uniform(0.75, 1.25), 2)
                rows.append({
                    "month":            month.strftime("%Y-%m"),
                    "owner":            owner,
                    "region":           region,
                    "account_segment":  random.choice(SEGMENTS),
                    "campaign":         random.choice(CAMPAIGNS),
                    "target_revenue":   target,
                    "forecast_revenue": forecast,
                    "currency":         "USD",
                })

    write_csv(os.path.join(OUTPUT_DIR, "targets_sheet.csv"), rows)
    print(f"  targets_sheet.csv    {len(rows)} rows")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating synthetic datasets into ./data/ ...")
    generate_crm(200)
    generate_ops(150)
    generate_targets()
    print("Done. Run: streamlit run app.py")
