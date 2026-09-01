"""
ExpenseAI - Main Backend Application Server
Flask REST API delivering high-performance endpoints for Expense CRUD,
Deep Analytics, AI Insights, Financial Health Scoring, and Budget Planning.
"""

import os
import io
import csv
import json
import calendar
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response

from backend.database import (
    init_db, fetch_all, fetch_one, execute_query, get_connection
)
from backend.models import (
    validate_expense_data, validate_budget_data,
    VALID_CATEGORIES, VALID_PAYMENT_METHODS
)
from backend.analytics import (
    get_dashboard_summary, get_monthly_analysis,
    get_category_analysis, get_daily_spending,
    get_highest_expense_analysis
)
from backend.ai_analysis import (
    calculate_expense_health_score, get_ai_prediction,
    generate_local_ai_insights, query_gemini_ai_insights
)
from backend.seed_data import seed_demo_data, clear_all_data

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

# Ensure database is initialized at startup
init_db()


# --------------------------------------------------------------------------
# STATIC FRONTEND ROUTES
# --------------------------------------------------------------------------
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


# --------------------------------------------------------------------------
# HEALTH & METADATA
# --------------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "app": "ExpenseAI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    """Returns application constants, categories, payment methods, and settings."""
    settings_rows = fetch_all("SELECT key, value FROM settings")
    settings_dict = {r["key"]: r["value"] for r in settings_rows}
    
    return jsonify({
        "categories": VALID_CATEGORIES,
        "payment_methods": VALID_PAYMENT_METHODS,
        "settings": settings_dict
    })


