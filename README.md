# OptimQL — Autonomous Multi-Agent AI Database Optimizer

OptimQL is an autonomous multi-agent system that analyzes, optimizes, and validates SQL queries using a pipeline of specialized AI agents. It uses PostgreSQL's `EXPLAIN ANALYZE` to measure real execution plans, suggests index creation and query rewrites, then validates improvements in a shadow database before recommending changes.

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Safety Agent │ ──▶ │ Analysis     │ ──▶ │ Optimization     │ ──▶ │ Validation      │
│ (blocks DDL, │     │ Agent        │     │ Agent            │     │ Agent           │
│  injection)  │     │ (EXPLAIN on  │     │ (index, rewrite  │     │ (shadow DB test │
│              │     │  main DB)    │     │  suggestions)    │     │  + comparison)  │
└──────────────┘     └──────────────┘     └──────────────────┘     └─────────────────┘
         ▲                                                                  │
         │              Orchestrator Agent (coordinates pipeline)           │
         └──────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | Role |
|---|---|
| **Safety Agent** | Blocks dangerous operations (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, multi-statement injection). Only allows SELECT, WITH, and EXPLAIN queries. |
| **Analysis Agent** | Runs `EXPLAIN ANALYZE` on the main database and extracts execution metrics (sequential scans, index scans, cost, execution time). |
| **Optimization Agent** | Rule-based engine that suggests indexes for WHERE/JOIN/ORDER BY columns, trigram indexes for LIKE wildcards, correlated subquery rewrites, and SELECT * warnings. |
| **Validation Agent** | Applies suggested indexes to the shadow database, re-runs `EXPLAIN ANALYZE`, measures improvement percentage, then cleans up (drops test indexes). |
| **Orchestrator Agent** | Coordinates the full pipeline: Safety → Analysis → Optimization → Validation. Returns structured results to the API. |

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Database | PostgreSQL 15 (Docker) |
| Shadow DB | PostgreSQL 15 (Docker, port 5433) |
| ORM / SQL | SQLAlchemy 2.0 |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Alt Frontend | Streamlit (optional) |
| Testing | Pytest |

---

## Project Structure

```
OptimQL/
├── backend/
│   ├── main.py              # FastAPI app with /analyze endpoint
│   ├── database.py          # DB engines, session factories, query execution
│   ├── db_utils.py          # DB connection test + dummy data seeding
│   └── agents/
│       ├── orchestrator.py  # Pipeline coordinator
│       ├── safety.py        # Query safety checker
│       ├── analysis.py      # EXPLAIN ANALYZE executor
│       ├── optimization.py  # Index/rewrite suggestion engine
│       └── validation.py    # Shadow DB validation
├── frontend/
│   ├── app.py               # Streamlit frontend (optional)
│   └── react-app/           # React + TypeScript frontend
│       ├── src/
│       │   ├── App.tsx
│       │   ├── components/
│       │   │   ├── QueryEditor.tsx
│       │   │   ├── OptimizationResults.tsx
│       │   │   ├── PerformanceMetrics.tsx
│       │   │   └── ui/ (button, textarea, sonner)
│       │   └── utils/toast.ts
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.cjs
│       └── tsconfig.json
├── tests/
│   ├── test_orchestrator.py     # Pytest unit tests (mocked agents)
│   ├── test_smoke.py            # Offline agent smoke tests
│   └── validate_all_queries.py  # Full end-to-end API validation
├── tools/                       # Developer helper scripts
├── docker-compose.yml           # PostgreSQL main + shadow DBs
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project config + pytest settings
├── conftest.py                  # Pytest path configuration
├── .env                         # Database connection strings
└── pyrightconfig.json           # Type checking config
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop

### 1. Clone & Setup Python Environment

```bash
git clone https://github.com/DebangarajKaushik10/OptimQL.git
cd OptimQL
python -m venv venv
```

Activate the virtual environment:

```powershell
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Start Databases

```bash
docker compose up -d
```

This starts two PostgreSQL 15 containers:
- **Main DB** → `localhost:5432` (used for analysis)
- **Shadow DB** → `localhost:5433` (used for safe validation)

### 3. Seed Dummy Data

```bash
python -m backend.db_utils
```

Creates `users`, `orders`, and `products` tables with sample data in both databases.

### 4. Start the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

API available at: http://localhost:8000  
Swagger docs at: http://localhost:8000/docs

### 5. Start the React Frontend

