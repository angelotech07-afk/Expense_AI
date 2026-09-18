import os
import io
import csv
from datetime import datetime, date
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from backend.database import get_db, init_db
from backend.models import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse,
    BudgetCreate, BudgetResponse, SettingsUpdate,
    SummaryStatsResponse, MonthlyBreakdownResponse, CategoryBreakdownResponse,
    DailyDataPoint, WhereMoneyGoesResponse, AIInsightsResponse,
    HealthScoreResponse, PredictionResponse
)
from backend.analytics import (
    get_summary_stats, get_monthly_breakdown, get_category_breakdown,
    get_daily_trend, get_where_money_goes, get_setting
)
from backend.ai_analysis import (
    generate_ai_insights, calculate_expense_health_score, calculate_prediction
)
from backend.seed_data import seed_database, clear_database

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="ExpenseAI API",
    description="AI-Powered Personal Expense Analysis System REST API",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 1. EXPENSE CRUD ENDPOINTS
# ==========================================

@app.post("/api/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(expense: ExpenseCreate):
    """Add a new expense to the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO expenses (amount, category, description, date, payment_method, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            round(expense.amount, 2),
            expense.category.strip(),
            expense.description.strip(),
            expense.date,
            expense.payment_method or "UPI",
            expense.notes.strip() if expense.notes else "",
            now_str,
            now_str
        ))
        expense_id = cursor.lastrowid
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        return dict(row)


@app.get("/api/expenses", response_model=ExpenseListResponse)
def get_expenses(
    search: Optional[str] = Query(None, description="Search term in description or notes"),
    category: Optional[str] = Query(None, description="Filter by category"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    start_date: Optional[str] = Query(None, description="Filter start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Filter end date YYYY-MM-DD"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month number (1-12)"),
    year: Optional[int] = Query(None, description="Filter by year (e.g. 2026)"),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("date", pattern="^(date|amount|category|description|id)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=5000)
):
    """Retrieve filtered and sorted list of expenses with pagination."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        where_clauses = ["1=1"]
        params = []
        
        if search:
            where_clauses.append("(description LIKE ? OR notes LIKE ? OR category LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term, term])
            
        if category and category != "ALL":
            where_clauses.append("category = ?")
            params.append(category)
            
        if payment_method and payment_method != "ALL":
            where_clauses.append("payment_method = ?")
            params.append(payment_method)
            
        if start_date:
            where_clauses.append("date >= ?")
            params.append(start_date)
            
        if end_date:
            where_clauses.append("date <= ?")
            params.append(end_date)
            
        if month:
            where_clauses.append("CAST(strftime('%m', date) AS INTEGER) = ?")
            params.append(month)
            
        if year:
            where_clauses.append("CAST(strftime('%Y', date) AS INTEGER) = ?")
            params.append(year)
            
        if min_amount is not None:
            where_clauses.append("amount >= ?")
            params.append(min_amount)
            
        if max_amount is not None:
            where_clauses.append("amount <= ?")
            params.append(max_amount)
            
        where_sql = " AND ".join(where_clauses)
        
        # Count total matches & sum
        count_query = f"SELECT COUNT(id) AS total_count, COALESCE(SUM(amount), 0) AS total_amount FROM expenses WHERE {where_sql}"
        cursor.execute(count_query, params)
        count_row = cursor.fetchone()
        total_count = int(count_row["total_count"])
        total_amount = float(count_row["total_amount"])
        
        # Query items
        offset = (page - 1) * page_size
        items_query = f"""
            SELECT id, amount, category, description, date, payment_method, notes, created_at, updated_at
            FROM expenses
            WHERE {where_sql}
            ORDER BY {sort_by} {sort_order.upper()}, id DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(items_query, params + [page_size, offset])
        items = [dict(r) for r in cursor.fetchall()]
        
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        
        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_amount": total_amount
        }


@app.get("/api/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int):
    """Retrieve a single expense by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense not found")
        return dict(row)


@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, expense: ExpenseUpdate):
    """Update an existing expense."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Expense not found")
            
        update_fields = []
        params = []
        
        if expense.amount is not None:
            update_fields.append("amount = ?")
            params.append(round(expense.amount, 2))
        if expense.category is not None:
            update_fields.append("category = ?")
            params.append(expense.category.strip())
        if expense.description is not None:
            update_fields.append("description = ?")
            params.append(expense.description.strip())
        if expense.date is not None:
            update_fields.append("date = ?")
            params.append(expense.date)
        if expense.payment_method is not None:
            update_fields.append("payment_method = ?")
            params.append(expense.payment_method)
        if expense.notes is not None:
            update_fields.append("notes = ?")
            params.append(expense.notes.strip())
            
        if update_fields:
            update_fields.append("updated_at = ?")
            params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            params.append(expense_id)
            sql = f"UPDATE expenses SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(sql, params)
            
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        return dict(cursor.fetchone())


@app.delete("/api/expenses/{expense_id}", status_code=200)
def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"success": True, "message": f"Expense #{expense_id} deleted successfully"}


# ==========================================
# 2. ANALYTICS ENDPOINTS
# ==========================================

@app.get("/api/analytics/summary", response_model=SummaryStatsResponse)
def get_summary():
    """Get high-level summary cards (Total, This Month, Daily Avg, Highest, Top Cat, Count)."""
    with get_db() as conn:
        return get_summary_stats(conn)


@app.get("/api/analytics/monthly", response_model=MonthlyBreakdownResponse)
def get_monthly(year: Optional[int] = None):
    """Get month-by-month spending analysis for a specific year (default: current year)."""
    target_year = year or date.today().year
    with get_db() as conn:
        return get_monthly_breakdown(conn, target_year)


@app.get("/api/analytics/categories", response_model=CategoryBreakdownResponse)
def get_categories(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Get spending grouped by category with percentages and averages."""
    with get_db() as conn:
        return get_category_breakdown(conn, start_date, end_date, month, year)


@app.get("/api/analytics/daily", response_model=List[DailyDataPoint])
def get_daily(
    days: int = Query(30, ge=7, le=365),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get daily spending time-series for charts."""
    with get_db() as conn:
        return get_daily_trend(conn, days, start_date, end_date)


@app.get("/api/analytics/where-money-goes", response_model=WhereMoneyGoesResponse)
def get_money_destinations():
    """Identify highest individual expense, top category, peak day, and peak month."""
    with get_db() as conn:
        return get_where_money_goes(conn)


# ==========================================
# 3. AI INSIGHTS, HEALTH SCORE & PREDICTION
# ==========================================

@app.get("/api/ai/insights", response_model=AIInsightsResponse)
def get_insights():
    """Get AI generated insights: patterns, alerts, positive feedback, anomalies."""
    with get_db() as conn:
        insights = generate_ai_insights(conn)
        return {
            "insights": insights,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "rule_statistical"
        }


@app.get("/api/ai/health-score", response_model=HealthScoreResponse)
def get_health_score():
    """Calculate Expense Health Score (0-100) with rating and factor breakdown."""
    with get_db() as conn:
        return calculate_expense_health_score(conn)


@app.get("/api/ai/prediction", response_model=PredictionResponse)
def get_prediction():
    """Calculate end-of-month spending forecast based on daily velocity."""
    with get_db() as conn:
        return calculate_prediction(conn)


# ==========================================
# 4. BUDGET & GOALS ENDPOINTS
# ==========================================

@app.get("/api/budget", response_model=BudgetResponse)
def get_budget():
    """Get current month's budget tracking and limit status."""
    with get_db() as conn:
        cursor = conn.cursor()
        today = date.today()
        curr_month_str = f"{today.year:04d}-{today.month:02d}"
        
        # Check budget setting
        cursor.execute("SELECT value FROM settings WHERE key = 'monthly_budget'")
        b_row = cursor.fetchone()
        monthly_limit = float(b_row["value"]) if (b_row and b_row["value"]) else 35000.0
        
        # Current month spend
        cursor.execute("SELECT COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE date LIKE ?", (f"{curr_month_str}%",))
        spent = float(cursor.fetchone()["spent"])
        
        remaining = max(0.0, monthly_limit - spent)
        pct_used = round((spent / monthly_limit * 100), 1) if monthly_limit > 0 else 0.0
        
        status = "ok"
        if pct_used >= 100:
            status = "exceeded"
        elif pct_used >= 80:
            status = "warning"
            
        return {
            "id": 1,
            "category": "OVERALL",
            "monthly_limit": monthly_limit,
            "month": today.month,
            "year": today.year,
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "percentage_used": pct_used,
            "status": status,
            "created_at": datetime.now().isoformat()
        }


@app.post("/api/budget")
def set_budget(budget: BudgetCreate):
    """Set or update the monthly spending budget."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES ('monthly_budget', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (str(budget.monthly_limit),))
        return {"success": True, "monthly_limit": budget.monthly_limit}


# ==========================================
# 5. SETTINGS, EXPORT & SAMPLE DATA
# ==========================================

@app.get("/api/settings")
def get_settings():
    """Get all user settings."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        return {r["key"]: r["value"] for r in rows}


@app.put("/api/settings")
def update_settings(settings: SettingsUpdate):
    """Update user preferences."""
    with get_db() as conn:
        cursor = conn.cursor()
        if settings.currency_symbol:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('currency_symbol', ?)", (settings.currency_symbol,))
        if settings.currency_code:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('currency_code', ?)", (settings.currency_code,))
        if settings.user_name:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('user_name', ?)", (settings.user_name,))
        if settings.monthly_budget is not None:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('monthly_budget', ?)", (str(settings.monthly_budget),))
        if settings.theme:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('theme', ?)", (settings.theme,))
        return {"success": True}


@app.post("/api/sample-data/seed")
def seed_data(force: bool = Query(True)):
    """Populate realistic sample expenses across multiple months."""
    count = seed_database(force=force)
    return {"success": True, "message": f"Successfully loaded {count} sample expense records."}


@app.post("/api/sample-data/clear")
def clear_data():
    """Reset database and clear all expenses."""
    clear_database()
    return {"success": True, "message": "All expense data cleared."}


@app.get("/api/export/csv")
def export_csv():
    """Export all expenses as downloadable CSV."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, category, description, amount, payment_method, notes, created_at FROM expenses ORDER BY date DESC, id DESC")
        rows = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Date", "Category", "Description", "Amount (INR)", "Payment Method", "Notes", "Created At"])
        
        for r in rows:
            writer.writerow([r["id"], r["date"], r["category"], r["description"], r["amount"], r["payment_method"], r["notes"], r["created_at"]])
            
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ExpenseAI_Export.csv"}
        )


# ==========================================
# 6. STATIC FILE SERVING FOR FRONTEND
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
