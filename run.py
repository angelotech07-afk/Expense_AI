import os
import sys
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import init_db
from backend.seed_data import seed_database

def start_server():
    print("=" * 65)
    print("  🚀 ExpenseAI — AI-Powered Personal Expense Analysis System")
    print("  'Understand your spending. Make smarter decisions.'")
    print("=" * 65)
    
    # 1. Initialize SQLite Database
    print("\n[1/3] Initializing SQLite database schema...")
    init_db()
    
    # 2. Check and Seed Sample Data if clean
    print("[2/3] Checking dataset status...")
    seed_database(force=False)
    
    # 3. Launching Server
    print("[3/3] Starting FastAPI backend and serving frontend...")
    print("\n" + "—" * 65)
    print("  🌐 Web Dashboard:    http://127.0.0.1:8000")
    print("  📚 API Interactive:  http://127.0.0.1:8000/docs")
    print("  📊 API OpenAPI Spec: http://127.0.0.1:8000/openapi.json")
    print("—" * 65 + "\n")
    
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