```bash
cd frontend/react-app
npm install
npm run dev
```

Frontend available at: http://localhost:5173

---

## API Reference

### `GET /`
Health check.

```json
{ "status": "OptimQL Backend is running" }
```

### `POST /analyze`
Analyze and optimize a SQL query.

**Request:**
```json
{ "query": "SELECT * FROM users WHERE id = 1" }
```

**Response:**
```json
{
  "original_query": "SELECT * FROM users WHERE id = 1",
  "suggested_query": "Query looks reasonably optimized based on basic heuristics.",
  "improvement_percentage": 0.0,
  "confidence_score": 0.5,
  "details": "No validated improvement could be measured in the shadow DB."
}
```

| Field | Description |
|---|---|
| `original_query` | The input query |
| `suggested_query` | The optimization suggestion (CREATE INDEX, rewrite, or advice) |
| `improvement_percentage` | Measured improvement from shadow DB validation (0-100) |
| `confidence_score` | 0.95 = validated improvement, 0.50 = unvalidated suggestion, 0.0 = rejected |
| `details` | Human-readable explanation |

---

## Test Queries

These queries have been validated end-to-end against live databases:

### 1. JOIN with WHERE filter → Index suggestion
```sql
SELECT u.name, o.total_amount FROM users u JOIN orders o ON o.user_id = u.id WHERE o.status = 'pending'
```
**Result:** `CREATE INDEX ... ON orders (user_id)` — ~95% improvement, 0.95 confidence

### 2. SELECT * anti-pattern → Column advice
```sql
SELECT * FROM users
```
**Result:** "Avoid SELECT *; specify only the columns you need" — 0.50 confidence

### 3. LIKE with leading wildcard → Trigram index
```sql
SELECT * FROM products WHERE name LIKE '%phone%'
```
**Result:** `CREATE INDEX CONCURRENTLY ... USING gin (name gin_trgm_ops)` — ~97% improvement

### 4. ILIKE case-insensitive wildcard → Trigram index
```sql
SELECT * FROM products WHERE name ILIKE '%wireless%'
```
**Result:** Same trigram index suggestion — ~14% improvement

### 5. Correlated subquery → Rewrite + index
```sql
SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u
```
**Result:** LEFT JOIN + GROUP BY rewrite suggestion + index — ~57% improvement

### 6. DROP TABLE → Safety rejection
```sql
DROP TABLE users
```
**Result:** Rejected by Safety Agent — 0% improvement, 0.0 confidence

### 7. SQL injection attempt → Safety rejection
```sql
SELECT * FROM users; DROP TABLE users
```
**Result:** Rejected (multi-statement detected) — 0% improvement, 0.0 confidence

### 8. Simple PK lookup → Already optimized
```sql
SELECT id, name FROM users WHERE id = 1
```
**Result:** "Query looks reasonably optimized" — 0.50 confidence

---

## Running Tests

### Unit Tests (no database needed)
```bash
python -m pytest tests/test_orchestrator.py -v
```

### Smoke Tests (no database needed)
```bash
python -m pytest tests/test_smoke.py -v -s
```

### Full End-to-End Validation (requires running servers)
```bash
python tests/validate_all_queries.py
```

---

## Environment Variables

Configured in `.env` at the project root:

| Variable | Default | Description |
|---|---|---|
| `MAIN_DB_URL` | `postgresql://user:password@localhost:5432/main_db` | Main database connection |
| `SHADOW_DB_URL` | `postgresql://user:password@localhost:5433/shadow_db` | Shadow database connection |

---

## Optimization Capabilities

| Pattern Detected | Suggestion |
|---|---|
| Sequential scan on WHERE columns | `CREATE INDEX ON table (column)` |
| Sequential scan on JOIN columns | `CREATE INDEX ON table (join_column)` |
| Sequential scan on ORDER BY columns | `CREATE INDEX ON table (sort_column)` |
| LIKE/ILIKE with leading wildcard (`%...%`) | `CREATE INDEX CONCURRENTLY ... USING gin (col gin_trgm_ops)` |
| Correlated COUNT(*) subquery | Rewrite as LEFT JOIN + aggregated subquery |
| SELECT * usage | Advice to specify needed columns only |
| IN/NOT IN subqueries | Advice to consider EXISTS or JOINs |
| Dangerous DDL (DROP, DELETE, etc.) | Blocked by Safety Agent |
| Multi-statement queries | Blocked (SQL injection protection) |

---

## License

See repository for license information.
