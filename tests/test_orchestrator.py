import pytest

from backend.agents.orchestrator import OrchestratorAgent


def test_orchestrator_happy_path(monkeypatch):
    query = "SELECT u.name, o.total_amount FROM users u JOIN orders o ON o.user_id = u.id WHERE o.status = 'pending'"

    # Stub SafetyAgent.is_safe -> True
    monkeypatch.setattr(
        "backend.agents.orchestrator.SafetyAgent.is_safe",
        lambda self, q: True,
    )

    # Stub SchemaBuilderAgent so it doesn't touch a real DB
    monkeypatch.setattr(
        "backend.agents.orchestrator.SchemaBuilderAgent.extract_schema",
        lambda self, q: {"users": {"name": "VARCHAR(255)"}, "orders": {"user_id": "INTEGER", "status": "VARCHAR(255)", "total_amount": "DECIMAL(10,2)"}},
    )
    monkeypatch.setattr(
        "backend.agents.orchestrator.SchemaBuilderAgent.create_dummy_tables",
        lambda self, schema, engine: True,
    )

    # Stub AnalysisAgent.analyze -> basic metrics
    monkeypatch.setattr(
        "backend.agents.orchestrator.AnalysisAgent.analyze",
        lambda self, q: {
            "raw_plan": "Seq Scan on orders o\n",
            "has_sequential_scan": True,
            "has_index_scan": False,
            "cost_estimate": "Startup: 0.00, Total: 10.00",
            "execution_time_ms": "5.0",
        },
    )

    # Stub OptimizationAgent.optimize -> index suggestion
    monkeypatch.setattr(
        "backend.agents.orchestrator.OptimizationAgent.optimize",
        lambda self, q, metrics: [
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id)"
        ],
    )

    # Stub ValidationAgent.validate -> reports improvement
    monkeypatch.setattr(
        "backend.agents.orchestrator.ValidationAgent.validate",
        lambda self, orig, sugg: {
            "best_suggestion": "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id)",
            "improvement_percentage": 50.0,
            "baseline_time_ms": 10.0,
        },
    )

    orchestrator = OrchestratorAgent()
    result = orchestrator.process(query)

    assert result["original_query"] == query
    assert "idx_orders_user_id" in result["suggested_query"]
    assert result["improvement_percentage"] == 50.0
    assert result["confidence_score"] == 0.95
    assert "Found safe optimization" in result["details"]


def test_orchestrator_safety_reject(monkeypatch):
    """A dangerous query should be rejected. The orchestrator first checks
    statement type (Step 0) and then safety (Step 1). A DROP query is caught
    at Step 0 as unsupported. We test both paths here."""
    # --- Path A: DROP is caught by statement-type classification (Step 0) ---
    query_drop = "DROP TABLE users;"
    orchestrator = OrchestratorAgent()
    result = orchestrator.process(query_drop)

    assert result["original_query"] == query_drop
    assert result["suggested_query"] == "N/A"
    assert result["improvement_percentage"] == 0.0
    assert result["confidence_score"] == 0.0
    assert "Unsupported query type" in result["details"]

    # --- Path B: A SELECT query that Safety Agent explicitly rejects ---
    query_select = "SELECT * FROM users"

    monkeypatch.setattr(
        "backend.agents.orchestrator.SafetyAgent.is_safe",
        lambda self, q: False,
    )

    result2 = orchestrator.process(query_select)

    assert result2["original_query"] == query_select
    assert result2["suggested_query"] == "N/A"
    assert result2["improvement_percentage"] == 0.0
    assert result2["confidence_score"] == 0.0
    assert "Safety Agent" in result2["details"]
