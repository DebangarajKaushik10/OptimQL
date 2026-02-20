from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from backend.agents.orchestrator import OrchestratorAgent

app = FastAPI(title="OptimQL API", description="Autonomous Multi-Agent AI Database Optimizer API")

# CORS: allow local frontend dev servers (Vite/React)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
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

@app.get("/")
def read_root():
    return {"status": "OptimQL Backend is running"}

@app.post("/analyze", response_model=OptimizationResult)
async def analyze_query(request: SQLQueryRequest):
    try:
        orchestrator = OrchestratorAgent()
        result = orchestrator.process(request.query)

        return OptimizationResult(**result)
    except Exception as e:
        logging.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
