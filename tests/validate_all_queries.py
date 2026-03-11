"""
Comprehensive validation script for all OptimQL test queries.
Runs each query against the live /analyze endpoint and checks the response.
"""
import sys
import json
import requests

API = "http://localhost:8000/analyze"
PASS = 0
FAIL = 0

def test_query(name: str, query: str, checks: dict):
    global PASS, FAIL
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"QUERY: {query[:80]}{'...' if len(query) > 80 else ''}")
    try:
        r = requests.post(API, json={"query": query}, timeout=30)
        data = r.json()
        print(f"STATUS: {r.status_code}")
        print(f"RESPONSE: {json.dumps(data, indent=2)}")

        errors = []
        for key, expected in checks.items():
            actual = data.get(key)
            if callable(expected):
                if not expected(actual):
                    errors.append(f"  CHECK FAILED: {key} = {actual!r}")
            elif actual != expected:
                errors.append(f"  CHECK FAILED: {key} = {actual!r}, expected {expected!r}")

        if errors:
            FAIL += 1
            print(f"RESULT: FAIL")
            for e in errors:
                print(e)
        else:
            PASS += 1
            print(f"RESULT: PASS")

    except Exception as e:
        FAIL += 1
        print(f"RESULT: ERROR - {e}")


# ---- TEST 1: JOIN with WHERE filter ----
test_query(
    "JOIN with WHERE filter (index suggestion)",
    "SELECT u.name, o.total_amount FROM users u JOIN orders o ON o.user_id = u.id WHERE o.status = 'pending'",
    {
        "original_query": lambda v: "users" in v and "orders" in v,
        "suggested_query": lambda v: v != "N/A" and "INDEX" in v.upper(),
        "improvement_percentage": lambda v: v > 0,
        "confidence_score": lambda v: v > 0,
    },
)

# ---- TEST 2: SELECT * anti-pattern ----
test_query(
    "SELECT * anti-pattern",
    "SELECT * FROM users",
    {
        "original_query": "SELECT * FROM users",
        "confidence_score": lambda v: v > 0,
    },
)

# ---- TEST 3: LIKE with leading wildcard ----
test_query(
    "LIKE with leading wildcard (trigram index)",
    "SELECT * FROM products WHERE name LIKE '%phone%'",
    {
        "original_query": lambda v: "LIKE" in v or "like" in v,
        "suggested_query": lambda v: v != "N/A",
        "confidence_score": lambda v: v > 0,
    },
)

# ---- TEST 4: ILIKE with leading wildcard ----
test_query(
    "ILIKE case-insensitive wildcard",
    "SELECT * FROM products WHERE name ILIKE '%wireless%'",
    {
        "original_query": lambda v: "ILIKE" in v or "ilike" in v,
        "suggested_query": lambda v: v != "N/A",
        "confidence_score": lambda v: v > 0,
    },
)

# ---- TEST 5: Correlated subquery ----
test_query(
    "Correlated subquery (rewrite suggestion)",
    "SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u",
    {
        "original_query": lambda v: "COUNT" in v.upper(),
        "suggested_query": lambda v: v != "N/A",
        "confidence_score": lambda v: v > 0,
    },
)

# ---- TEST 6: Dangerous DROP TABLE ----
test_query(
    "Safety rejection: DROP TABLE",
    "DROP TABLE users",
    {
        "suggested_query": "N/A",
        "improvement_percentage": 0.0,
        "confidence_score": 0.0,
        "details": lambda v: "Safety Agent" in v,
    },
)

# ---- TEST 7: Multi-statement injection ----
test_query(
    "Safety rejection: multi-statement injection",
    "SELECT * FROM users; DROP TABLE users",
    {
        "suggested_query": "N/A",
        "improvement_percentage": 0.0,
        "confidence_score": 0.0,
        "details": lambda v: "Safety Agent" in v,
    },
)

# ---- TEST 8: Simple optimized query ----
test_query(
    "Simple optimized query (PK lookup)",
    "SELECT id, name FROM users WHERE id = 1",
    {
        "original_query": lambda v: "id = 1" in v,
        "confidence_score": lambda v: v >= 0,
    },
)

# ---- SUMMARY ----
print(f"\n{'='*60}")
print(f"SUMMARY: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print(f"{'='*60}")
sys.exit(0 if FAIL == 0 else 1)