# --------------------------------------------------------------------------
# EXPENSE CRUD API
# --------------------------------------------------------------------------
@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    """
    List expenses with flexible filtering, search, sorting, and pagination.
    Query Params:
    - search: text search in description, notes, category
    - category: filter by category
    - payment_method: filter by payment method
    - month: filter by month (1-12)
    - year: filter by year (e.g. 2026)
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - min_amount: float
    - max_amount: float
    - sort_by: date | amount | category | description (default: date)
    - order: asc | desc (default: desc)
    - limit: int (default: 100)
    - offset: int (default: 0)
    """
    try:
        conditions = []
        params = []
        
        # Search
        search = request.args.get("search", "").strip()
        if search:
            conditions.append("(description LIKE ? OR notes LIKE ? OR category LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
            
        # Category
        category = request.args.get("category", "").strip()
        if category and category.upper() != "ALL":
            conditions.append("category = ?")
            params.append(category)
            
        # Payment Method
        pm = request.args.get("payment_method", "").strip()
        if pm and pm.upper() != "ALL":
            conditions.append("payment_method = ?")
            params.append(pm)
            
        # Month & Year
        month = request.args.get("month")
        year = request.args.get("year")
        if month and year:
            conditions.append("date LIKE ?")
            params.append(f"{int(year):04d}-{int(month):02d}%")
        elif year:
            conditions.append("date LIKE ?")
            params.append(f"{int(year):04d}-%")
            
        # Date range
        start_date = request.args.get("start_date", "").strip()
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
            
        end_date = request.args.get("end_date", "").strip()
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
            
        # Amount range
        min_amount = request.args.get("min_amount")
        if min_amount:
            conditions.append("amount >= ?")
            params.append(float(min_amount))
            
        max_amount = request.args.get("max_amount")
        if max_amount:
            conditions.append("amount <= ?")
            params.append(float(max_amount))
            
        # Sorting
        sort_by = request.args.get("sort_by", "date").lower()
        order = request.args.get("order", "desc").lower()
        
        allowed_sort_fields = {"date": "date", "amount": "amount", "category": "category", "description": "description", "id": "id"}
        sort_field = allowed_sort_fields.get(sort_by, "date")
        sort_order = "ASC" if order == "asc" else "DESC"
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        # Count total matches
        count_query = f"SELECT COUNT(*) as total_count, COALESCE(SUM(amount), 0) as total_amount FROM expenses {where_clause}"
        stats_row = fetch_one(count_query, tuple(params))
        total_count = stats_row["total_count"] if stats_row else 0
        total_filtered_amount = stats_row["total_amount"] if stats_row else 0.0
        
        # Pagination
        limit = max(1, min(500, int(request.args.get("limit", 100))))
        offset = max(0, int(request.args.get("offset", 0)))
        
        query = f"""
            SELECT id, amount, category, description, date, payment_method, notes, created_at, updated_at
            FROM expenses
            {where_clause}
            ORDER BY {sort_field} {sort_order}, id DESC
            LIMIT ? OFFSET ?
        """
        rows = fetch_all(query, tuple(params + [limit, offset]))
        
        return jsonify({
            "expenses": rows,
            "total_count": total_count,
            "total_amount": round(total_filtered_amount, 2),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve expenses: {str(e)}"}), 400


@app.route("/api/expenses", methods=["POST"])
def create_expense():
    """Create a new expense record."""
    try:
        data = request.get_json() or {}
        is_valid, err, sanitized = validate_expense_data(data)
        if not is_valid:
            return jsonify({"error": err}), 422
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (amount, category, description, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sanitized["amount"],
                sanitized["category"],
                sanitized["description"],
                sanitized["date"],
                sanitized["payment_method"],
                sanitized["notes"]
            ))
            new_id = cursor.lastrowid
            conn.commit()
            
        created = fetch_one("SELECT * FROM expenses WHERE id = ?", (new_id,))
        return jsonify({
            "message": "Expense created successfully.",
            "expense": created
        }), 201
    except Exception as e:
        return jsonify({"error": f"Server error creating expense: {str(e)}"}), 500


@app.route("/api/expenses/<int:expense_id>", methods=["GET"])
def get_expense(expense_id: int):
    """Retrieve a single expense by ID."""
    expense = fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    if not expense:
        return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404
    return jsonify({"expense": expense})


@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id: int):
    """Update an existing expense by ID."""
    try:
        existing = fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        if not existing:
            return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404
            
        data = request.get_json() or {}
        is_valid, err, sanitized = validate_expense_data(data, is_update=True)
        if not is_valid:
            return jsonify({"error": err}), 422
            
        # Prepare fields to update
        fields = []
        params = []
        for key in ["amount", "category", "description", "date", "payment_method", "notes"]:
            if key in sanitized:
                fields.append(f"{key} = ?")
                params.append(sanitized[key])
                
        if not fields:
            return jsonify({"message": "No fields provided to update.", "expense": existing})
            
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(expense_id)
        
        query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
        execute_query(query, tuple(params))
        
        updated = fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        return jsonify({
            "message": "Expense updated successfully.",
            "expense": updated
        })
    except Exception as e:
        return jsonify({"error": f"Server error updating expense: {str(e)}"}), 500


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id: int):
    """Delete an expense by ID."""
    try:
        existing = fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        if not existing:
            return jsonify({"error": f"Expense with ID {expense_id} not found."}), 404
            
        execute_query("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return jsonify({"message": f"Expense with ID {expense_id} deleted successfully."})
    except Exception as e:
        return jsonify({"error": f"Server error deleting expense: {str(e)}"}), 500


# --------------------------------------------------------------------------
# ANALYTICS ENDPOINTS
# --------------------------------------------------------------------------
@app.route("/api/analytics/summary", methods=["GET"])
def analytics_summary():
    """Returns top KPI dashboard cards."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    summary = get_dashboard_summary(month, year)
    return jsonify(summary)


@app.route("/api/analytics/monthly", methods=["GET"])
def analytics_monthly():
    """Returns 12-month expense progression for a year."""
    year = request.args.get("year", type=int)
    result = get_monthly_analysis(year)
    return jsonify(result)


@app.route("/api/analytics/categories", methods=["GET"])
def analytics_categories():
    """Returns category breakdown and percentage distribution."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    result = get_category_analysis(month, year)
    return jsonify(result)


@app.route("/api/analytics/daily", methods=["GET"])
def analytics_daily():
    """Returns daily spending points for interactive trend charts."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    result = get_daily_spending(month, year)
    return jsonify(result)


@app.route("/api/analytics/highest", methods=["GET"])
def analytics_highest():
    """Returns 'Where Is My Money Going?' analytical breakdown."""
    result = get_highest_expense_analysis()
    return jsonify(result)


# --------------------------------------------------------------------------
# AI INSIGHTS & HEALTH SCORE ENDPOINTS
# --------------------------------------------------------------------------
@app.route("/api/ai/insights", methods=["GET"])
def ai_insights():
    """Returns dynamically computed AI suggestions & anomalies."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    
    local_insights = generate_local_ai_insights(month, year)
    gemini_data = query_gemini_ai_insights(month=month, year=year)
    
    return jsonify({
        "insights": local_insights,
        "gemini_analysis": gemini_data
    })


@app.route("/api/ai/health-score", methods=["GET"])
def ai_health_score():
    """Returns Expense Health Score (0-100) and point breakdown."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    result = calculate_expense_health_score(month, year)
    return jsonify(result)


@app.route("/api/ai/predict", methods=["GET"])
def ai_predict():
    """Returns month-end burn rate forecast."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    result = get_ai_prediction(month, year)
    return jsonify(result)


@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    """Interactive AI Financial Assistant Q&A endpoint."""
    data = request.get_json() or {}
    user_query = data.get("query", "").strip()
    if not user_query:
        return jsonify({"error": "Query cannot be empty."}), 400
        
    # Gather financial summary to provide context
    now = datetime.now()
    summary = get_dashboard_summary()
    cat_analysis = get_category_analysis()
    
    top_cat = summary["top_category"]["name"]
    total = summary["total_spending"]
    
    # Try Gemini if key configured
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("AI_API_KEY")
    if not key:
        row = fetch_one("SELECT value FROM settings WHERE key = 'gemini_api_key'")
        if row and row["value"]:
            key = row["value"].strip()
            
    if key:
        try:
            import urllib.request
            prompt = (
                f"You are ExpenseAI Financial Advisor. Context:\n"
                f"- Total Recorded Spending: ₹{total:,.2f}\n"
                f"- Top Spending Category: {top_cat} (₹{summary['top_category']['amount']:,.2f})\n"
                f"- User Question: {user_query}\n"
                f"Provide a helpful, practical, encouraging financial response under 100 words in friendly markdown."
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                g_data = json.loads(resp.read().decode("utf-8"))
                text = g_data["candidates"][0]["content"]["parts"][0]["text"]
                return jsonify({"reply": text, "source": "Gemini AI"})
        except Exception:
            pass
            
    # Rule-based fallback response
    q_lower = user_query.lower()
    if "save" in q_lower or "cut" in q_lower or "budget" in q_lower:
        reply = (
            f"Based on your recent transactions, your biggest expense category is **{top_cat}** "
            f"(₹{summary['top_category']['amount']:,.2f}). "
            f"A practical strategy is targeting a 10-15% reduction on discretionary {top_cat} purchases, "
            f"which could free up approximately ₹{summary['top_category']['amount']*0.12:,.0f} this month!"
        )
    elif "highest" in q_lower or "largest" in q_lower:
        hi = summary['highest_expense']
        reply = f"Your single highest expense was **₹{hi['amount']:,.2f}** for '{hi['description']}' ({hi['category']}) on {hi['date']}."
    else:
        reply = (
            f"Here is your financial snapshot: You have spent a total of ₹{total:,.2f} across "
            f"{summary['total_transactions']} transactions. Your top expenditure area is **{top_cat}**. "
            f"Review your budget progress in the Budget tab to keep spending in check!"
        )
        
    return jsonify({"reply": reply, "source": "ExpenseAI Local Engine"})


# --------------------------------------------------------------------------
# BUDGET ENDPOINTS
# --------------------------------------------------------------------------
@app.route("/api/budget", methods=["GET"])
def get_budgets():
    """Retrieve budgets for requested month/year and compute utilization."""
    now = datetime.now()
    month = request.args.get("month", type=int, default=now.month)
    year = request.args.get("year", type=int, default=now.year)
    
    # Query budget rules
    budget_rows = fetch_all(
        "SELECT id, month, year, category, amount, created_at, updated_at FROM budgets WHERE month = ? AND year = ?",
        (month, year)
    )
    
    # Query actual spending in that month
    month_prefix = f"{year:04d}-{month:02d}%"
    expense_rows = fetch_all(
        "SELECT amount, category FROM expenses WHERE date LIKE ?",
        (month_prefix,)
    )
    
    total_spent = sum(r["amount"] for r in expense_rows)
    cat_spent_map: Dict[str, float] = {}
    for r in expense_rows:
        c = r["category"]
        cat_spent_map[c] = cat_spent_map.get(c, 0.0) + r["amount"]
        
    # Overall budget (category 'ALL')
    overall_budget_row = next((b for b in budget_rows if b["category"] == "ALL"), None)
    overall_budget_amt = overall_budget_row["amount"] if overall_budget_row else 0.0
    
    overall_remaining = max(0.0, overall_budget_amt - total_spent) if overall_budget_amt > 0 else 0.0
    overall_pct_used = round((total_spent / overall_budget_amt) * 100, 1) if overall_budget_amt > 0 else 0.0
    
    # Category level budgets
    category_budgets = []
    for b in budget_rows:
        if b["category"] != "ALL":
            c_name = b["category"]
            c_spent = cat_spent_map.get(c_name, 0.0)
            c_amt = b["amount"]
            c_rem = max(0.0, c_amt - c_spent)
            c_pct = round((c_spent / c_amt) * 100, 1) if c_amt > 0 else 0.0
            category_budgets.append({
                "id": b["id"],
                "category": c_name,
                "budget_amount": round(c_amt, 2),
                "spent_amount": round(c_spent, 2),
                "remaining_amount": round(c_rem, 2),
                "percentage_used": c_pct,
                "is_exceeded": c_spent > c_amt
            })
            
    days_in_month = calendar.monthrange(year, month)[1]
    current_day = now.day if (year == now.year and month == now.month) else 1
    days_left = max(1, days_in_month - current_day)
    daily_remaining_allowance = round(overall_remaining / days_left, 2) if overall_remaining > 0 else 0.0
    
    return jsonify({
        "month": month,
        "year": year,
        "overall_budget": {
            "id": overall_budget_row["id"] if overall_budget_row else None,
            "budget_amount": round(overall_budget_amt, 2),
            "spent_amount": round(total_spent, 2),
            "remaining_amount": round(overall_remaining, 2),
            "percentage_used": overall_pct_used,
            "is_exceeded": total_spent > overall_budget_amt and overall_budget_amt > 0,
            "daily_remaining_allowance": daily_remaining_allowance,
            "days_left": days_left
        },
        "category_budgets": category_budgets,
        "all_budgets": budget_rows
    })


@app.route("/api/budget", methods=["POST"])
def set_budget():
    """Set or update monthly overall or category budget."""
    try:
        data = request.get_json() or {}
        is_valid, err, sanitized = validate_budget_data(data)
        if not is_valid:
            return jsonify({"error": err}), 422
            
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO budgets (month, year, category, amount, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(month, year, category) DO UPDATE SET
                    amount = excluded.amount,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                sanitized["month"],
                sanitized["year"],
                sanitized["category"],
                sanitized["amount"]
            ))
            conn.commit()
            
        return jsonify({"message": "Budget saved successfully.", "budget": sanitized}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to save budget: {str(e)}"}), 500


@app.route("/api/budget/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id: int):
    """Delete a specific budget entry."""
    try:
        execute_query("DELETE FROM budgets WHERE id = ?", (budget_id,))
        return jsonify({"message": "Budget deleted successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to delete budget: {str(e)}"}), 500


# --------------------------------------------------------------------------
# SAMPLE DATA & EXPORT ENDPOINTS
# --------------------------------------------------------------------------
@app.route("/api/sample-data", methods=["POST"])
def populate_sample_data():
    """Seed the database with sample transactions."""
    try:
        count = seed_demo_data(clear_existing=True)
        return jsonify({"message": f"Successfully loaded {count} demo transactions and budgets."})
    except Exception as e:
        return jsonify({"error": f"Failed to populate sample data: {str(e)}"}), 500


@app.route("/api/sample-data", methods=["DELETE"])
def reset_all_data():
    """Reset/Clear all expense records."""
    try:
        clear_all_data()
        return jsonify({"message": "All expense and budget records cleared successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to clear data: {str(e)}"}), 500


@app.route("/api/export", methods=["GET"])
def export_expenses():
    """Export expenses as CSV or JSON."""
    fmt = request.args.get("format", "csv").lower()
    rows = fetch_all("SELECT id, amount, category, description, date, payment_method, notes, created_at FROM expenses ORDER BY date DESC")
    
    if fmt == "json":
        return jsonify({"expenses": rows})
        
    # Generate CSV in memory
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Date", "Category", "Description", "Amount (INR)", "Payment Method", "Notes", "Created At"])
    
    for r in rows:
        writer.writerow([
            r["id"],
            r["date"],
            r["category"],
            r["description"],
            r["amount"],
            r["payment_method"],
            r["notes"],
            r["created_at"]
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=expenses_export.csv"}
    )


# --------------------------------------------------------------------------
# SETTINGS API
# --------------------------------------------------------------------------
@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get all settings."""
    rows = fetch_all("SELECT key, value FROM settings")
    return jsonify({r["key"]: r["value"] for r in rows})


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update settings key-values."""
    try:
        data = request.get_json() or {}
        with get_connection() as conn:
            cursor = conn.cursor()
            for k, v in data.items():
                cursor.execute("""
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = CURRENT_TIMESTAMP
                """, (k, str(v)))
            conn.commit()
        return jsonify({"message": "Settings updated successfully."})
    except Exception as e:
        return jsonify({"error": f"Failed to update settings: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 ExpenseAI Server starting on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
