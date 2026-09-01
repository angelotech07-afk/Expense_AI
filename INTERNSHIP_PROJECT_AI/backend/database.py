"""
ExpenseAI - Database Layer
Provides SQLite database connection management, schema initialization, and helper functions.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Default DB Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "expenses.db")


def get_db_path() -> str:
    """Ensure database directory exists and return absolute path."""
    os.makedirs(DB_DIR, exist_ok=True)
    return DB_PATH


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a SQLite connection configured with row factories and foreign keys."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables, indexes, and default settings."""
    target_path = db_path or get_db_path()
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        
        # Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL, -- Format: YYYY-MM-DD
                payment_method TEXT DEFAULT 'UPI',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Budgets table (monthly overall or category specific)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK (year >= 2000),
                category TEXT NOT NULL DEFAULT 'ALL',
                amount REAL NOT NULL CHECK (amount >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(month, year, category)
            );
        """)
        
        # App Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_lookup ON budgets(year, month, category);")
        
        # Default Settings if missing
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES 
            ('currency_symbol', '₹'),
            ('currency_code', 'INR'),
            ('currency_name', 'Indian Rupee'),
            ('theme', 'dark'),
            ('ai_provider', 'local'),
            ('gemini_api_key', '')
        """)
        
        conn.commit()


def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """Execute write query and return lastrowid or affected rows."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def fetch_all(query: str, params: tuple = (), db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Execute select query and return list of dictionaries."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def fetch_one(query: str, params: tuple = (), db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Execute select query and return single dictionary or None."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
