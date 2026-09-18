import sqlite3
import calendar
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional


CATEGORY_COLORS = {
    "Food": "#f97316",           # Vibrant Orange
    "Groceries": "#10b981",      # Emerald Green
    "Shopping": "#ec4899",      # Pink
    "Bills": "#eab308",          # Amber
    "Rent": "#8b5cf6",           # Purple
    "Travel": "#06b6d4",         # Cyan
    "Transportation": "#3b82f6", # Blue
    "Healthcare": "#ef4444",     # Red
    "Entertainment": "#a855f7",  # Violet
    "Education": "#14b8a6",      # Teal
    "Other": "#64748b"           # Slate
}


def get_setting(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    """Retrieve setting value by key."""
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row["value"] if row else default


def get_summary_stats(conn: sqlite3.Connection, target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Calculate high-level dashboard metrics:
    - Total expenses (all time or selected period)
    - This month total expenses
    - Previous month total expenses & MoM change
    - Average daily spending in current month
    - Highest individual expense
    - Top category and % share
    - Total transaction count
    """
    cursor = conn.cursor()
    
    # Base date
    today = target_date or date.today()
    current_year = today.year
    current_month = today.month
    
    # 1. Total All-time Expenses
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total, COUNT(id) AS count FROM expenses")
    all_time = cursor.fetchone()
    total_expenses = float(all_time["total"])
    transaction_count = int(all_time["count"])
    
    # 2. This Month Expenses
    curr_month_str = f"{current_year:04d}-{current_month:02d}"
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(id) AS count FROM expenses WHERE date LIKE ?",
        (f"{curr_month_str}%",)
    )
    this_month_row = cursor.fetchone()
    this_month_expenses = float(this_month_row["total"])
    
    # 3. Previous Month Expenses
    if current_month == 1:
        prev_month_year = current_year - 1
        prev_month = 12
    else:
        prev_month_year = current_year
        prev_month = current_month - 1
        
    prev_month_str = f"{prev_month_year:04d}-{prev_month:02d}"
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE date LIKE ?",
        (f"{prev_month_str}%",)
    )
    prev_month_row = cursor.fetchone()
    prev_month_expenses = float(prev_month_row["total"])
    
    # Calculate MoM change percentage
    if prev_month_expenses > 0:
        mom_change_pct = round(((this_month_expenses - prev_month_expenses) / prev_month_expenses) * 100, 1)
    else:
        mom_change_pct = 0.0 if this_month_expenses == 0 else 100.0
        
    # 4. Average Daily Spending (for current month up to today)
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    days_elapsed = min(today.day, days_in_month) if (today.year == current_year and today.month == current_month) else days_in_month
    days_elapsed = max(1, days_elapsed)
    avg_daily_spending = round(this_month_expenses / days_elapsed, 2)
    
    # 5. Highest Individual Expense
    cursor.execute(
        "SELECT id, amount, category, description, date, payment_method FROM expenses ORDER BY amount DESC LIMIT 1"
    )
    highest_row = cursor.fetchone()
    highest_expense = dict(highest_row) if highest_row else None
    
    # 6. Top Category (All time or this month)
    cursor.execute("""
        SELECT category, SUM(amount) AS total, COUNT(id) AS count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """)
    top_cat_row = cursor.fetchone()
    top_category = None
    if top_cat_row and total_expenses > 0:
        cat_total = float(top_cat_row["total"])
        top_category = {
            "category": top_cat_row["category"],
            "total": cat_total,
            "count": int(top_cat_row["count"]),
            "percentage": round((cat_total / total_expenses) * 100, 1),
            "color": CATEGORY_COLORS.get(top_cat_row["category"], "#6366f1")
        }
        
    currency_symbol = get_setting(conn, "currency_symbol", "₹")
    month_name = calendar.month_name[current_month]
    
    return {
        "total_expenses": total_expenses,
        "this_month_expenses": this_month_expenses,
        "prev_month_expenses": prev_month_expenses,
        "month_over_month_change_pct": mom_change_pct,
        "avg_daily_spending": avg_daily_spending,
        "highest_expense": highest_expense,
        "top_category": top_category,
        "transaction_count": transaction_count,
        "currency_symbol": currency_symbol,
        "current_month_name": month_name,
        "current_year": current_year
    }


def get_monthly_breakdown(conn: sqlite3.Connection, year: int) -> Dict[str, Any]:
    """
    Calculate spending for each of the 12 months for a given year.
    Returns array of month data points, highest/lowest month, and averages.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            CAST(strftime('%m', date) AS INTEGER) AS month_num,
            SUM(amount) AS total,
            COUNT(id) AS count,
            AVG(amount) AS avg_amount
        FROM expenses
        WHERE strftime('%Y', date) = ?
        GROUP BY month_num
        ORDER BY month_num ASC
    """, (str(year),))
    
    rows = cursor.fetchall()
    month_data_map = {row["month_num"]: row for row in rows}
    
    months_list = []
    total_year_spending = 0.0
    active_months_count = 0
    prev_total = None
    
    for m in range(1, 13):
        m_name = calendar.month_name[m]
        if m in month_data_map:
            total = float(month_data_map[m]["total"])
            count = int(month_data_map[m]["count"])
            avg_tx = round(float(month_data_map[m]["avg_amount"]), 2)
            total_year_spending += total
            active_months_count += 1
        else:
            total = 0.0
            count = 0
            avg_tx = 0.0
            
        change_pct = None
        if prev_total is not None and prev_total > 0:
            change_pct = round(((total - prev_total) / prev_total) * 100, 1)
        elif prev_total == 0 and total > 0:
            change_pct = 100.0
            
        prev_total = total
        
        months_list.append({
            "month_num": m,
            "month_name": m_name,
            "year": year,
            "total": total,
            "transaction_count": count,
            "avg_per_transaction": avg_tx,
            "change_pct_prev_month": change_pct
        })
        
    avg_monthly_spending = round(total_year_spending / max(1, active_months_count), 2)
    
    active_months = [m for m in months_list if m["total"] > 0]
    highest_month = max(active_months, key=lambda x: x["total"]) if active_months else None
    lowest_month = min(active_months, key=lambda x: x["total"]) if active_months else None
    
    return {
        "year": year,
        "months": months_list,
        "total_year_spending": total_year_spending,
        "avg_monthly_spending": avg_monthly_spending,
        "highest_month": highest_month,
        "lowest_month": lowest_month
    }


def get_category_breakdown(
    conn: sqlite3.Connection,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate spending by category with percentage distribution and transaction counts.
    """
    cursor = conn.cursor()
    query = "SELECT category, SUM(amount) AS total, COUNT(id) AS count, AVG(amount) AS avg_amount FROM expenses WHERE 1=1"
    params: List[Any] = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if year:
        query += " AND strftime('%Y', date) = ?"
        params.append(str(year))
    if month:
        query += " AND CAST(strftime('%m', date) AS INTEGER) = ?"
        params.append(month)
        
    query += " GROUP BY category ORDER BY total DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    total_amount = sum(float(r["total"]) for r in rows)
    categories = []
    
    for r in rows:
        c_total = float(r["total"])
        pct = round((c_total / total_amount * 100), 1) if total_amount > 0 else 0.0
        categories.append({
            "category": r["category"],
            "total": c_total,
            "percentage": pct,
            "transaction_count": int(r["count"]),
            "avg_transaction": round(float(r["avg_amount"]), 2),
            "color": CATEGORY_COLORS.get(r["category"], "#6366f1")
        })
        
    highest_cat = categories[0] if categories else None
    
    return {
        "categories": categories,
        "total_amount": total_amount,
        "highest_category": highest_cat
    }


def get_daily_trend(
    conn: sqlite3.Connection,
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get daily expense totals for the specified number of recent days or custom date range.
    """
    cursor = conn.cursor()
    
    if start_date and end_date:
        query = """
            SELECT date, SUM(amount) AS total, COUNT(id) AS count
            FROM expenses
            WHERE date >= ? AND date <= ?
            GROUP BY date
            ORDER BY date ASC
        """
        cursor.execute(query, (start_date, end_date))
    else:
        # Default: last N days from max date in db or today
        cursor.execute("SELECT MAX(date) AS max_d FROM expenses")
        max_row = cursor.fetchone()
        latest_date_str = max_row["max_d"] if (max_row and max_row["max_d"]) else date.today().isoformat()
        latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
        cutoff_date = (latest_date - timedelta(days=days - 1)).isoformat()
        
        query = """
            SELECT date, SUM(amount) AS total, COUNT(id) AS count
            FROM expenses
            WHERE date >= ?
            GROUP BY date
            ORDER BY date ASC
        """
        cursor.execute(query, (cutoff_date,))
        
    rows = cursor.fetchall()
    return [{"date": r["date"], "total": float(r["total"]), "transaction_count": int(r["count"])} for r in rows]


def get_where_money_goes(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Identify:
    - Highest individual expense
    - Highest category
    - Highest spending day
    - Highest spending month
    - Top 5 recent large expenses
    """
    cursor = conn.cursor()
    
    # 1. Highest Individual Expense
    cursor.execute("""
        SELECT id, amount, category, description, date, payment_method, notes
        FROM expenses
        ORDER BY amount DESC
        LIMIT 1
    """)
    highest_exp_row = cursor.fetchone()
    highest_individual_expense = dict(highest_exp_row) if highest_exp_row else None
    
    # 2. Highest Category Overall
    cursor.execute("""
        SELECT category, SUM(amount) AS total, COUNT(id) AS count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """)
    highest_cat_row = cursor.fetchone()
    highest_category = dict(highest_cat_row) if highest_cat_row else None
    
    # 3. Highest Spending Day
    cursor.execute("""
        SELECT date, SUM(amount) AS total, COUNT(id) AS count
        FROM expenses
        GROUP BY date
        ORDER BY total DESC
        LIMIT 1
    """)
    highest_day_row = cursor.fetchone()
    highest_spending_day = dict(highest_day_row) if highest_day_row else None
    
    # 4. Highest Spending Month
    cursor.execute("""
        SELECT strftime('%Y-%m', date) AS month_key, SUM(amount) AS total, COUNT(id) AS count
        FROM expenses
        GROUP BY month_key
        ORDER BY total DESC
        LIMIT 1
    """)
    highest_month_row = cursor.fetchone()
    highest_spending_month = None
    if highest_month_row:
        m_key = highest_month_row["month_key"]
        try:
            yr, mo = m_key.split("-")
            m_name = calendar.month_name[int(mo)]
            highest_spending_month = {
                "month_key": m_key,
                "month_name": f"{m_name} {yr}",
                "total": float(highest_month_row["total"]),
                "count": int(highest_month_row["count"])
            }
        except Exception:
            highest_spending_month = dict(highest_month_row)
            
    # 5. Top 5 Largest Expenses
    cursor.execute("""
        SELECT id, amount, category, description, date, payment_method
        FROM expenses
        ORDER BY amount DESC
        LIMIT 5
    """)
    top_large = [dict(r) for r in cursor.fetchall()]
    
    return {
        "highest_individual_expense": highest_individual_expense,
        "highest_category": highest_category,
        "highest_spending_day": highest_spending_day,
        "highest_spending_month": highest_spending_month,
        "top_recent_large_expenses": top_large
    }
