import sqlite3
import os
import math
import calendar
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional


def calculate_expense_health_score(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Calculate an Expense Health Score (0-100) based on:
    1. Budget Adherence (30 max)
    2. Category Diversification (25 max)
    3. MoM Spending Trajectory (25 max)
    4. Outlier / Impulse Control (20 max)
    """
    cursor = conn.cursor()
    today = date.today()
    curr_month_str = f"{today.year:04d}-{today.month:02d}"
    
    # 1. Check Budget Adherence (30 points)
    cursor.execute("SELECT value FROM settings WHERE key = 'monthly_budget'")
    budget_setting = cursor.fetchone()
    monthly_budget = float(budget_setting["value"]) if (budget_setting and budget_setting["value"]) else 35000.0
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE date LIKE ?", (f"{curr_month_str}%",))
    spent_row = cursor.fetchone()
    month_spent = float(spent_row["spent"])
    
    # Prorate budget based on day of month
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)
    expected_spend_to_date = (monthly_budget / days_in_month) * days_elapsed
    
    budget_score = 30
    budget_desc = ""
    if month_spent == 0:
        budget_score = 30
        budget_desc = "No expenses recorded this month yet."
    elif month_spent <= expected_spend_to_date:
        budget_score = 30
        budget_desc = f"Excellent pacing! You are within your prorated monthly budget of ₹{monthly_budget:,.0f}."
    elif month_spent <= monthly_budget:
        ratio = (month_spent - expected_spend_to_date) / (monthly_budget - expected_spend_to_date + 1)
        budget_score = max(10, int(30 - (ratio * 15)))
        budget_desc = f"You are currently slightly ahead of daily pacing for your ₹{monthly_budget:,.0f} budget."
    else:
        overage = month_spent - monthly_budget
        overage_pct = (overage / monthly_budget) * 100
        deduction = min(25, int(overage_pct / 4))
        budget_score = max(5, 30 - 15 - deduction)
        budget_desc = f"Monthly budget exceeded by ₹{overage:,.0f} ({overage_pct:.1f}%)."

    # 2. Category Concentration / Diversification (25 points)
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
        ORDER BY total DESC
    """, (f"{curr_month_str}%",))
    cat_rows = cursor.fetchall()
    
    diversification_score = 25
    div_desc = ""
    if not cat_rows or month_spent == 0:
        diversification_score = 25
        div_desc = "Balanced category distribution."
    else:
        top_cat_total = float(cat_rows[0]["total"])
        top_cat_name = cat_rows[0]["category"]
        top_cat_pct = (top_cat_total / month_spent) * 100
        
        # If rent, high concentration is normal. For discretionary (Shopping/Food), it warrants attention
        if top_cat_name in ["Rent"]:
            if top_cat_pct > 50:
                diversification_score = 20
                div_desc = f"Rent constitutes {top_cat_pct:.1f}% of your spending, which is common for housing."
            else:
                diversification_score = 25
                div_desc = "Well-balanced spending across essential and discretionary categories."
        else:
            if top_cat_pct > 45:
                diversification_score = 12
                div_desc = f"Heavy concentration in {top_cat_name} ({top_cat_pct:.1f}% of total). Spreading spend improves financial stability."
            elif top_cat_pct > 30:
                diversification_score = 18
                div_desc = f"{top_cat_name} represents {top_cat_pct:.1f}% of this month's spending."
            else:
                diversification_score = 25
                div_desc = "Excellent diversity across expense categories with no single dominant sink."

    # 3. MoM Spending Trajectory (25 points)
    if today.month == 1:
        prev_m_str = f"{today.year-1:04d}-12"
    else:
        prev_m_str = f"{today.year:04d}-{today.month-1:02d}"
        
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE date LIKE ?", (f"{prev_m_str}%",))
    prev_spent = float(cursor.fetchone()["total"])
    
    trajectory_score = 25
    traj_desc = ""
    if prev_spent == 0:
        trajectory_score = 22
        traj_desc = "Baseline tracking month. Future months will compare trajectory trends."
    else:
        # Projected full month comparison
        projected_current = (month_spent / days_elapsed) * days_in_month
        mom_diff_pct = ((projected_current - prev_spent) / prev_spent) * 100
        
        if mom_diff_pct <= 0:
            trajectory_score = 25
            traj_desc = f"Spending is trending {abs(mom_diff_pct):.1f}% lower or consistent compared to last month."
        elif mom_diff_pct <= 15:
            trajectory_score = 22
            traj_desc = f"Slight spending increase of {mom_diff_pct:.1f}% compared to last month."
        elif mom_diff_pct <= 35:
            trajectory_score = 15
            traj_desc = f"Spending pace is {mom_diff_pct:.1f}% higher than previous month."
        else:
            trajectory_score = 10
            traj_desc = f"Significant spending acceleration ({mom_diff_pct:.1f}% increase vs previous month)."

    # 4. Outlier & Impulse Control (20 points)
    cursor.execute("SELECT amount FROM expenses WHERE date LIKE ?", (f"{curr_month_str}%",))
    amounts = [float(r["amount"]) for r in cursor.fetchall()]
    
    outlier_score = 20
    outlier_desc = ""
    if len(amounts) < 3:
        outlier_score = 20
        outlier_desc = "Steady transaction amounts with no erratic spikes."
    else:
        avg_amt = sum(amounts) / len(amounts)
        variance = sum((x - avg_amt) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        
        # Outliers > avg + 2.5 * std_dev
        threshold = avg_amt + (2.5 * std_dev)
        outliers = [x for x in amounts if x > threshold and x > 2000]
        
        if not outliers:
            outlier_score = 20
            outlier_desc = "Consistent purchase sizes with good impulse control."
        elif len(outliers) == 1:
            outlier_score = 16
            outlier_desc = f"1 large transaction identified (₹{outliers[0]:,.0f})."
        else:
            outlier_score = max(8, 20 - (len(outliers) * 4))
            outlier_desc = f"{len(outliers)} unusually large individual purchases flagged this month."

    total_score = min(100, max(0, budget_score + diversification_score + trajectory_score + outlier_score))
    
    if total_score >= 85:
        rating = "Excellent"
        summary = "Outstanding financial management! Spending is well-controlled, diverse, and within budget."
    elif total_score >= 70:
        rating = "Good"
        summary = "Healthy spending profile with manageable variance. Minor optimizations possible in top categories."
    elif total_score >= 50:
        rating = "Fair"
        summary = "Moderate financial health. Consider reviewing top spending categories and establishing tighter caps."
    else:
        rating = "Needs Attention"
        summary = "High spending acceleration or budget overages detected. Active budget recalibration recommended."

    factors = [
        {
            "factor_name": "Budget Adherence",
            "score": budget_score,
            "max_score": 30,
            "status": "success" if budget_score >= 25 else "warning" if budget_score >= 15 else "critical",
            "description": budget_desc
        },
        {
            "factor_name": "Category Diversification",
            "score": diversification_score,
            "max_score": 25,
            "status": "success" if diversification_score >= 20 else "warning" if diversification_score >= 15 else "critical",
            "description": div_desc
        },
        {
            "factor_name": "Spending Trajectory",
            "score": trajectory_score,
            "max_score": 25,
            "status": "success" if trajectory_score >= 20 else "warning" if trajectory_score >= 15 else "critical",
            "description": traj_desc
        },
        {
            "factor_name": "Impulse & Outlier Control",
            "score": outlier_score,
            "max_score": 20,
            "status": "success" if outlier_score >= 16 else "warning" if outlier_score >= 12 else "critical",
            "description": outlier_desc
        }
    ]

    return {
        "score": total_score,
        "rating": rating,
        "summary": summary,
        "factors": factors
    }


def generate_ai_insights(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Generate dynamic, intelligent, and actionable insights based on actual expense data:
    1. Spending Pattern Analysis (MoM changes)
    2. Category Alerts (disproportionate share)
    3. Positive Feedback (reduced spending)
    4. Budget Suggestions (recommended targets)
    5. Anomaly Detection (unusual transactions)
    6. Recurring Expense Detection
    """
    cursor = conn.cursor()
    today = date.today()
    curr_month_str = f"{today.year:04d}-{today.month:02d}"
    
    if today.month == 1:
        prev_month_str = f"{today.year-1:04d}-12"
    else:
        prev_month_str = f"{today.year:04d}-{today.month-1:02d}"

    insights: List[Dict[str, Any]] = []

    # 1. Total this month vs last month comparison
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total, COUNT(id) as cnt FROM expenses WHERE date LIKE ?", (f"{curr_month_str}%",))
    curr_m = cursor.fetchone()
    curr_total = float(curr_m["total"])
    curr_count = int(curr_m["cnt"])

    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total, COUNT(id) as cnt FROM expenses WHERE date LIKE ?", (f"{prev_month_str}%",))
    prev_m = cursor.fetchone()
    prev_total = float(prev_m["total"])

    if curr_total > 0 and prev_total > 0:
        diff_pct = round(((curr_total - prev_total) / prev_total) * 100, 1)
        if diff_pct > 15:
            insights.append({
                "id": "pattern-spending-spike",
                "type": "pattern",
                "title": "Overall Spending Acceleration",
                "message": f"Your total expenses this month (₹{curr_total:,.0f}) are {diff_pct}% higher than last month (₹{prev_total:,.0f}).",
                "severity": "warning",
                "icon": "trending-up",
                "action_tip": "Review your highest non-essential transactions to identify spontaneous purchases."
            })
        elif diff_pct < -10:
            insights.append({
                "id": "positive-overall-reduction",
                "type": "positive",
                "title": "Reduced Monthly Spending",
                "message": f"Impressive control! Your expenses this month are {abs(diff_pct)}% lower compared to last month at this stage.",
                "severity": "success",
                "icon": "shield-check",
                "action_tip": "Maintain this trajectory to allocate remaining funds into your savings or emergency fund."
            })

    # 2. Category-Level MoM Shift & Category Alerts
    cursor.execute("""
        SELECT category, SUM(amount) as total, COUNT(id) as count
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
    """, (f"{curr_month_str}%",))
    curr_cats = {r["category"]: {"total": float(r["total"]), "count": int(r["count"])} for r in cursor.fetchall()}

    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date LIKE ?
        GROUP BY category
    """, (f"{prev_month_str}%",))
    prev_cats = {r["category"]: float(r["total"]) for r in cursor.fetchall()}

    # Check for categories with notable spikes or high concentration
    for cat, data in curr_cats.items():
        cat_total = data["total"]
        pct_of_total = (cat_total / curr_total * 100) if curr_total > 0 else 0
        
        # High category concentration alert
        if pct_of_total >= 30 and cat not in ["Rent"]:
            insights.append({
                "id": f"alert-concentration-{cat.lower()}",
                "type": "alert",
                "title": f"High Concentration in {cat}",
                "message": f"{cat} is currently taking {pct_of_total:.1f}% of your monthly expenses (₹{cat_total:,.0f}).",
                "severity": "warning",
                "icon": "alert-triangle",
                "action_tip": f"Setting a dedicated budget cap for {cat} can help rebalance your spending profile."
            })

        # Category MoM shift
        if cat in prev_cats and prev_cats[cat] > 0:
            c_prev = prev_cats[cat]
            c_diff_pct = round(((cat_total - c_prev) / c_prev) * 100, 1)
            
            if c_diff_pct >= 25 and cat_total > 1500:
                insights.append({
                    "id": f"pattern-{cat.lower()}-increase",
                    "type": "pattern",
                    "title": f"{cat} Spending Increased",
                    "message": f"Your spending on {cat} increased by {c_diff_pct}% this month (₹{cat_total:,.0f} vs ₹{c_prev:,.0f} last month).",
                    "severity": "info",
                    "icon": "arrow-up-right",
                    "action_tip": f"Check your recent {cat} entries to see if this represents a one-off purchase or recurring lifestyle shift."
                })
            elif c_diff_pct <= -20 and c_prev > 1500:
                insights.append({
                    "id": f"positive-{cat.lower()}-decrease",
                    "type": "positive",
                    "title": f"{cat} Spending Decreased",
                    "message": f"Your {cat} spending decreased by {abs(c_diff_pct)}% compared with last month (₹{cat_total:,.0f} vs ₹{c_prev:,.0f}).",
                    "severity": "success",
                    "icon": "thumbs-up",
                    "action_tip": "Keep up these mindful spending habits in this category."
                })

    # 3. Statistical Anomaly Detection (Unusual Transactions)
    cursor.execute("""
        SELECT id, amount, category, description, date, payment_method
        FROM expenses
        ORDER BY date DESC
        LIMIT 100
    """)
    recent_txs = [dict(r) for r in cursor.fetchall()]
    
    if len(recent_txs) >= 5:
        amounts = [t["amount"] for t in recent_txs]
        avg_amt = sum(amounts) / len(amounts)
        variance = sum((x - avg_amt) ** 2 for x in amounts) / len(amounts)
        std_dev = math.sqrt(variance)
        anomaly_cutoff = max(avg_amt + (2.2 * std_dev), avg_amt * 2.8)
        
        anomalies = [t for t in recent_txs if t["amount"] > anomaly_cutoff and t["category"] not in ["Rent"]]
        if anomalies:
            top_anomaly = anomalies[0]
            insights.append({
                "id": f"anomaly-tx-{top_anomaly['id']}",
                "type": "anomaly",
                "title": "Unusual Transaction Detected",
                "message": f"A single expense of ₹{top_anomaly['amount']:,.0f} for '{top_anomaly['description']}' ({top_anomaly['category']}) on {top_anomaly['date']} is significantly above your average transaction size of ₹{avg_amt:,.0f}.",
                "severity": "warning",
                "icon": "zap",
                "action_tip": "Verify if this was an anticipated annual/one-off expense or an unplanned purchase."
            })

    # 4. Smart Budget Suggestions based on 3-month rolling averages
    cursor.execute("""
        SELECT category, AVG(monthly_sum) as avg_monthly
        FROM (
            SELECT category, strftime('%Y-%m', date) as ym, SUM(amount) as monthly_sum
            FROM expenses
            GROUP BY category, ym
        )
        GROUP BY category
        HAVING avg_monthly > 1000
        ORDER BY avg_monthly DESC
        LIMIT 2
    """)
    suggested_budget_cats = cursor.fetchall()
    for row in suggested_budget_cats:
        c_name = row["category"]
        c_avg = float(row["avg_monthly"])
        recommended_cap = math.ceil((c_avg * 0.95) / 500.0) * 500  # Rounded to nearest 500
        insights.append({
            "id": f"suggestion-budget-{c_name.lower()}",
            "type": "suggestion",
            "title": f"Budget Suggestion for {c_name}",
            "message": f"Based on your historical spending average of ₹{c_avg:,.0f}/month on {c_name}, establishing a monthly target of ₹{recommended_cap:,.0f} could optimize your monthly cash flow.",
            "severity": "info",
            "icon": "target",
            "action_tip": f"You can set a formal monthly limit in the Budget section."
        })

    # 5. Recurring Expense Detector
    cursor.execute("""
        SELECT description, category, amount, COUNT(DISTINCT strftime('%Y-%m', date)) as months_seen
        FROM expenses
        GROUP BY LOWER(description), category, amount
        HAVING months_seen >= 2
        ORDER BY amount DESC
        LIMIT 2
    """)
    recurring = cursor.fetchall()
    for r in recurring:
        insights.append({
            "id": f"pattern-recurring-{r['category'].lower()}",
            "type": "pattern",
            "title": f"Recurring Expense Identified",
            "message": f"'{r['description']}' (₹{r['amount']:,.0f} in {r['category']}) occurs regularly across multiple months.",
            "severity": "info",
            "icon": "repeat",
            "action_tip": "Account for this in your baseline fixed monthly commitments."
        })

    # 6. Fallback insight if dataset is still sparse
    if not insights:
        insights.append({
            "id": "welcome-insight",
            "type": "suggestion",
            "title": "AI Expense Engine Active",
            "message": "ExpenseAI is monitoring your spending patterns. As you log transactions across categories, deeper pattern recognition, anomaly detection, and budget alerts will appear here in real time.",
            "severity": "info",
            "icon": "sparkles",
            "action_tip": "Log your daily expenses consistently to unlock personalized spending intelligence."
        })

    return insights


def calculate_prediction(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Project expected total monthly spend based on current run rate & calendar days.
    """
    today = date.today()
    curr_month_str = f"{today.year:04d}-{today.month:02d}"
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_elapsed = max(1, today.day)
    days_remaining = days_in_month - days_elapsed

    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE date LIKE ?", (f"{curr_month_str}%",))
    current_spent = float(cursor.fetchone()["spent"])

    daily_burn_rate = current_spent / days_elapsed
    projected_additional = daily_burn_rate * days_remaining
    estimated_eom_total = round(current_spent + projected_additional, 2)

    # Budget comparison
    cursor.execute("SELECT value FROM settings WHERE key = 'monthly_budget'")
    budget_setting = cursor.fetchone()
    monthly_budget = float(budget_setting["value"]) if (budget_setting and budget_setting["value"]) else 35000.0

    budget_comp = {
        "monthly_budget": monthly_budget,
        "is_projected_over": estimated_eom_total > monthly_budget,
        "variance_amount": round(abs(estimated_eom_total - monthly_budget), 2),
        "variance_pct": round(((estimated_eom_total - monthly_budget) / monthly_budget) * 100, 1) if monthly_budget > 0 else 0
    }

    return {
        "current_spent": round(current_spent, 2),
        "estimated_eom_total": estimated_eom_total,
        "projected_additional_spend": round(projected_additional, 2),
        "daily_burn_rate": round(daily_burn_rate, 2),
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "budget_comparison": budget_comp,
        "disclaimer": "Estimate based on current daily spending velocity. Discretionary expenses and irregular bill dates may alter final actual totals."
    }
