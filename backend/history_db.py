import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime

# Define the DB path relative to this file
DB_PATH = os.path.join(os.path.dirname(__file__), "optimql_history.db")

def init_history_db():
    """Initializes the SQLite database table for query history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            original_query TEXT UNIQUE,
            suggested_query TEXT,
            improvement_pct REAL,
            confidence_score REAL,
            baseline_time_ms REAL,
            rows_scanned INTEGER,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_history(original_query: str, suggested_query: str, improvement_pct: float, 
                   confidence_score: float, baseline_time_ms: Optional[float], 
                   rows_scanned: Optional[int], details: str):
    """Inserts a new optimization result into the history table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # We use INSERT OR REPLACE to update existing entries for the same query to keep the most recent run 
    # instead of bloating the DB with duplicates.
    cursor.execute('''
        INSERT OR REPLACE INTO query_history 
        (original_query, suggested_query, improvement_pct, confidence_score, baseline_time_ms, rows_scanned, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (original_query, suggested_query, improvement_pct, confidence_score, baseline_time_ms, rows_scanned, details))
    
    conn.commit()
    conn.close()

def get_history(limit: int = 50) -> List[Dict]:
    """Retrieves the most recent history records."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM query_history 
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Convert sqlite3.Row objects to dictionaries
    return [dict(row) for row in rows]

def get_cached_result(original_query: str) -> Optional[Dict]:
    """Checks if we've already optimized this exact query recently."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM query_history 
        WHERE original_query = ?
        LIMIT 1
    ''', (original_query,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None
