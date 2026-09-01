#!/usr/bin/env python3
"""
ExpenseAI - Root Workspace Launcher
Forwards execution to INTERNSHIP_PROJECT_AI/run.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "INTERNSHIP_PROJECT_AI")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.chdir(PROJECT_DIR)

from run import main

if __name__ == "__main__":
    main()
