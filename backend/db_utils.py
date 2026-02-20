import logging
from backend.database import execute_query, get_main_db, main_engine, get_shadow_db, shadow_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_connection(engine, db_name: str) -> bool:
    """Test if we can connect to a given database engine."""
    try:
        result = execute_query(engine, "SELECT 1")
        if result and result[0][0] == 1:
            logger.info(f"Successfully connected to {db_name}.")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to connect to {db_name}: {e}")
        return False

def init_dummy_data():
    """Seed the Main DB and Shadow DB with dummy e-commerce data for testing."""
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE
    );
    
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(id),
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10, 2),
        status VARCHAR(20)
    );
    
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(200) UNIQUE,
        description TEXT,
        price DECIMAL(10,2)
    );
    """
    
    # We deliberately omit indexes here so the AI can suggest them later.
    
    try:
        # Create schema in Main DB
        execute_query(main_engine, schema_sql)
        # Create schema in Shadow DB
        execute_query(shadow_engine, schema_sql)
        
        logger.info("Dummy schema initialized in both Main and Shadow DBs.")
        
        # Insert a few dummy records into Main DB
        insert_sql = """
        INSERT INTO users (name, email) VALUES 
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com')
        ON CONFLICT DO NOTHING;
        
        INSERT INTO orders (user_id, total_amount, status) VALUES 
        (1, 100.50, 'completed'),
        (2, 200.00, 'pending');
        
    INSERT INTO products (name, description, price) VALUES
    ('Smartphone X', 'A powerful smartphone', 699.99),
    ('Phone Case', 'Durable protective case', 19.99),
    ('Wireless Headset', 'Noise cancelling headset', 129.99)
    ON CONFLICT DO NOTHING;
        """
        execute_query(main_engine, insert_sql)
        # Mirror to Shadow DB
        execute_query(shadow_engine, insert_sql)
        
        logger.info("Dummy data inserted.")
        
    except Exception as e:
        logger.error(f"Error initializing dummy data: {e}")

if __name__ == "__main__":
    if test_db_connection(main_engine, "Main DB") and test_db_connection(shadow_engine, "Shadow DB"):
        init_dummy_data()
