# DeliverIQ — Logistics Profitability Analyzer

> **Client-simulation project for Forward Deployed Engineer prep.**
> You are embedded with a client for 2–3 days. They handed you three ugly data exports
> and one vague sentence. Ship something they can actually use.

---

## The Brief (read this like a real client said it)

> *"We run regional deliveries. We **know** we're losing money on some of them, but we
> have no idea which routes, drivers, or customers are the problem. Our ops manager is
> not technical — she lives in spreadsheets. Our last analyst gave us a 40-tab Excel file
> nobody understands. Can you just... show us where the money is leaking, and let us ask
> questions without bugging engineering every time?"*

That's the whole spec. Everything else is your job to figure out. **This ambiguity is the
point** — FDE interviews test exactly this.

### What "done" looks like (the deliverables)
1. A **cleaned, queryable database** built from 3 messy raw files.
2. An **API** the client's internal tools could call.
3. A **dashboard** the non-technical ops manager can actually use.
4. A **natural-language query box** so she can ask "which drivers lost us money in Q2?"
   without writing SQL.
5. A **one-page findings summary** — the single most important FDE deliverable: *insight,
   not just software.*

---

## Why this project (map to FDE skills)

| FDE skill tested | Where it shows up here |
|---|---|
| Messy / unfamiliar data | 3 raw files with real-world defects (see below) |
| SQL depth beyond CRUD | Profitability requires joins, window functions, aggregation |
| Build speed under ambiguity | Hard 3-day timebox; 80% solution beats perfect |
| Stakeholder communication | Dashboard + findings page for a non-technical user |
| LLM in a client workflow | NL→SQL query box, feedback theme extraction |
| Deploy to any environment | Dockerized so it runs anywhere the client has |
| Business framing | Deliverable is "$X leaking on route Y", not "I built an API" |

---

## The Messy Data (this is deliberate)

You'll generate (or I can generate for you) three raw files that imitate a real client dump.
**Do not clean them at the source — cleaning them is the job.**

**`raw/orders.csv`** — ~15,000 delivery records, with real-world defects baked in:
- Dates in mixed formats (`2024-03-01`, `01/03/2024`, `March 1 2024`, some blank)
- `delivery_fee` and `cost` columns with currency symbols, commas, and some negatives
- Duplicate order IDs (same order logged twice)
- `status` free-typed: `Delivered`, `delivered`, `DELIVERED`, `done`, `complete`
- Missing driver IDs on ~5% of rows
- Distances in mixed units (some km, some miles, unlabeled)

**`raw/drivers.xlsx`** — driver + vehicle info:
- Header row not on line 1 (junk rows on top — classic Excel export)
- Vehicle type inconsistent (`2-wheeler`, `bike`, `Motorcycle`, `MC`)
- Some drivers appear in orders but are missing from this file entirely

**`raw/feedback.csv`** — free-text customer feedback (unstructured):
- One row per complaint/review, no ratings, just text
- Mixed languages / code-mixed (nod to your Telugu+Hindi experience)
- This is where the **LLM** earns its place: extract theme + sentiment

---

## Architecture

```
  raw/*.{csv,xlsx}
        │
        ▼
  [ 1. ETL pipeline ]  ── pandas: clean, normalize, dedupe, unit-convert
        │
        ▼
  [ 2. PostgreSQL ]    ── star-ish schema: fact_orders + dim_driver + dim_customer
        │
        ├──────────────► [ 3. FastAPI ]  ── /metrics, /routes, /drivers, /ask (NL→SQL)
        │                      │
        │                      ▼
        └──────────────► [ 4. Streamlit dashboard ]  ── what the ops manager sees
                               │
                               ▼
                         [ 5. LLM layer ]  ── NL→SQL + feedback theme/sentiment
```

### Stack (chosen for build speed, swap if you prefer)
- **ETL:** Python + pandas
- **DB:** PostgreSQL (use `EXPLAIN ANALYZE` on at least one slow query — interview gold)
- **API:** FastAPI + SQLAlchemy + Pydantic
- **Dashboard:** Streamlit (fastest path to a non-technical-friendly UI)
- **LLM:** any provider's API — NL→SQL and feedback classification
- **Infra:** Docker Compose (Postgres + API + dashboard in one `up`)

---

## Timebox — 3 "client days"

Treat each as ~a focused half/full day. **Shipping beats polishing.**

### Day 1 — Understand & clean (do NOT touch the API yet)
- [ ] Open the raw files. Write down every defect you find *before* coding. (This note
      becomes part of your findings — clients love "here's what was wrong with your data".)
- [ ] Build `etl/clean.py`: load → fix dates → strip currency → dedupe → normalize status
      & vehicle types → convert all distances to km → flag unmatched driver IDs.
