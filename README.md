# OptimQL

OptimQL is a multi-agent SQL optimization tool. It analyzes a query, checks it for safety, estimates execution cost, suggests rewrites or indexes, validates promising changes, and stores the result in a local history database for later review.

The current repository contains two user-facing surfaces:

- A FastAPI backend that exposes analysis and history endpoints.
- A React + TypeScript frontend that provides the analyzer, history browser, export actions, and documentation tabs.

## Architecture

```mermaid
flowchart LR
  User[User] --> UI[React Frontend]
  UI --> API[FastAPI Backend]
  API --> ORCH[Orchestrator Agent]

  ORCH --> SAFE[Safety Agent]
  SAFE --> ANALYZE[Analysis Agent]
  ANALYZE --> OPT[Optimization Agent]
  OPT --> VALIDATE[Validation Agent]

  VALIDATE --> API
  API --> HIST[(SQLite History DB)]
  HIST --> API
  API --> UI
```

### Request flow

```mermaid
sequenceDiagram
  participant U as User
  participant F as React App
  participant B as FastAPI
  participant O as Orchestrator
  participant H as SQLite History

  U->>F: Enter SQL and click Analyze
  F->>B: POST /analyze { query }
  B->>H: Check cached result
  alt cached result exists
    H-->>B: Stored optimization result
    B-->>F: Return cached response
  else new query
    B->>O: Process normalized query
    O->>O: Safety -> Analysis -> Optimization -> Validation
    O-->>B: Structured optimization result
    B->>H: Store result for history reuse
    B-->>F: Return analysis payload
  end
  F->>B: GET /history when History tab opens
  B->>H: Read most recent results
  H-->>B: History rows
  B-->>F: History list
```

### Backend responsibilities

| Layer | Responsibility |
|---|---|
| FastAPI API | Exposes `/`, `/analyze`, and `/history`. |
| Orchestrator | Coordinates the agent pipeline. |
| Safety agent | Rejects dangerous or multi-statement SQL. |
| Analysis agent | Measures execution behavior and cost. |
| Optimization agent | Produces index and rewrite suggestions. |
| Validation agent | Verifies candidate changes in a shadow environment. |
| SQLite history | Stores recent optimization results and serves cached responses for repeated queries. |

### Frontend responsibilities

| Area | Responsibility |
|---|---|
| Analyzer tab | Lets the user enter SQL, load examples, and run analysis. |
| Agent pipeline | Shows the step-by-step processing state while the backend runs. |
| Results panel | Displays the original query, optimized query, metrics, and suggestions. |
| History tab | Loads saved optimizations from `/history`. |
| Docs tab | Explains how the system works from the UI. |
| Export actions | Downloads the current result as JSON or CSV. |

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Agent logic | Python |
| Query history | SQLite |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Motion | Framer Motion |
| Icons | Lucide React |
| Testing | Pytest |

## Project Structure

```text
OptimQL/
├── backend/
│   ├── main.py              # FastAPI app with /, /analyze, /history
│   ├── history_db.py        # SQLite history storage and cache lookup
│   ├── database.py          # Database helpers and connection setup
│   ├── db_utils.py          # Database checks and seed helpers
│   └── agents/
│       ├── orchestrator.py   # Pipeline coordinator
│       ├── safety.py        # SQL safety checks
│       ├── analysis.py      # Query analysis and metrics extraction
│       ├── optimization.py  # Rewrite and index suggestions
│       ├── validation.py    # Shadow-db validation
│       └── schema_builder.py
├── frontend/
│   ├── app.py               # Optional Streamlit UI
│   └── react-app/
│       ├── src/
│       │   ├── App.tsx
│       │   ├── components/
│       │   │   ├── AgentPipeline.tsx
│       │   │   ├── OptimizationResults.tsx
│       │   │   ├── PerformanceMetrics.tsx
│       │   │   ├── QueryEditor.tsx
│       │   │   └── ui/
│       │   └── utils/
│       ├── index.html
│       ├── package.json
│       ├── tailwind.config.cjs
│       └── vite.config.ts
├── tests/
├── tools/
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

## How It Works

1. The user enters a SQL query in the React analyzer.
2. The frontend sends the normalized query to `POST /analyze`.
3. The backend checks SQLite history first.
4. If the query was seen before, the cached result is returned immediately.
5. Otherwise, the orchestrator runs the safety, analysis, optimization, and validation steps.
6. The backend stores the final result in SQLite history.
7. The frontend renders the metrics, query diff, and agent pipeline.
8. The History tab reads from `GET /history` and shows recent runs.

## API Reference

### `GET /`

Health check.

```json
{ "status": "OptimQL Backend is running" }
```

### `POST /analyze`

Analyze and optimize a SQL query.

Request:

```json
{ "query": "SELECT * FROM users WHERE id = 1" }
```

Response fields:

| Field | Description |
|---|---|
| `original_query` | Input query. |
| `suggested_query` | Recommended optimized query or advice. |
| `improvement_percentage` | Measured improvement from validation. |
| `confidence_score` | Confidence in the result. |
| `details` | Human-readable explanation. |
| `baseline_time_ms` | Baseline execution time when available. |
| `rows_scanned` | Rows scanned when available. |

### `GET /history`

Returns the most recent cached optimization results.

## Example Optimization Patterns

| Pattern | Typical Outcome |
|---|---|
| Sequential scan on a filter column | Add an index on the filter column. |
| Join-heavy query | Add an index on the join key. |
| Leading-wildcard `LIKE` / `ILIKE` | Suggest a trigram index. |
| Correlated subquery | Suggest a rewrite using joins or aggregation. |
| `SELECT *` | Suggest selecting only required columns. |
| Dangerous DDL or multi-statement input | Reject the query. |

## Frontend Flow

```mermaid
flowchart TD
  A[Analyzer tab] --> B[Load example or paste SQL]
  B --> C[Click Analyze]
  C --> D[Show Agent Pipeline]
  D --> E[Render Metrics]
  D --> F[Render Original and Optimized Query]
  E --> G[Export JSON or CSV]
  A --> H[History tab]
  H --> I[Fetch /history]
  I --> J[Render saved runs]
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker Desktop

### Backend

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python -m backend.db_utils
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend/react-app
npm install
npm run dev
```

## Testing

Unit tests:

```bash
python -m pytest tests/test_orchestrator.py -v
```

Smoke tests:

```bash
python -m pytest tests/test_smoke.py -v -s
```

End-to-end validation:

```bash
python tests/validate_all_queries.py
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MAIN_DB_URL` | `postgresql://user:password@localhost:5432/main_db` | Main database connection. |
| `SHADOW_DB_URL` | `postgresql://user:password@localhost:5433/shadow_db` | Shadow database connection. |

## Notes

- The local SQLite history file is generated by the backend and should not be committed.
- The React app is the primary UI; the Streamlit app remains optional.
- The backend caches repeated queries through the history table to avoid recomputing the same result.
