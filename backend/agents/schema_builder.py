import re
from backend.database import execute_query

class SchemaBuilderAgent:
    """
    Dynamically creates dummy tables based on extracted table/column names from query.
    Enables optimization of arbitrary queries without pre-existing schema.
    """

    def __init__(self):
        pass

    def extract_schema(self, query: str) -> dict:
        """
        Extract table names and infer columns from query.
        Returns: {"table1": {"col1": "type1", "col2": "type2"}, ...}
        """
        schema = {}
        alias_to_table = {}

        sql_keywords = {
            "as", "and", "or", "not", "in", "is", "like", "between", "where",
            "from", "join", "on", "group", "by", "order", "having", "limit",
            "count", "avg", "sum", "min", "max", "distinct", "select"
        }

        # Extract base tables and aliases: FROM users u, JOIN orders AS o ...
        table_pattern = r"\b(?:FROM|JOIN)\s+([A-Za-z0-9_\.]+)(?:\s+(?:AS\s+)?([A-Za-z0-9_]+))?"
        tables = re.findall(table_pattern, query, re.IGNORECASE)
        for table_ref, alias in tables:
            table_name = table_ref.split('.')[-1].lower()
            schema.setdefault(table_name, {})
            alias_to_table[table_name] = table_name
            if alias:
                alias_to_table[alias.lower()] = table_name

        def add_column_reference(col_ref: str) -> None:
            col_ref = col_ref.strip()
            if not col_ref:
                return

            col_lower = col_ref.lower()
            if col_lower in sql_keywords or col_lower == "*":
                return

            if '.' in col_ref:
                left, col_name = col_ref.split('.', 1)
                table_name = alias_to_table.get(left.lower(), left.lower())
            else:
                # Assign unqualified columns to first extracted table.
                if not schema:
                    return
                table_name = next(iter(schema.keys()))
                col_name = col_ref

            col_name = col_name.strip().lower()
            if not col_name or col_name in sql_keywords:
                return

            schema.setdefault(table_name, {})
            schema[table_name][col_name] = self._infer_type(col_name)

        # Extract table-qualified and unqualified identifiers from query.
        token_pattern = r"\b([A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*|[A-Za-z_][A-Za-z0-9_]*)\b"
        for token in re.findall(token_pattern, query):
            add_column_reference(token)

        # Ensure each table has at least one non-PK column so EXPLAIN can run join/filter conditions.
        for table_name, cols in schema.items():
            if not cols:
                cols["dummy_col"] = "VARCHAR(255)"

        return schema

    def _infer_type(self, col_name: str) -> str:
        """Heuristic type inference based on column name."""
        col_lower = col_name.lower()
        
        if any(x in col_lower for x in ["id", "count", "number", "qty", "amount", "salary", "price", "total"]):
            return "INTEGER"
        if any(x in col_lower for x in ["date", "time", "created", "updated", "hire"]):
            return "TIMESTAMP"
        if any(x in col_lower for x in ["email", "phone", "address", "url", "text", "description", "name", "title", "status"]):
            return "VARCHAR(255)"
        if any(x in col_lower for x in ["salary", "price", "amount", "total", "cost", "rate"]):
            return "DECIMAL(10,2)"
        
        return "VARCHAR(255)"  # default

    def create_dummy_tables(self, schema: dict, engine) -> bool:
        """Create dummy tables in the specified engine."""
        try:
            # Drop existing tables first (reverse order to respect FKs)
            table_names = list(schema.keys())
            for table_name in reversed(table_names):
                drop_sql = f"DROP TABLE IF EXISTS {table_name} CASCADE"
                execute_query(engine, drop_sql)
            
            # Create tables
            for table_name, columns in schema.items():
                col_defs = ["id SERIAL PRIMARY KEY"]
                for col_name, col_type in columns.items():
                    if col_name != "id":
                        col_defs.append(f"{col_name} {col_type}")
                
                create_sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
                execute_query(engine, create_sql)
            
            # Seed tables with dummy data
            self._seed_dummy_data(schema, engine)
            return True
            
        except Exception as e:
            print(f"Error creating dummy tables: {e}")
            return False

    def _seed_dummy_data(self, schema: dict, engine) -> None:
        """Insert sample data into created tables."""
        try:
            for table_name, columns in schema.items():
                # Create sample data based on column types
                col_names = [c for c in columns.keys() if c != "id"]
                if not col_names:
                    col_names = []
                
                sample_values = []
                for i in range(5):  # 5 sample rows per table
                    row_values = []
                    for col_name, col_type in columns.items():
                        if col_name == "id":
                            continue
                        if "TIMESTAMP" in col_type:
                            row_values.append(f"'2023-{(i % 12) + 1:02d}-{(i % 25) + 1:02d}'::TIMESTAMP")
                        elif "DECIMAL" in col_type or "INTEGER" in col_type:
                            row_values.append(str(1000 + i * 100))
                        else:  # VARCHAR
                            row_values.append(f"'sample_{col_name}_{i}'")
                    
                    sample_values.append(f"({', '.join(row_values)})")
                
                if sample_values and col_names:
                    col_str = ', '.join(col_names)
                    insert_sql = f"INSERT INTO {table_name} ({col_str}) VALUES {', '.join(sample_values)}"
                    execute_query(engine, insert_sql)
        
        except Exception as e:
            print(f"Warning: Could not seed data: {e}")
