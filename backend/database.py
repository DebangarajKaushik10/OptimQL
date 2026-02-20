import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Main DB Connection
MAIN_DB_URL = os.getenv("MAIN_DB_URL", "postgresql://user:password@localhost:5432/main_db")
main_engine = create_engine(MAIN_DB_URL)
MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)

# Shadow DB Connection
SHADOW_DB_URL = os.getenv("SHADOW_DB_URL", "postgresql://user:password@localhost:5433/shadow_db")
shadow_engine = create_engine(SHADOW_DB_URL)
ShadowSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=shadow_engine)

Base = declarative_base()

def get_main_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_shadow_db():
    db = ShadowSessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_query(engine, query: str):
    """Utility to execute raw SQL and fetch results."""
    with engine.connect() as connection:
        result = connection.execute(text(query))
        connection.commit()
        if result.returns_rows:
            return result.fetchall()
        return None


def execute_autocommit(engine, query: str):
    """Execute a SQL statement in autocommit mode (useful for CREATE EXTENSION,
    or CREATE INDEX CONCURRENTLY in Postgres which require no surrounding
    transaction). Returns result.fetchall() when rows are returned, otherwise None.
    """
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        result = conn.execute(text(query))
        # No commit needed for autocommit mode
        if hasattr(result, 'returns_rows') and result.returns_rows:
            return result.fetchall()
        return None

def get_execution_plan(engine, query: str):
    """Utility to run EXPLAIN ANALYZE safely."""
    explain_query = f"EXPLAIN ANALYZE {query}"
    return execute_query(engine, explain_query)
