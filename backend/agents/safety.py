import re

class SafetyAgent:
    """
    Agent 1: Safety Agent
    Checks if a query is safe to analyze (e.g., blocks DROP, DELETE, UPDATE, INSERT, ALTER).
    """

    def __init__(self):
        # Patterns to flag dangerous operations or SQL injection attempts
        self.dangerous_patterns = [
            r"\bDROP\b",
            r"\bDELETE\b",
            r"\bUPDATE\b",
            r"\bINSERT\b",
            r"\bALTER\b",
            r"\bTRUNCATE\b",
            r"\bGRANT\b",
            r"\bREVOKE\b",
            r"\bEXEC\b",
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.dangerous_patterns]

    def _has_semicolon_outside_quotes(self, s: str) -> bool:
        """Return True if there's a semicolon outside of any single/double quotes.

        This is a lightweight check to avoid rejecting queries that include
        semicolons inside string literals (e.g. punctuation inside text).
        It does not perform full SQL parsing but is sufficient for our safety
        needs here.
        """
        in_single = False
        in_double = False
        in_dollar = None  # holds the delimiter like $tag$
        in_block_comment = False
        i = 0
        L = len(s)
        while i < L:
            # Handle block comments /* ... */
            if not in_single and not in_double and not in_dollar and s.startswith("/*", i):
                end = s.find("*/", i + 2)
                if end == -1:
                    return False
                i = end + 2
                continue

            # Handle line comments -- until end of line
            if not in_single and not in_double and not in_dollar and s.startswith("--", i):
                nl = s.find("\n", i + 2)
                if nl == -1:
                    break
                i = nl + 1
                continue

            ch = s[i]

            # Dollar-quoted string e.g. $tag$ ... $tag$
            if ch == "$" and not in_single and not in_double:
                m = re.match(r"\$[A-Za-z0-9_]*\$", s[i:])
                if m:
                    delim = m.group(0)
                    # find closing delimiter
                    end = s.find(delim, i + len(delim))
                    if end == -1:
                        # unterminated dollar-quote; be conservative and treat as safe
                        return False
                    i = end + len(delim)
                    continue

            if ch == "'" and not in_double and in_dollar is None:
                # handle doubled single-quote escaping by skipping next char
                if in_single and i + 1 < L and s[i + 1] == "'":
                    i += 2
                    continue
                in_single = not in_single
                i += 1
                continue

            if ch == '"' and not in_single and in_dollar is None:
                if in_double and i + 1 < L and s[i + 1] == '"':
                    i += 2
                    continue
                in_double = not in_double
                i += 1
                continue

            if ch == ";" and not in_single and not in_double and in_dollar is None:
                return True

            i += 1

        return False

    def is_safe(self, query: str) -> bool:
        """Returns True if the query appears safe, False otherwise."""
        # Normalize input: strip surrounding whitespace and allow a single
        # trailing semicolon (users often paste queries that end with `;`).
        q = query.strip()
        if q.endswith(";"):
            # remove only one trailing semicolon so embedded/multiple
            # semicolons (indicating multiple statements) are still detected
            # by the dangerous pattern checks below.
            q = q[:-1].strip()
        # If there is a semicolon outside of any quoted literal, treat as
        # a potential multi-statement and reject.
        if self._has_semicolon_outside_quotes(q):
            return False

        for pattern in self.compiled_patterns:
            if pattern.search(q):
                return False
        
        # Ensure it's strictly a SELECT or EXPLAIN statement
        if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", q, re.IGNORECASE):
            return False

        return True
