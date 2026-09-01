#!/usr/bin/env python3
"""
ExpenseAI - Quick Application Launcher
Starts the Flask server and serves the modern frontend and REST API on http://127.0.0.1:8000
"""

import os
import sys
import webbrowser
from threading import Timer

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import app
from backend.database import init_db
from backend.seed_data import seed_demo_data


def open_browser(port):
    url = f"http://127.0.0.1:{port}"
    print(f"✨ Opening ExpenseAI in browser: {url}")
    webbrowser.open(url)


def main():
    port = int(os.environ.get("PORT", 8000))
    
    # Initialize DB schema
    init_db()
    
    # Check if database has any expenses, if empty seed initial demo data for instant delight
    from backend.database import fetch_one
    count_row = fetch_one("SELECT COUNT(*) as count FROM expenses")
    if not count_row or count_row["count"] == 0:
        print("🌱 Populating initial realistic demo dataset (Indian Rupee ₹)...")
        seed_demo_data(clear_existing=False)

    print("=" * 65)
    print("  🚀 ExpenseAI — AI-Powered Personal Expense Analysis System")
    print("  📍 Server URL : http://127.0.0.1:" + str(port))
    print("  📊 Dashboard  : http://127.0.0.1:" + str(port) + "/#dashboard")
    print("  🧠 AI Engine  : Dual-Engine Active (Local Statistical + Gemini)")
    print("=" * 65)
    
    # Automatically open browser after 1 second if not in headless mode
    if os.environ.get("NO_BROWSER") != "1":
        Timer(1.2, open_browser, args=[port]).start()
        
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
