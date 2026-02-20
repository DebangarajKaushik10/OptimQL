from backend.database import get_execution_plan, main_engine

class AnalysisAgent:
    """
    Agent 2: Query Analysis Agent
    Reads execution plan from database using EXPLAIN ANALYZE.
    """

    def analyze(self, query: str) -> dict:
        """Runs the query and extracts performance metrics."""
        
        try:
            plan_rows = get_execution_plan(main_engine, query)
            if not plan_rows:
                return {"error": "Could not retrieve execution plan."}

            plan_text = "\n".join([row[0] for row in plan_rows])
            
            # Very basic extraction logic for demo purposes
            metrics = {
                "raw_plan": plan_text,
                "has_sequential_scan": "Seq Scan" in plan_text,
                "has_index_scan": "Index Scan" in plan_text,
                "cost_estimate": self._extract_cost(plan_text),
                "execution_time_ms": self._extract_time(plan_text)
            }
            
            return metrics
            
        except Exception as e:
            return {"error": str(e)}

    def _extract_cost(self, plan_text: str) -> str:
        # Example: "cost=0.00..35.50"
        import re
        match = re.search(r"cost=([\d\.]+)\.\.([\d\.]+)", plan_text)
        if match:
             return f"Startup: {match.group(1)}, Total: {match.group(2)}"
        return "Unknown"

    def _extract_time(self, plan_text: str) -> str:
        # Example: "Execution Time: 0.052 ms"
        import re
        match = re.search(r"Execution Time:\s*([\d\.]+)\s*ms", plan_text)
        if match:
             return match.group(1)
        return "Unknown"
