@echo off
title ExpenseAI — AI-Powered Personal Expense Analysis System
echo =========================================================================
echo    ExpenseAI — Personal Expense Analysis ^& Financial Intelligence
echo =========================================================================
echo.
echo Installing/Verifying dependencies...
python -m pip install -r backend\requirements.txt --quiet
echo.
echo Starting ExpenseAI Server on http://127.0.0.1:8000 ...
python run.py
pause
