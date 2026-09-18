import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

# Define database file path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "expenses.db")


def ensure_db_dir_exists():
    """Ensure that the database directory exists."""
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional scope around a series of operations."""
    ensure_db_dir_exists()
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # High concurrency & performance
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables and indices if they do not exist."""
    ensure_db_dir_exists()
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Expenses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'UPI',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
        """)
        
        # 2. Budgets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL DEFAULT 'OVERALL',
                monthly_limit REAL NOT NULL CHECK (monthly_limit > 0),
                month INTEGER,
                year INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                UNIQUE(category, month, year)
            );
        """)
        
        # 3. Settings / Preferences Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        
        # Indices for optimal query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_payment ON expenses(payment_method);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount);")
        
        # Insert default settings if missing
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES
            ('currency_symbol', '₹'),
            ('currency_code', 'INR'),
            ('user_name', 'Alex'),
            ('monthly_budget', '35000'),
            ('theme', 'dark')
        """)
        
    print(f"[Database] SQLite schema verified at {DB_PATH}")


if __name__ == "__main__":
    init_db()
