import logging
from backend.agents.safety import SafetyAgent
from backend.agents.analysis import AnalysisAgent
from backend.agents.optimization import OptimizationAgent
from backend.agents.validation import ValidationAgent
from backend.agents.schema_builder import SchemaBuilderAgent
from backend.database import execute_query, main_engine, shadow_engine

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Agent 5: Orchestrator Agent
    Coordinates the pipeline: Safety -> Analysis -> Optimization -> Validation
    """

    def __init__(self):
        self.safety = SafetyAgent()
        self.schema_builder = SchemaBuilderAgent()
        self.analysis = AnalysisAgent()
        self.optimization = OptimizationAgent()
        self.validation = ValidationAgent()

    def _ensure_tables_exist(self, query: str) -> tuple[bool, list[str]]:
        """Check that all referenced tables exist in main DB."""
        try:
            tables = self.safety.extract_table_names(query)
            if not tables:
                return True, []

            placeholder = ','.join([f"'{t}'" for t in tables])
            sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ({placeholder})"
            rows = execute_query(main_engine, sql)
            existing = [r[0].lower() for r in rows] if rows else []
            missing = [t for t in tables if t not in existing]
            return (len(missing) == 0), missing
        except Exception as e:
            logger.warning(f"Table existence check failed: {e}")
            return True, []

    def process(self, query: str) -> dict:
        """Runs the entire multi-agent optimization pipeline."""
        logger.info(f"Orchestrator starting process for query: {query}")

        # Step 0: Query Classification
        statement_type = self.safety.get_statement_type(query)
        if statement_type not in ("SELECT", "WITH", "EXPLAIN"):
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": f"Unsupported query type '{statement_type}'. Only SELECT/WITH/EXPLAIN are allowed for optimization."
            }

        # Step 1: Safety Check
        if not self.safety.is_safe(query):
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": "Query rejected by Safety Agent. It contains flagged dangerous operations or is not a SELECT/EXPLAIN query."
            }

        # Step 2: Schema Extraction & Dynamic Table Creation
        logger.info("Extracting schema from query and creating dummy tables...")
        try:
            schema = self.schema_builder.extract_schema(query)
            if schema:
                # Create tables in both main and shadow DBs
                created_main = self.schema_builder.create_dummy_tables(schema, main_engine)
                created_shadow = self.schema_builder.create_dummy_tables(schema, shadow_engine)
                if not created_main or not created_shadow:
                    return {
                        "original_query": query,
                        "suggested_query": "N/A",
                        "improvement_percentage": 0.0,
                        "confidence_score": 0.0,
                        "details": "Schema builder failed while creating dynamic dummy tables."
                    }
                logger.info(f"Created dummy tables: {list(schema.keys())}")
            else:
                logger.warning("No schema could be extracted from query")
        except Exception as e:
            logger.error(f"Schema builder error: {e}")
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": f"Failed to create dummy tables: {str(e)}"
            }
            
        # Step 3: Analysis (Main DB)
        analysis_metrics = self.analysis.analyze(query)
        if "error" in analysis_metrics:
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": f"Analysis Agent failed: {analysis_metrics['error']}"
            }
            
        # Step 4: Optimization Suggestion
        suggestions = self.optimization.optimize(query, analysis_metrics)
        
        # Step 5: Validation (Shadow DB)
        validation_result = self.validation.validate(query, suggestions)
        if "error" in validation_result:
             return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": f"Validation Agent failed: {validation_result['error']}"
            }
            
        best_suggestion = validation_result.get("best_suggestion")
        improvement = validation_result.get("improvement_percentage", 0.0)
        baseline_time = validation_result.get("baseline_time_ms", 0.0)
        
        if best_suggestion and improvement > 0:
            details = (
                f"**Validated Optimization Found**\n\n"
                f"* **Original Speed:** {baseline_time} ms\n"
                f"* **Improvement Measured:** {improvement:.2f}%\n"
                f"* **Reasoning:** The Validation Agent tested this index in an ephemeral shadow database and successfully proved it accelerates the query. Implementing this suggestion will reduce I/O bottlenecks and sequential scans."
            )
            confidence = 0.95
        else:
            # If we couldn't validate an improvement but the optimization
            # agent still produced suggestions, present the top suggestion
            # as an unvalidated recommendation with lower confidence so the
            # user can review/apply it manually.
            if suggestions:
                best_suggestion = suggestions[0]
                details = (
                    f"**Heuristic Suggestion**\n\n"
                    f"* **Reasoning:** The Optimization Agent recommended this improvement based on best practices (e.g., adding an index or rewriting a subquery), "
                    f"but the Validation Agent could not decisively measure a speedup in the shadow database (often due to small dummy data sizes). "
                    f"Review and apply if it matches your schema needs."
                )
                confidence = 0.50
            else:
                best_suggestion = "No safe optimization found."
                details = (
                    f"**Query Looks Good**\n\n"
                    f"* **Reasoning:** No major bottlenecks, missing indexes, or anti-patterns were detected. "
                    f"Basic heuristics suggest the query is already well-optimized."
                )
                confidence = 0.50

        return {
            "original_query": query,
            "suggested_query": best_suggestion,
            "improvement_percentage": improvement,
            "confidence_score": confidence,
            "details": details,
            "baseline_time_ms": baseline_time,
            "rows_scanned": analysis_metrics.get("rows_scanned")
        }
