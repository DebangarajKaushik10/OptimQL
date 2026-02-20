from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.agents.analysis import AnalysisAgent
from backend.agents.optimization import OptimizationAgent

q = "SELECT * FROM products WHERE name LIKE '%phone%';"
ana = AnalysisAgent()
metrics = ana = ana = ana = AnalysisAgent().analyze(q)
opt = OptimizationAgent()
suggestions = opt.optimize(q, metrics)
print('Analysis metrics:')
print(metrics)
print('\nSuggestions:')
for s in suggestions:
    print('-', s)
