import os
import sys
import time
import socket
import threading
import webbrowser
import subprocess
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from backend.database import init_db
from backend.seed_data import seed_database

HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}"


def is_server_running(host: str = HOST, port: int = PORT) -> bool:
    """Check if the backend server is already running and accepting connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.8)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def open_browser_when_ready(url: str = APP_URL, timeout: float = 8.0):
    """Wait for server to accept connections, then open browser automatically."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_server_running():
            time.sleep(0.3)
            webbrowser.open(url)
            return
        time.sleep(0.25)
    # Fallback open even if port check timed out
    webbrowser.open(url)


def kill_process_on_port(port: int = PORT):
    """Safely terminate existing process on the given port (Windows compatible)."""
    try:
        cmd = f'powershell -Command "(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue).OwningProcess"'
        out = subprocess.check_output(cmd, shell=True).decode().strip()
        for pid_str in out.split():
            if pid_str.isdigit():
                pid = int(pid_str)
                os.system(f"taskkill /PID {pid} /F >nul 2>&1")
        time.sleep(1)
    except Exception as e:
        print(f"[Warning] Could not terminate process on port {port}: {e}")


def start_server(force_restart: bool = False):
    print("=" * 65)
    print("  🚀 ExpenseAI — AI-Powered Personal Expense Analysis System")
    print("  'Understand your spending. Make smarter decisions.'")
    print("=" * 65)

    if force_restart:
        print(f"\n[Restart] Stopping existing server on port {PORT}...")
        kill_process_on_port(PORT)

    # Prevent duplicate backend processes
    if is_server_running():
        print(f"\n[INFO] ExpenseAI server is ALREADY running at {APP_URL}")
        print("[INFO] Duplicate backend process prevented.")
        print(f"[INFO] Opening dashboard in your default browser: {APP_URL}\n")
        webbrowser.open(APP_URL)
        return

    # 1. Initialize SQLite Database
    print("\n[1/3] Initializing SQLite database schema...")
    init_db()

    # 2. Check and Seed Sample Data if clean
    print("[2/3] Checking dataset status...")
    seed_database(force=False)

    # 3. Launching Server
    print("[3/3] Starting FastAPI backend and serving frontend...")
    print("\n" + "—" * 65)
    print(f"  🌐 Web Dashboard:    {APP_URL}")
    print(f"  📚 API Interactive:  {APP_URL}/docs")
    print(f"  📊 API OpenAPI Spec: {APP_URL}/openapi.json")
    print("—" * 65 + "\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser_when_ready, args=(APP_URL,), daemon=True).start()

    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=True)


if __name__ == "__main__":
    restart = "--restart" in sys.argv or "-r" in sys.argv
    start_server(force_restart=restart)
