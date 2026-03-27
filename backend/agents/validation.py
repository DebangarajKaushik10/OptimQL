import re
import logging
from backend.database import get_execution_plan, execute_query, shadow_engine
from sqlalchemy import text
from backend.agents.analysis import AnalysisAgent

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Agent 4: Validation Agent
    Takes optimization suggestions, applies them to Shadow DB momentarily,
    and runs EXPLAIN ANALYZE to compare cost/time.
    """

    def __init__(self):
        self.analysis_agent = AnalysisAgent()

    def validate(self, original_query: str, suggestions: list[str]) -> dict:
        """
        Tests the suggestions in the shadow DB.
        Rolls back changes afterward if possible or drops created indexes.
        """
        logs: list[str] = []
        try:
            logs.append("Getting baseline execution plan from shadow DB...")
            baseline_plan = get_execution_plan(shadow_engine, original_query)
        except Exception as e:
            logs.append(f"Failed to get baseline from shadow DB: {e}")
            return {"error": f"Failed to get baseline from shadow DB: {e}", "validation_logs": logs}

        if not baseline_plan:
            logs.append("Failed to get baseline from shadow DB: no plan returned")
            return {"error": "Failed to get baseline from shadow DB.", "validation_logs": logs}

        baseline_text = "\n".join([row[0] for row in baseline_plan])
        baseline_time_str = self.analysis_agent._extract_time(baseline_text)
        baseline_time = float(baseline_time_str) if baseline_time_str != "Unknown" else 0.0

        logger.info(f"Baseline execution time: {baseline_time} ms")
        logger.info(f"Baseline plan:\n{baseline_text}")
        logs.append(f"Baseline execution time: {baseline_time} ms")
        logs.append(baseline_text)

        best_improvement = 0.0
        best_suggestion = None

        for suggestion in suggestions:
            # We only support CREATE INDEX for safe simulation right now
            if not suggestion.upper().startswith("CREATE INDEX"):
                logger.info(f"Skipping non-index suggestion: {suggestion}")
                logs.append(f"Skipping non-index suggestion: {suggestion}")
                continue

            # Extract index name from: CREATE INDEX [IF NOT EXISTS] idx_name ON ...
            idx_match = re.search(
                # Allow optional CONCURRENTLY between INDEX and IF NOT EXISTS
                r"CREATE\s+INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
                suggestion, re.IGNORECASE,
            )
            if not idx_match:
                logger.warning(f"Could not parse index name from: {suggestion}")
                logs.append(f"Could not parse index name from: {suggestion}")
                continue

            idx_name = idx_match.group(1)
            logger.info(f"Testing suggestion: {suggestion} (index: {idx_name})")
            logs.append(f"Testing suggestion: {suggestion} (index: {idx_name})")

            try:
                # 1. Apply suggestion (create index on shadow DB)
                exec_suggestion = suggestion

                # If suggestion requires pg_trgm (gin_trgm_ops) or uses CONCURRENTLY,
                # we may need to run those statements in autocommit mode. Use the
                # execute_autocommit helper when necessary.
                needs_trgm = "gin_trgm_ops" in exec_suggestion.lower()
                needs_concurrent = bool(re.search(r"\bCONCURRENTLY\b", exec_suggestion, re.IGNORECASE))

                if needs_trgm:
                    try:
                        from backend.database import execute_autocommit

                        execute_autocommit(shadow_engine, "CREATE EXTENSION IF NOT EXISTS pg_trgm")
                        logger.info("Ensured pg_trgm extension exists in shadow DB.")
                        logs.append("Ensured pg_trgm extension exists in shadow DB.")
                    except Exception as ext_err:
                        logger.warning(f"Could not create pg_trgm extension in shadow DB: {ext_err}")
                        logs.append(f"Could not create pg_trgm extension in shadow DB: {ext_err}")

                if needs_concurrent:
                    try:
                        from backend.database import execute_autocommit

                        execute_autocommit(shadow_engine, exec_suggestion)
                        logs.append(f"Applied suggestion in autocommit: {exec_suggestion}")
                    except Exception as e:
                        logger.error(f"Failed to apply concurrent suggestion in autocommit: {e}")
                        logs.append(f"Failed to apply concurrent suggestion in autocommit: {e}")
                        raise
                else:
                    execute_query(shadow_engine, exec_suggestion)
                    logs.append(f"Applied suggestion: {exec_suggestion}")

                # 2. Re-run query plan with the new index
                new_plan = get_execution_plan(shadow_engine, original_query)
                if not new_plan:
                    logger.warning("Could not get new plan after applying suggestion")
                    logs.append("Could not get new plan after applying suggestion")
                    continue

                new_text = "\n".join([row[0] for row in new_plan])
                new_time_str = self.analysis_agent._extract_time(new_text)
                new_time = float(new_time_str) if new_time_str != "Unknown" else 0.0

                logger.info(f"New execution time: {new_time} ms")
                logs.append(f"New execution time: {new_time} ms")

                # 3. Calculate improvement
                if baseline_time > 0 and new_time > 0:
                    improvement = ((baseline_time - new_time) / baseline_time) * 100
                    logger.info(f"Improvement: {improvement:.2f}%")
                    logs.append(f"Improvement measured: {improvement:.2f}% for suggestion {suggestion}")
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_suggestion = suggestion
                elif baseline_time > 0 and new_time == 0:
                    # Query got faster than measurable
                    best_improvement = 100.0
                    best_suggestion = suggestion

            except Exception as e:
                logger.error(f"Error testing suggestion '{suggestion}': {e}")
                logs.append(f"Error testing suggestion '{suggestion}': {e}")
            finally:
                # 4. Always clean up: drop the index
                try:
                    execute_query(shadow_engine, f"DROP INDEX IF EXISTS {idx_name}")
                    logger.info(f"Cleaned up index: {idx_name}")
                    logs.append(f"Cleaned up index: {idx_name}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to clean up index {idx_name}: {cleanup_err}")
                    logs.append(f"Failed to clean up index {idx_name}: {cleanup_err}")

        return {
            "best_suggestion": best_suggestion,
            "improvement_percentage": round(best_improvement, 2),
            "baseline_time_ms": baseline_time,
            "validation_logs": logs,
        }
