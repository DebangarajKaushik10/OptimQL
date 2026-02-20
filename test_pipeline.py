"""Quick diagnostic script for the OptimQL pipeline."""
from backend.database import execute_query, get_execution_plan, main_engine, shadow_engine

# 1. Check tables exist
print("=== Tables in Main DB ===")
tables = execute_query(main_engine, "SELECT tablename FROM pg_tables WHERE schemaname='public'")
print(tables)

print("\n=== Tables in Shadow DB ===")
tables_s = execute_query(shadow_engine, "SELECT tablename FROM pg_tables WHERE schemaname='public'")
print(tables_s)

# 2. Check data
print("\n=== Users ===")
print(execute_query(main_engine, "SELECT * FROM users"))

print("\n=== Orders ===")
print(execute_query(main_engine, "SELECT * FROM orders"))

# 3. Test EXPLAIN ANALYZE
test_query = "SELECT u.name, o.total_amount FROM users u JOIN orders o ON o.user_id = u.id WHERE o.status = 'pending'"
print(f"\n=== Execution Plan for test query ===")
plan = get_execution_plan(main_engine, test_query)
if plan:
    for row in plan:
        print(row[0])

# 4. Test the full pipeline
print("\n=== Full Pipeline Test ===")
from backend.agents.orchestrator import OrchestratorAgent
orch = OrchestratorAgent()
result = orch.process(test_query)
for k, v in result.items():
    print(f"  {k}: {v}")
