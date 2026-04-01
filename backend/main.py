from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
from backend.agents.orchestrator import OrchestratorAgent
from backend.history_db import init_history_db, insert_history, get_history, get_cached_result

app = FastAPI(title="OptimQL API", description="Autonomous Multi-Agent AI Database Optimizer API")

# Initialize SQLite database for history tracking
init_history_db()

# CORS: allow local frontend dev servers (Vite/React)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SQLQueryRequest(BaseModel):
    query: str

class OptimizationResult(BaseModel):
    original_query: str
    suggested_query: str
    improvement_percentage: float
    confidence_score: float
    details: str
    baseline_time_ms: Optional[float] = None
    rows_scanned: Optional[int] = None

@app.get("/")
def read_root():
    return {"status": "OptimQL Backend is running"}

@app.post("/analyze", response_model=OptimizationResult)
async def analyze_query(request: SQLQueryRequest):
    try:
        normalized_query = request.query.strip()
        
        # Check SQLite db for matching original query
        cached_run = get_cached_result(normalized_query)
        if cached_run:
            logging.info("Returning cached result from SQLite db.")
            return OptimizationResult(
                original_query=cached_run["original_query"],
                suggested_query=cached_run["suggested_query"],
                improvement_percentage=cached_run["improvement_pct"],
                confidence_score=cached_run["confidence_score"],
                details=cached_run["details"],
                baseline_time_ms=cached_run["baseline_time_ms"],
                rows_scanned=cached_run["rows_scanned"]
            )

        orchestrator = OrchestratorAgent()
        result = orchestrator.process(normalized_query)

        # Save to SQLite history
        insert_history(
            original_query=result["original_query"],
            suggested_query=result["suggested_query"],
            improvement_pct=result["improvement_percentage"],
            confidence_score=result["confidence_score"],
            baseline_time_ms=result.get("baseline_time_ms"),
            rows_scanned=result.get("rows_scanned"),
            details=result["details"]
        )

        return OptimizationResult(**result)
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def read_history():
    try:
        return get_history()
    except Exception as e:
        logging.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
