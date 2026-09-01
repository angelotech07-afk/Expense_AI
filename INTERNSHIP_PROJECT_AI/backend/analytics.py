"""
ExpenseAI - Analytics Engine
Performs core financial aggregations, monthly/category breakdowns, daily trends, and highest spending analyses.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import calendar
from backend.database import fetch_all, fetch_one

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def get_dashboard_summary(month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Computes top-level KPI cards:
    - Total Expenses (for selected month/year or all-time)
    - This Month total & comparison vs Last Month
    - Average Daily Spending
    - Highest Individual Expense
    - Top Category & its percentage
    - Total Number of Transactions
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    
    # 1. Overall / Selected Period Total and count
    if month is not None:
        month_str = f"{target_year:04d}-{target_month:02d}%"
        expenses_rows = fetch_all(
            "SELECT id, amount, category, description, date, payment_method FROM expenses WHERE date LIKE ? ORDER BY date DESC",
            (month_str,)
        )
    else:
        expenses_rows = fetch_all(
            "SELECT id, amount, category, description, date, payment_method FROM expenses ORDER BY date DESC"
        )
        
    total_spending = sum(r["amount"] for r in expenses_rows)
    total_transactions = len(expenses_rows)
    
    # 2. Current Month Spending & Previous Month Spending
    curr_month_str = f"{target_year:04d}-{target_month:02d}%"
    curr_month_rows = fetch_all(
        "SELECT amount, date, category FROM expenses WHERE date LIKE ?",
        (curr_month_str,)
    )
    this_month_total = sum(r["amount"] for r in curr_month_rows)
    this_month_transactions = len(curr_month_rows)
    
    # Previous Month calculation
    if target_month == 1:
        prev_month = 12
        prev_year = target_year - 1
    else:
        prev_month = target_month - 1
        prev_year = target_year
    prev_month_str = f"{prev_year:04d}-{prev_month:02d}%"
    prev_month_rows = fetch_all(
        "SELECT amount FROM expenses WHERE date LIKE ?",
        (prev_month_str,)
    )
    prev_month_total = sum(r["amount"] for r in prev_month_rows)
    
    # Month-over-month % change
    if prev_month_total > 0:
        mom_change_pct = round(((this_month_total - prev_month_total) / prev_month_total) * 100, 1)
    elif this_month_total > 0:
        mom_change_pct = 100.0
    else:
        mom_change_pct = 0.0
        
    # 3. Average Daily Spending
    if month is not None:
        days_in_month = calendar.monthrange(target_year, target_month)[1]
        # If current active month, compute up to today's day
        if target_year == now.year and target_month == now.month:
            active_days = max(1, now.day)
        else:
            active_days = days_in_month
        avg_daily_spending = round(this_month_total / active_days, 2) if active_days > 0 else 0.0
    else:
        # All time: total spending / number of unique spending days or span
        date_span_row = fetch_one("SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(DISTINCT date) as unique_days FROM expenses")
        unique_days = date_span_row["unique_days"] if date_span_row and date_span_row["unique_days"] else 1
        avg_daily_spending = round(total_spending / max(1, unique_days), 2)
        
    # 4. Highest Individual Expense
    highest_expense_row = fetch_one(
        "SELECT id, amount, category, description, date, payment_method FROM expenses ORDER BY amount DESC LIMIT 1"
    )
    highest_expense = dict(highest_expense_row) if highest_expense_row else {
        "amount": 0.0,
        "description": "None",
        "category": "N/A",
        "date": "-"
    }
    
    # 5. Top Category
    target_rows = curr_month_rows if month is not None else expenses_rows
    cat_totals: Dict[str, float] = {}
    for r in target_rows:
        cat = r["category"]
        cat_totals[cat] = cat_totals.get(cat, 0.0) + r["amount"]
        
    if cat_totals:
        top_category_name = max(cat_totals, key=cat_totals.get)
        top_category_amount = cat_totals[top_category_name]
        basis_total = this_month_total if month is not None else total_spending
        top_category_pct = round((top_category_amount / basis_total) * 100, 1) if basis_total > 0 else 0.0
    else:
        top_category_name = "N/A"
        top_category_amount = 0.0
        top_category_pct = 0.0
        
    # 6. Overall trend direction
    if mom_change_pct > 5:
        trend_direction = "increasing"
    elif mom_change_pct < -5:
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"

    return {
        "total_spending": round(total_spending, 2),
        "total_transactions": total_transactions,
        "this_month_total": round(this_month_total, 2),
        "this_month_transactions": this_month_transactions,
        "prev_month_total": round(prev_month_total, 2),
        "mom_change_pct": mom_change_pct,
        "avg_daily_spending": avg_daily_spending,
        "highest_expense": highest_expense,
        "top_category": {
            "name": top_category_name,
            "amount": round(top_category_amount, 2),
            "percentage": top_category_pct
        },
        "trend_direction": trend_direction,
        "current_month_name": MONTH_NAMES[target_month - 1],
        "current_year": target_year
    }


def get_monthly_analysis(year: Optional[int] = None) -> Dict[str, Any]:
    """
    Computes 12-month expense breakdown for given year:
    - Jan to Dec totals
    - Average monthly spending
    - Highest spending month
    - Lowest spending month (among active months)
    - Month-to-month deltas
    """
    target_year = year if year is not None else datetime.now().year
    
    # Query all expenses for target year
    year_prefix = f"{target_year:04d}-%"
    rows = fetch_all(
        "SELECT amount, strftime('%m', date) as month_num FROM expenses WHERE date LIKE ?",
        (year_prefix,)
    )
    
    monthly_totals = [0.0] * 12
    monthly_counts = [0] * 12
    
    for r in rows:
        m_idx = int(r["month_num"]) - 1
        monthly_totals[m_idx] += float(r["amount"])
        monthly_counts[m_idx] += 1
        
    monthly_totals = [round(t, 2) for t in monthly_totals]
    
    total_yearly_spending = sum(monthly_totals)
    
    # Month-to-month changes
    mom_changes = []
    for i in range(12):
        if i == 0:
            mom_changes.append(0.0)
        else:
            prev = monthly_totals[i - 1]
            curr = monthly_totals[i]
            if prev > 0:
                diff_pct = round(((curr - prev) / prev) * 100, 1)
            elif curr > 0:
                diff_pct = 100.0
            else:
                diff_pct = 0.0
            mom_changes.append(diff_pct)
            
    # Active months stats
    active_totals = [(MONTH_NAMES[i], monthly_totals[i], i + 1) for i in range(12) if monthly_totals[i] > 0]
    
    if active_totals:
        highest_month = max(active_totals, key=lambda x: x[1])
        lowest_month = min(active_totals, key=lambda x: x[1])
        avg_monthly = round(total_yearly_spending / len(active_totals), 2)
    else:
        highest_month = ("None", 0.0, 0)
        lowest_month = ("None", 0.0, 0)
        avg_monthly = 0.0
        
    monthly_breakdown = []
    for i in range(12):
        monthly_breakdown.append({
            "month_num": i + 1,
            "month_name": MONTH_NAMES[i],
            "total": monthly_totals[i],
            "transaction_count": monthly_counts[i],
            "mom_change_pct": mom_changes[i]
        })
        
    return {
        "year": target_year,
        "total_yearly_spending": round(total_yearly_spending, 2),
        "avg_monthly_spending": avg_monthly,
        "highest_spending_month": {
            "name": highest_month[0],
            "amount": round(highest_month[1], 2),
            "month_num": highest_month[2]
        },
        "lowest_spending_month": {
            "name": lowest_month[0],
            "amount": round(lowest_month[1], 2),
            "month_num": lowest_month[2]
        },
        "monthly_breakdown": monthly_breakdown,
        "months": MONTH_NAMES,
        "totals": monthly_totals
    }


def get_category_analysis(month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Computes category-wise breakdown:
    - Total per category
    - Percentage of total
    - Transaction count per category
    - Average transaction amount per category
    - Dynamic highlight text
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month
    
    if target_month is not None:
        date_pattern = f"{target_year:04d}-{target_month:02d}%"
        rows = fetch_all(
            "SELECT id, amount, category, description, date FROM expenses WHERE date LIKE ?",
            (date_pattern,)
        )
        period_label = f"{MONTH_NAMES[target_month - 1]} {target_year}"
    else:
        rows = fetch_all("SELECT id, amount, category, description, date FROM expenses")
        period_label = "All Time"
        
    total_spending = sum(r["amount"] for r in rows)
    
    cat_map: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        cat = r["category"]
        amt = float(r["amount"])
        if cat not in cat_map:
            cat_map[cat] = {
                "category": cat,
                "total": 0.0,
                "count": 0,
                "max_expense": 0.0,
                "max_description": ""
            }
        cat_map[cat]["total"] += amt
        cat_map[cat]["count"] += 1
        if amt > cat_map[cat]["max_expense"]:
            cat_map[cat]["max_expense"] = amt
            cat_map[cat]["max_description"] = r["description"]
            
    categories_list = []
    for cat, data in cat_map.items():
        cat_total = round(data["total"], 2)
        percentage = round((cat_total / total_spending * 100), 1) if total_spending > 0 else 0.0
        avg_txn = round(cat_total / data["count"], 2) if data["count"] > 0 else 0.0
        categories_list.append({
            "category": cat,
            "total": cat_total,
            "percentage": percentage,
            "count": data["count"],
            "avg_transaction": avg_txn,
            "max_expense": round(data["max_expense"], 2),
            "max_description": data["max_description"]
        })
        
    # Sort descending by total amount
    categories_list.sort(key=lambda x: x["total"], reverse=True)
    
    if categories_list:
        top_cat = categories_list[0]
        highlight_text = (
            f"Your highest spending category in {period_label} is {top_cat['category']}, "
            f"accounting for {top_cat['percentage']}% of your total expenses (₹{top_cat['total']:,.2f})."
        )
    else:
        top_cat = None
        highlight_text = "No expense data available for the selected period."
        
    return {
        "period": period_label,
        "total_spending": round(total_spending, 2),
        "total_categories": len(categories_list),
        "highest_category": top_cat,
        "highlight_text": highlight_text,
        "categories": categories_list
    }


def get_daily_spending(month: Optional[int] = None, year: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
    """
    Computes daily timeline data for charts:
    Returns list of dates and amounts for the requested month or past N days.
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    
    # Query daily grouped expenses
    month_prefix = f"{target_year:04d}-{target_month:02d}%"
    rows = fetch_all(
        "SELECT date, SUM(amount) as daily_total, COUNT(*) as txn_count FROM expenses WHERE date LIKE ? GROUP BY date ORDER BY date ASC",
        (month_prefix,)
    )
    
    # Generate all days in target month
    days_in_month = calendar.monthrange(target_year, target_month)[1]
    daily_map = {r["date"]: {"total": float(r["daily_total"]), "count": int(r["txn_count"])} for r in rows}
    
    daily_data = []
    labels = []
    amounts = []
    
    for d in range(1, days_in_month + 1):
        date_str = f"{target_year:04d}-{target_month:02d}-{d:02d}"
        entry = daily_map.get(date_str, {"total": 0.0, "count": 0})
        labels.append(f"{d:02d} {MONTH_NAMES[target_month - 1][:3]}")
        amounts.append(round(entry["total"], 2))
        daily_data.append({
            "date": date_str,
            "day": d,
            "label": f"{d:02d} {MONTH_NAMES[target_month - 1][:3]}",
            "amount": round(entry["total"], 2),
            "count": entry["count"]
        })
        
    return {
        "month": target_month,
        "year": target_year,
        "month_name": MONTH_NAMES[target_month - 1],
        "labels": labels,
        "amounts": amounts,
        "daily_breakdown": daily_data
    }


