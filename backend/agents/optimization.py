import re
import logging

logger = logging.getLogger(__name__)

class OptimizationAgent:
    """
    Agent 3: Optimization Agent
    Suggests improvements like indexes or rewrites based on rule-based logic.
    Detects WHERE, JOIN, and ORDER BY columns for targeted index suggestions.
    """

    def optimize(self, query: str, analysis_metrics: dict) -> list[str]:
        suggestions = []

        # Detect correlated COUNT(*) subquery patterns and suggest a JOIN+GROUP rewrite
        rewrite = self._suggest_rewrite_for_correlated_count_subquery(query)
        if rewrite:
            suggestions.append(rewrite)

        # Detect LIKE patterns with leading wildcard (e.g. '%phone%') and suggest trigram/index
        # match LIKE or ILIKE (case-insensitive). capture leading-wildcard patterns like '%phone%'
        for match in re.finditer(r"(?:(\w+)\.)?(\w+)\s+(?:I?LIKE)\s+'(%.*%)'", query, re.IGNORECASE):
            tbl_alias = match.group(1)
            col = match.group(2)
            like_pattern = match.group(3)
            # Only suggest trigram for leading wildcard patterns
            if like_pattern.startswith("%"):
                # Resolve table name from alias mapping or FROM clause
                table = None
                # try alias_map later (we'll compute alias_map now if necessary)
                # store candidate to process after alias_map is available
                # we'll add suggestion after building alias_map below
                pass

        # Extract table aliases mapping: alias -> table_name
        alias_map = self._extract_aliases(query)

        # Now retry detection of LIKE leading-wildcard patterns to generate index suggestions
        for match in re.finditer(r"(?:(\w+)\.)?(\w+)\s+(?:I?LIKE)\s+'(%.*%)'", query, re.IGNORECASE):
            tbl_alias = match.group(1)
            col = match.group(2)
            like_pattern = match.group(3)
            if like_pattern.startswith("%"):
                if tbl_alias:
                    table = alias_map.get(tbl_alias, tbl_alias)
                else:
                    # Try to find a single table in FROM clause
                    table = self._find_primary_table(query)
                if table:
                    idx_name = f"idx_{table}_{col}_trgm"
                    suggestion = (
                        f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {idx_name} ON {table} USING gin ({col} gin_trgm_ops)"
                    )
                    # Add a short human-friendly note as well
                    suggestions.append(suggestion)

        # Rule 1: If sequential scan detected, suggest indexes on filtered/joined columns
        if analysis_metrics.get("has_sequential_scan"):
            # Find columns used in WHERE clauses
            where_cols = self._extract_where_columns(query)
            # Find columns used in JOIN ON clauses
            join_cols = self._extract_join_columns(query)
            # Find columns used in ORDER BY
            order_cols = self._extract_orderby_columns(query)

            target_cols = where_cols + join_cols + order_cols
            seen = set()

            for table_or_alias, column in target_cols:
                # Resolve alias to real table name
                table = alias_map.get(table_or_alias, table_or_alias)
                key = f"{table}.{column}"
                if key in seen or column.lower() == "id":
                    continue
                seen.add(key)
                idx_name = f"idx_{table}_{column}"
                suggestions.append(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({column})"
                )

            # Fallback: if we found seq scan but couldn't parse columns, suggest generic
            if not suggestions:
                raw_plan = analysis_metrics.get("raw_plan", "")
                # Try to extract table name from the seq scan line in the plan
                scan_match = re.search(r"Seq Scan on (\w+)", raw_plan)
                if scan_match:
                    table = scan_match.group(1)
                    where_simple = self._extract_simple_where_column(query, table, alias_map)
                    if where_simple:
                        idx_name = f"idx_{table}_{where_simple}"
                        suggestions.append(
                            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({where_simple})"
                        )

        # Rule 2: Rewrite IN/NOT IN as EXISTS or JOIN
        if "IN (" in query.upper() or "NOT IN (" in query.upper():
            suggestions.append(
                "Consider rewriting IN/NOT IN clauses using EXISTS or JOINs for better performance."
            )

        # Rule 3: SELECT * is usually wasteful
        if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
            suggestions.append(
                "Avoid SELECT *; specify only the columns you need to reduce I/O."
            )

        if not suggestions:
            suggestions.append(
                "Query looks reasonably optimized based on basic heuristics."
            )

        logger.info(f"Optimization suggestions: {suggestions}")
        return suggestions

    def _suggest_rewrite_for_correlated_count_subquery(self, query: str) -> str | None:
        """Detect a simple correlated COUNT(*) subquery and return a JOIN+GROUP rewrite suggestion.

        This is intentionally conservative and matches common patterns like:
        SELECT ..., (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS cnt
        FROM users u;
        """
        # Use a regex to capture key parts: outer select projection, inner table/alias, join columns, outer table/alias
        pattern = re.compile(
            r"SELECT\s+(?P<outer_select>.+?),\s*\(\s*SELECT\s+COUNT\(\*\)\s+FROM\s+(?P<inner_table>\w+)\s+(?P<inner_alias>\w+)\s+WHERE\s+(?P=inner_alias)\.(?P<inner_col>\w+)\s*=\s*(?P<outer_alias>\w+)\.(?P<outer_col>\w+)\s*\)\s+AS\s+(?P<alias>\w+)\s+FROM\s+(?P<outer_table>\w+)\s+(?P=outer_alias)",
            re.IGNORECASE | re.DOTALL,
        )

        m = pattern.search(query)
        if not m:
            return None

        outer_select = m.group("outer_select").strip()
        inner_table = m.group("inner_table")
        inner_alias = m.group("inner_alias")
        inner_col = m.group("inner_col")
        outer_table = m.group("outer_table")
        outer_alias = m.group("outer_alias")
        outer_col = m.group("outer_col")
        alias = m.group("alias")

        # Build a readable rewrite suggestion
        rewrite = (
            "Rewrite using a LEFT JOIN + aggregated subquery to avoid the correlated subquery:\n"
            f"SELECT {outer_select}, COALESCE(o.{alias}, 0) AS {alias}\n"
            f"FROM {outer_table} {outer_alias}\n"
            f"LEFT JOIN (\n"
            f"  SELECT {inner_alias}.{inner_col} AS {inner_col}, COUNT(*) AS {alias}\n"
            f"  FROM {inner_table} {inner_alias}\n"
            f"  GROUP BY {inner_alias}.{inner_col}\n"
            f") o ON o.{inner_col} = {outer_alias}.{outer_col};"
        )

        return rewrite

    def _extract_aliases(self, query: str) -> dict:
        """Extract table alias mappings: alias -> real_table_name."""
        alias_map = {}
        # Match patterns like: FROM users u, JOIN orders o, FROM users AS u
        for match in re.finditer(
            r"(?:FROM|JOIN)\s+(\w+)(?:\s+AS)?\s+(\w+)", query, re.IGNORECASE
        ):
            table, alias = match.group(1), match.group(2)
            # Skip SQL keywords that look like aliases
            if alias.upper() not in (
                "ON", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
                "CROSS", "GROUP", "ORDER", "HAVING", "LIMIT", "SET",
            ):
                alias_map[alias] = table
                alias_map[table] = table  # table maps to itself too
        # Also capture simple FROM <table> without explicit alias
        for match in re.finditer(r"FROM\s+(\w+)(?:\s+AS\s+(\w+))?", query, re.IGNORECASE):
            table = match.group(1)
            alias = match.group(2)
            alias_map[table] = table
            if alias:
                alias_map[alias] = table
        return alias_map

    def _find_primary_table(self, query: str) -> str | None:
        """Return the first table name found in FROM clause when no alias is used."""
        m = re.search(r"FROM\s+(\w+)(?:\s+AS\s+\w+)?", query, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    def _extract_where_columns(self, query: str) -> list[tuple[str, str]]:
        """Extract (table_or_alias, column) pairs from WHERE clause."""
        cols = []
        # Match: alias.column = 'value' or alias.column = value
        for match in re.finditer(
            r"WHERE\s+.*?(\w+)\.(\w+)\s*=", query, re.IGNORECASE
        ):
            cols.append((match.group(1), match.group(2)))
        # Also match: WHERE column = 'value' (no alias)
        where_match = re.search(r"WHERE\s+(.*?)(?:GROUP|ORDER|LIMIT|HAVING|$)", query, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_body = where_match.group(1)
            for m in re.finditer(r"(\w+)\.(\w+)\s*(?:=|<|>|LIKE|IN|IS)", where_body, re.IGNORECASE):
                pair = (m.group(1), m.group(2))
                if pair not in cols:
                    cols.append(pair)
        return cols

    def _extract_join_columns(self, query: str) -> list[tuple[str, str]]:
        """Extract (table_or_alias, column) pairs from JOIN ON clauses."""
        cols = []
        for match in re.finditer(
            r"ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)", query, re.IGNORECASE
        ):
            cols.append((match.group(1), match.group(2)))
            cols.append((match.group(3), match.group(4)))
        return cols

    def _extract_orderby_columns(self, query: str) -> list[tuple[str, str]]:
        """Extract (table_or_alias, column) pairs from ORDER BY."""
        cols = []
        for match in re.finditer(
            r"ORDER\s+BY\s+.*?(\w+)\.(\w+)", query, re.IGNORECASE
        ):
            cols.append((match.group(1), match.group(2)))
        return cols

    def _extract_simple_where_column(self, query: str, table: str, alias_map: dict) -> str | None:
        """Fallback: try to find a WHERE column for a specific table."""
        # Find the alias for this table
        reverse_map = {v: k for k, v in alias_map.items() if k != v}
        alias = reverse_map.get(table, table)
        match = re.search(
            rf"{re.escape(alias)}\.(\w+)\s*(?:=|<|>|LIKE|IN|IS)", query, re.IGNORECASE
        )
        if match and match.group(1).lower() != "id":
            return match.group(1)
        return None