- [ ] Design the schema. Load clean data into Postgres via `etl/load.py`.
- [ ] **Checkpoint:** can you answer "what's total profit per driver?" in raw SQL? If yes,
      your foundation is solid.

### Day 2 — Expose & compute
- [ ] FastAPI endpoints:
  - `GET /metrics/summary` — total orders, revenue, cost, net margin
  - `GET /routes/unprofitable?limit=10` — worst routes by margin (window function here)
  - `GET /drivers/{id}` — per-driver profitability
  - `POST /ask` — natural-language question → generated SQL → result (the showpiece)
- [ ] Validate everything with Pydantic. Add `/docs` screenshot to your README later.
- [ ] Write the NL→SQL prompt carefully: give the LLM the schema, force it to return
      *read-only* SQL, and **never** `exec` raw LLM output against a write-capable
      connection (sandbox it — use a read-only DB role). Mention this safeguard in
      interviews; it shows production maturity.

### Day 3 — Communicate (the part that wins FDE interviews)
- [ ] Streamlit dashboard: KPI tiles (margin, worst route, worst driver), a chart of
      profit-by-route, a table of money-losing orders, and the NL query box.
- [ ] Run the feedback file through the LLM: tag each as theme (late / damaged / rude /
      pricing / other) + sentiment. Show the top complaint themes on the dashboard.
- [ ] Write `FINDINGS.md`: 1 page. "You are losing ~$X/month, concentrated on route Y and
      driver Z. Top complaint theme is late delivery (N% of feedback). Recommend A, B, C."
- [ ] Docker Compose it so `docker compose up` brings the whole thing to life.

### Stretch (only if time)
- [ ] Add a scheduled refresh (new raw drop → re-run ETL).
- [ ] Add auth to the API (you already know JWT).
- [ ] Deploy to AWS (EC2 + RDS) — you already have the cloud skills; this makes it a live demo link.

---

## Project Structure

```
deliveriq/
├── README.md               ← this file
├── FINDINGS.md             ← your 1-page client summary (write LAST, matters MOST)
├── docker-compose.yml
├── .env.example            ← DB creds, LLM API key (never commit the real .env)
├── raw/                    ← the messy input files (gitignored if large)
│   ├── orders.csv
│   ├── drivers.xlsx
│   └── feedback.csv
├── etl/
│   ├── clean.py            ← pandas cleaning logic
│   ├── load.py             ← load clean data into Postgres
│   └── schema.sql          ← table definitions + indexes
├── api/
│   ├── main.py             ← FastAPI app
│   ├── db.py               ← SQLAlchemy engine/session (read-only role for /ask)
│   ├── models.py           ← Pydantic schemas
│   └── llm.py              ← NL→SQL + feedback classification
├── dashboard/
│   └── app.py              ← Streamlit app
└── tests/
    └── test_clean.py       ← pytest: prove your cleaning handles the defects
```

---

## Setup

```bash
# 1. Clone / create the folder, then:
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt

# 2. Copy env template and fill in values
copy .env.example .env

# 3. Start Postgres (via Docker) and load data
docker compose up -d db
python etl/clean.py
python etl/load.py

# 4. Run the API
uvicorn api.main:app --reload
#    → open http://localhost:8000/docs

# 5. Run the dashboard (separate terminal)
streamlit run dashboard/app.py
```

### `requirements.txt` to start
```
pandas
openpyxl
sqlalchemy
psycopg2-binary
fastapi
uvicorn[standard]
pydantic
pydantic-settings
streamlit
plotly
pytest
python-dotenv
# + your LLM provider's SDK
```

---

## How to talk about this in interviews

Don't say *"I built a FastAPI app with a Streamlit dashboard."*

Say: *"A client gave me three broken data exports and one sentence. In three days I found
that ~70% of their losses came from one route and two drivers, built them a dashboard their
non-technical ops manager uses daily, and gave them a plain-English query box so they stopped
pinging engineering for every number. The hardest part wasn't the code — it was that the
data had five different date formats and duplicate orders inflating their revenue number by
8%, which nobody had caught."*

That paragraph is the entire point of this project. Build backward from being able to say it.

---

## Interview questions this project prepares you for
- "Walk me through how you'd handle a client's messy data export." → you lived it
- "How do you safely let an LLM generate SQL against a real database?" → read-only role, no exec of writes, schema-constrained prompt
- "How do you prioritize when you can't finish everything in the timebox?" → your Day 1/2/3 cuts
- "How do you explain a technical finding to a non-technical stakeholder?" → FINDINGS.md + dashboard
- "Tell me about a time you worked with no clear spec." → *this entire project*
```
