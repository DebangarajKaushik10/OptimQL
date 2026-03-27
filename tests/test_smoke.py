"""Smoke tests for safety and optimization agents (no database required)."""
import pytest
from backend.agents.safety import SafetyAgent
from backend.agents.optimization import OptimizationAgent


# --- SafetyAgent tests ---

class TestSafetyAgent:
    """Verify the SafetyAgent correctly classifies safe and unsafe queries."""

    @pytest.fixture()
    def agent(self):
        return SafetyAgent()

    @pytest.mark.parametrize(
        "query, expected",
        [
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
        ],
    )
    def test_is_safe(self, agent, query, expected):
        assert agent.is_safe(query) == expected, f"is_safe({query!r}) should be {expected}"


# --- OptimizationAgent tests ---

class TestOptimizationAgent:
    """Verify the OptimizationAgent produces sensible suggestions."""

    @pytest.fixture()
    def agent(self):
        return OptimizationAgent()

    def test_join_query_with_seq_scan(self, agent):
        """Index suggestions should be produced for JOIN queries with seq scan."""
        metrics = {
            "raw_plan": "Seq Scan on orders\n",
            "has_sequential_scan": True,
            "has_index_scan": False,
        }
        query = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE o.status = 'pending'"
        suggestions = agent.optimize(query, metrics)
        assert len(suggestions) > 0, "Expected at least one suggestion"
        # Should include an index suggestion
        assert any("CREATE INDEX" in s.upper() for s in suggestions), \
            "Expected at least one CREATE INDEX suggestion"

    def test_correlated_subquery_rewrite(self, agent):
        """Correlated COUNT(*) subquery should trigger a rewrite suggestion."""
        query = "SELECT u.name, (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS order_count FROM users u"
        suggestions = agent.optimize(query, {"has_sequential_scan": False})
        assert len(suggestions) > 0, "Expected at least one suggestion"
        assert any("JOIN" in s.upper() or "Rewrite" in s for s in suggestions), \
            "Expected a rewrite / JOIN suggestion for correlated subquery"

    def test_like_leading_wildcard(self, agent):
        """LIKE '%...%' with leading wildcard should suggest a trigram index."""
        query = "SELECT * FROM products WHERE name LIKE '%phone%'"
        metrics = {
            "has_sequential_scan": True,
            "raw_plan": "Seq Scan on products\n",
        }
        suggestions = agent.optimize(query, metrics)
        assert len(suggestions) > 0, "Expected at least one suggestion"
        # Should include a trigram index or SELECT * warning
        assert any("trgm" in s.lower() or "SELECT *" in s for s in suggestions), \
            "Expected a trigram index suggestion or SELECT * warning"

    def test_select_star_warning(self, agent):
        """SELECT * should trigger a warning about specifying columns."""
        query = "SELECT * FROM users"
        metrics = {"has_sequential_scan": False}
        suggestions = agent.optimize(query, metrics)
        assert any("SELECT *" in s or "columns" in s.lower() for s in suggestions), \
            "Expected a SELECT * anti-pattern warning"
