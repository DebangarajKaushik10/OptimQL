from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.agents.orchestrator import OrchestratorAgent

q = "SELECT * FROM products WHERE name LIKE '%phone%';"
orch = OrchestratorAgent()
res = orch.process(q)
print(res)
