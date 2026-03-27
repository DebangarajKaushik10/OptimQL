from pathlib import Path
import sys
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.database import get_execution_plan, main_engine

q = "SELECT * FROM products WHERE name LIKE '%phone%';"
plan = get_execution_plan(main_engine, q)
if plan:
    for row in plan:
        print(row[0])
else:
    print('No plan returned or query failed')
