# Screen-Recorded Demo Video Script (3–5 Minutes)

> **Purpose**: Use this structured script to record the 3–5 minute video demonstration required by **PRD Section 13** for the Braahmam International Limited assignment.

---

## ⏱️ Video Outline (Target: 3:30 – 4:30)

| Timestamp | Segment | Key Action / Talking Point |
|---|---|---|
| **0:00 – 0:30** | **Introduction & Problem Statement** | Welcome, explain the objective (unifying fragmented CRM, Ops, and Sheet data into a single source of truth without live credentials). |
| **0:30 – 1:30** | **Sales Dashboard & Funnel Metrics** | Walk through the 5 KPIs, monthly lead trend, status breakdown (Won/Lost/Open), and the stage conversion table with explicit denominators. Demonstrate record inspection. |
| **1:30 – 2:30** | **Operations Dashboard & Combined View** | Highlight SLA compliance, workload by team/service/client, and Target vs Forecast vs Actual. Explain the Sales-to-Ops joined view (green matched, red unmatched). |
| **2:30 – 3:30** | **Rule-Based Insights & Multi-Year Trends** | Present the 8 analytical insights. Show how observed facts are strictly separated from recommendations. Highlight the 2025 vs 2026 Year-over-Year comparison. |
| **3:30 – 4:15** | **Filters, Data Quality & SQLite Integration** | Toggle date and region filters to prove reactivity. Switch to Tab 4 to show null/unmatched reporting, data dictionary, and run an ad-hoc SQL query against the embedded SQLite database. |
| **4:15 – 4:45** | **Production Roadmap & Wrap-up** | Conclude with the 5-phase production roadmap (OAuth, canonical UUIDs, RBAC, DWH, AI governance). |

---

## 🎙️ Spoken Script & Screen Actions

### Part 1: Intro (0:00 – 0:30)
* **What to show on screen**: Browser open to `http://localhost:8501`, full dashboard view.
* **What to say**:
  > *"Hello, my name is [Your Name], and this is my submission for the Braahmam International Limited Sales & Operations Intelligence Dashboard prototype. The business challenge was that critical sales and operational data live in separate silos—GoHighLevel CRM, Plunet operations, and Google Sheets planning documents. Today, I'll demonstrate how our modular Python and Streamlit solution ingests, normalises, and correlates these sources into actionable intelligence with zero hallucination risk."*

---

### Part 2: Sales Dashboard (0:30 – 1:30)
* **What to show on screen**: Tab 1 (Sales Dashboard). Scroll across the 5 top KPIs and charts.
* **What to say**:
  > *"Starting with the Sales Dashboard: across the top, we track Total Leads, Open Pipeline Value, Won Deals, Overall Win Rate, and Average Deal Size. Below, we see monthly lead trajectory alongside an opportunity status breakdown. Notice our Stage Conversion Table: as requested in Section 6.2 of the PRD, every conversion step explicitly defines its denominator—both step-by-step drop-off and overall funnel yield from top of funnel. We also have proactive stale-lead indicators for deals inactive for over 14 days, and managers can open this expandable drawer to inspect the exact records behind the pipeline numbers."*

---

### Part 3: Operations & Combined View (1:30 – 2:30)
* **What to show on screen**: Click on Tab 2 (Operations Dashboard). Scroll to workload charts, Targets vs Forecast vs Actual, and the Sales-to-Ops chart.
* **What to say**:
  > *"Moving to the Operations Dashboard: we monitor active, overdue, and completed projects, plus total revenue and SLA compliance. We provide breakdown by team, service line, and client workload. In this chart, we track Target vs Forecast vs Actual won revenue side-by-side. Crucially, in our Combined Sales-to-Operations view, we bridge operations projects with CRM accounts. Green bars represent defensibly matched client accounts, while red bars clearly highlight unlinked operations clients—meaning we never hide data gaps from management."*

---

### Part 4: Analytical Insights & Trends (2:30 – 3:30)
* **What to show on screen**: Click on Tab 3 (Insights & Trends).
* **What to say**:
  > *"In Tab 3, we implement rule-based analytical insights. Per PRD Section 6.5, these insights are 100% deterministic, eliminating LLM hallucinations. Each card clearly separates Observed Facts from Actionable Recommendations. For example, our pipeline concentration alert warns if a single sales rep holds over 40% of open value. Furthermore, to answer PRD Question 5 regarding previous year trends, we provide a Year-over-Year comparison showing 2025 versus 2026 inbound volume across identical calendar months."*

---

### Part 5: Filters, Data Quality & SQLite (3:30 – 4:15)
* **What to show on screen**: Change the Region filter in the sidebar; observe the KPIs update. Then click Tab 4 (Data Quality & Docs). Run a query in the Live SQL tab.
* **What to say**:
  > *"Every chart and metric dynamically responds to our 5 global sidebar filters. In Tab 4, we showcase our data governance layer: complete quality audits detailing nulls, duplicate IDs, and unmatched records, accompanied by an inline data dictionary and KPI formula definitions. In addition, satisfying PRD Section 4.1, all data is mirrored into an embedded SQLite database, `data/intelligence.db`. Evaluators can even run live SQL queries directly inside the dashboard."*

---

### Part 6: Production Roadmap & Conclusion (4:15 – 4:45)
* **What to show on screen**: Scroll down to the Production Roadmap section or open `docs/PRODUCTION_ROADMAP.md`.
* **What to say**:
  > *"To transition this prototype into enterprise production, our roadmap outlines OAuth2 integration for GHL, webhook triggers for Plunet, canonical UUID entity mapping, Postgres/BigQuery warehousing, and role-based access control. All code is accompanied by 34 automated smoke tests and documented in our repository. Thank you for your time and consideration!"*

---

## 💡 Recording Tips
1. **Screen Resolution**: Set display to 1080p (1920x1080) with 100% scaling so all Streamlit charts fit neatly.
2. **Audio**: Use a headset mic to ensure crisp, clean audio with minimal background noise.
3. **Free Tools**: Use **OBS Studio** or Windows built-in Game Bar (`Win + G` or `Win + Alt + R`) or **Loom** for seamless recording.