def get_highest_expense_analysis() -> Dict[str, Any]:
    """
    'Where Is My Money Going?' Analysis:
    - Highest individual expense
    - Highest category
    - Highest spending day
    - Highest spending month
    - Top 5 largest single expenses
    """
    # 1. Highest individual expense
    highest_single = fetch_one(
        "SELECT id, amount, category, description, date, payment_method FROM expenses ORDER BY amount DESC LIMIT 1"
    )
    
    # 2. Top 5 largest expenses
    top_5_rows = fetch_all(
        "SELECT id, amount, category, description, date, payment_method FROM expenses ORDER BY amount DESC LIMIT 5"
    )
    
    # 3. Highest category
    highest_cat_row = fetch_one(
        "SELECT category, SUM(amount) as total, COUNT(*) as count FROM expenses GROUP BY category ORDER BY total DESC LIMIT 1"
    )
    
    # 4. Highest spending single day
    highest_day_row = fetch_one(
        "SELECT date, SUM(amount) as day_total, COUNT(*) as count FROM expenses GROUP BY date ORDER BY day_total DESC LIMIT 1"
    )
    
    # 5. Highest spending month
    highest_month_row = fetch_one(
        "SELECT strftime('%Y-%m', date) as ym, SUM(amount) as month_total FROM expenses GROUP BY ym ORDER BY month_total DESC LIMIT 1"
    )
    
    formatted_month = "None"
    if highest_month_row and highest_month_row["ym"]:
        try:
            parts = highest_month_row["ym"].split("-")
            formatted_month = f"{MONTH_NAMES[int(parts[1]) - 1]} {parts[0]}"
        except Exception:
            formatted_month = highest_month_row["ym"]
            
    return {
        "highest_individual_expense": dict(highest_single) if highest_single else None,
        "top_5_expenses": [dict(r) for r in top_5_rows],
        "highest_category": dict(highest_cat_row) if highest_cat_row else None,
        "highest_spending_day": {
            "date": highest_day_row["date"] if highest_day_row else "None",
            "amount": round(highest_day_row["day_total"], 2) if highest_day_row else 0.0,
            "count": highest_day_row["count"] if highest_day_row else 0
        },
        "highest_spending_month": {
            "label": formatted_month,
            "amount": round(highest_month_row["month_total"], 2) if highest_month_row else 0.0
        }
    }
