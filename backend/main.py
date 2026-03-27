from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
from backend.agents.orchestrator import OrchestratorAgent

app = FastAPI(title="OptimQL API", description="Autonomous Multi-Agent AI Database Optimizer API")

# Simple in-memory cache mapping normalized query to result 
# This ensures consistent metrics across multiple clicks
query_cache = {}

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
        
        # Return cached result if we've already optimized this exact query recently
        if normalized_query in query_cache:
            logging.info("Returning cached result to maintain consistency.")
            return OptimizationResult(**query_cache[normalized_query])

        orchestrator = OrchestratorAgent()
        result = orchestrator.process(normalized_query)

        # Save to cache
        query_cache[normalized_query] = result

        return OptimizationResult(**result)
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
