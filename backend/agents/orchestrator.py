import logging
from backend.agents.safety import SafetyAgent
from backend.agents.analysis import AnalysisAgent
from backend.agents.optimization import OptimizationAgent
from backend.agents.validation import ValidationAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    Agent 5: Orchestrator Agent
    Coordinates the pipeline: Safety -> Analysis -> Optimization -> Validation
    """

    def __init__(self):
        self.safety = SafetyAgent()
        self.analysis = AnalysisAgent()
        self.optimization = OptimizationAgent()
        self.validation = ValidationAgent()

    def process(self, query: str) -> dict:
        """Runs the entire multi-agent optimization pipeline."""
        logger.info(f"Orchestrator starting process for query: {query}")
        
        # Step 1: Safety Check
        if not self.safety.is_safe(query):
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": "Query rejected by Safety Agent. It contains flagged dangerous operations or is not a SELECT/EXPLAIN query."
            }
            
        # Step 2: Analysis (Main DB)
        analysis_metrics = self.analysis.analyze(query)
        if "error" in analysis_metrics:
            return {
                "original_query": query,
                "suggested_query": "N/A",
                "improvement_percentage": 0.0,
                "confidence_score": 0.0,
                "details": f"Analysis Agent failed: {analysis_metrics['error']}"
            }
            
        # Step 3: Optimization Suggestion
        suggestions = self.optimization.optimize(query, analysis_metrics)
        
        # Step 4: Validation (Shadow DB)
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
        
        if best_suggestion and improvement > 0:
            details = "Found safe optimization improvement during shadow validation."
            confidence = 0.95
        else:
            # If we couldn't validate an improvement but the optimization
            # agent still produced suggestions, present the top suggestion
            # as an unvalidated recommendation with lower confidence so the
            # user can review/apply it manually.
            if suggestions:
                best_suggestion = suggestions[0]
                details = "No validated improvement could be measured in the shadow DB. Presenting the top recommendation unvalidated."
                confidence = 0.50
            else:
                best_suggestion = "No safe optimization found."
                details = "No significant improvement could be generated or validated safely."
                confidence = 0.50

        return {
            "original_query": query,
            "suggested_query": best_suggestion,
            "improvement_percentage": improvement,
            "confidence_score": confidence,
            "details": details
        }
