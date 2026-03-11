"""Quick smoke test for all agents without requiring a database."""
from backend.agents.safety import SafetyAgent
from backend.agents.optimization import OptimizationAgent

# --- SafetyAgent tests ---
s = SafetyAgent()
cases = [
    ("SELECT * FROM users", True),
    ("SELECT * FROM users;", True),  # trailing semicolon allowed
    ("DROP TABLE users", False),
    ("DELETE FROM orders", False),
    ("SELECT 1; DROP TABLE users", False),
    ("EXPLAIN SELECT * FROM users", True),
    ("WITH cte AS (SELECT 1) SELECT * FROM cte", True),
    ("UPDATE users SET name='x'", False),
    ("INSERT INTO users VALUES (1)", False),
    ("ALTER TABLE users ADD col INT", False),
]
all_pass = True
for q, expected in cases:
    result = s.is_safe(q)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] is_safe({q!r}) = {result} (expected {expected})")

print(f"\nSafety Agent: {'ALL PASS' if all_pass else 'SOME FAILED'}")

# --- OptimizationAgent tests ---
opt = OptimizationAgent()

# Test with sequential scan metrics
metrics_seq = {
    "raw_plan": "Seq Scan on orders\n",
    "has_sequential_scan": True,
    "has_index_scan": False,
}
q1 = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE o.status = 'pending'"
suggs = opt.optimize(q1, metrics_seq)
print(f"\nOptimization for JOIN query: {len(suggs)} suggestions")
for s in suggs:
    print(f"  - {s}")

# Test correlated subquery rewrite detection
q2 = "SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u"
suggs2 = opt.optimize(q2, {"has_sequential_scan": False})
print(f"\nOptimization for correlated subquery: {len(suggs2)} suggestions")
for s in suggs2:
    print(f"  - {s[:80]}...")

# Test LIKE with leading wildcard
q3 = "SELECT * FROM products WHERE name LIKE '%phone%'"
suggs3 = opt.optimize(q3, {"has_sequential_scan": True, "raw_plan": "Seq Scan on products\n"})
print(f"\nOptimization for LIKE wildcard: {len(suggs3)} suggestions")
for s in suggs3:
    print(f"  - {s}")

print("\nAll smoke tests completed.")
