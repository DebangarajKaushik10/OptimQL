import sys
from pathlib import Path

# Ensure repository root is on sys.path so we can import the package when
# running this helper script from /tools
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.database import get_execution_plan, main_engine

q = "SELECT u.id, u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u;"
plan = get_execution_plan(main_engine, q)
if plan:
    for row in plan:
        print(row[0])
else:
    print('No plan returned or query failed')
