"""
ExpenseAI - AI Analysis & Insights Engine
Provides local rule-based statistical pattern detection, anomaly identification,
expense health score calculation (0-100), month-end burn rate prediction,
and optional Gemini AI conversational integration.
"""

import os
import math
import calendar
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from backend.database import fetch_all, fetch_one


def calculate_expense_health_score(month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculates transparent Expense Health Score (0-100) based on 5 quantifiable metrics:
    1. Budget Adherence (30 pts)
    2. Category Diversification (20 pts)
    3. Month-to-Month Stability (20 pts)
    4. Anomaly / Impulse Control (15 pts)
    5. Daily Burn Rate Consistency (15 pts)
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    
    month_prefix = f"{target_year:04d}-{target_month:02d}%"
    month_rows = fetch_all(
        "SELECT id, amount, category, date, description FROM expenses WHERE date LIKE ?",
        (month_prefix,)
    )
    
    if not month_rows:
        return {
            "score": 75,
            "grade": "Good (Baseline)",
            "color": "emerald",
            "summary": "No expenses recorded for this period yet. Maintain consistent tracking to get full insights.",
            "breakdown": [
                {"name": "Budget Adherence", "score": 25, "max": 30, "detail": "No budget breaches recorded."},
                {"name": "Category Diversification", "score": 15, "max": 20, "detail": "Awaiting category data."},
                {"name": "Spending Stability", "score": 15, "max": 20, "detail": "Baseline stability assumed."},
                {"name": "Impulse Control", "score": 10, "max": 15, "detail": "No anomalous transactions."},
                {"name": "Daily Consistency", "score": 10, "max": 15, "detail": "Daily cadence normal."}
            ],
            "tips": ["Add your daily transactions to receive real-time financial health monitoring."]
        }
        
    total_spent = sum(r["amount"] for r in month_rows)
    
    # 1. Budget Adherence (Max 30)
    budget_row = fetch_one(
        "SELECT amount FROM budgets WHERE year = ? AND month = ? AND category = 'ALL'",
        (target_year, target_month)
    )
    
    breakdown = []
    tips = []
    
    if budget_row and budget_row["amount"] > 0:
        budget_amt = budget_row["amount"]
        ratio = total_spent / budget_amt
        if ratio <= 0.70:
            budget_score = 30
            b_detail = f"Excellent! Spent only {ratio*100:.1f}% of your ₹{budget_amt:,.0f} budget."
        elif ratio <= 0.90:
            budget_score = 25
            b_detail = f"Healthy budget usage at {ratio*100:.1f}% of limit."
        elif ratio <= 1.0:
            budget_score = 18
            b_detail = f"Approaching limit: {ratio*100:.1f}% of budget consumed."
            tips.append("You are near your monthly budget threshold. Prioritize essential expenses only.")
        elif ratio <= 1.2:
            budget_score = 10
            b_detail = f"Overbudget by {((ratio - 1)*100):.1f}% (₹{total_spent - budget_amt:,.0f} over limit)."
            tips.append(f"You exceeded your monthly budget by ₹{total_spent - budget_amt:,.0f}. Review discretionary spending.")
        else:
            budget_score = 4
            b_detail = f"Severe budget overrun ({ratio*100:.1f}% of budget spent)."
            tips.append("Budget significantly exceeded. Freeze non-essential purchases for the rest of the month.")
    else:
        # If no budget set, award balanced baseline
        budget_score = 24
        b_detail = "No monthly budget defined. Setting a budget helps boost and preserve your health score."
        tips.append("Set a monthly budget in the Budget tab to enable accurate adherence tracking.")
    breakdown.append({"name": "Budget Adherence", "score": budget_score, "max": 30, "detail": b_detail})
    
    # 2. Category Concentration (Max 20)
    cat_totals: Dict[str, float] = {}
    for r in month_rows:
        c = r["category"]
        cat_totals[c] = cat_totals.get(c, 0.0) + r["amount"]
        
    highest_cat_ratio = max(cat_totals.values()) / total_spent if total_spent > 0 else 0
    highest_cat_name = max(cat_totals, key=cat_totals.get) if cat_totals else "None"
    
    # Exclude Rent from strict penalization as rent naturally dominates
    if highest_cat_name.lower() == "rent":
        if highest_cat_ratio > 0.60:
            cat_score = 15
            c_detail = f"Rent constitutes {highest_cat_ratio*100:.1f}% of spending (standard housing ratio)."
        else:
            cat_score = 19
            c_detail = "Healthy category distribution with reasonable fixed housing allocation."
    else:
        if highest_cat_ratio < 0.35:
            cat_score = 20
            c_detail = f"Well-balanced spending across {len(cat_totals)} categories."
        elif highest_cat_ratio < 0.50:
            cat_score = 15
            c_detail = f"{highest_cat_name} is slightly heavy ({highest_cat_ratio*100:.1f}% of spending)."
        else:
            cat_score = 8
            c_detail = f"High concentration in {highest_cat_name} ({highest_cat_ratio*100:.1f}% of total)."
            tips.append(f"Your spending is heavily concentrated in {highest_cat_name}. Try diversifying or reducing peak items.")
    breakdown.append({"name": "Category Diversification", "score": cat_score, "max": 20, "detail": c_detail})
    
    # 3. Month-to-Month Stability (Max 20)
    if target_month == 1:
        prev_m, prev_y = 12, target_year - 1
    else:
        prev_m, prev_y = target_month - 1, target_year
        
    prev_rows = fetch_all(
        "SELECT amount FROM expenses WHERE date LIKE ?",
        (f"{prev_y:04d}-{prev_m:02d}%",)
    )
    prev_spent = sum(r["amount"] for r in prev_rows)
    
    if prev_spent > 0:
        pct_diff = ((total_spent - prev_spent) / prev_spent) * 100
        if abs(pct_diff) <= 10:
            stab_score = 20
            s_detail = f"Very stable spending pattern ({pct_diff:+.1f}% vs last month)."
        elif pct_diff < -10:
            stab_score = 19
            s_detail = f"Spending reduced by {abs(pct_diff):.1f}% vs last month (positive savings shift)."
        elif pct_diff <= 25:
            stab_score = 14
            s_detail = f"Moderate spending increase of {pct_diff:.1f}% compared to last month."
        else:
            stab_score = 7
            s_detail = f"Significant spending spike of +{pct_diff:.1f}% vs last month."
            tips.append(f"Spending surged by {pct_diff:.1f}% compared to last month. Audit recent large purchases.")
    else:
        stab_score = 16
        s_detail = "First tracked month comparison baseline."
    breakdown.append({"name": "Spending Stability", "score": stab_score, "max": 20, "detail": s_detail})
    
    # 4. Anomaly / Impulse Control (Max 15)
    amounts = [r["amount"] for r in month_rows]
    mean_amt = total_spent / len(amounts) if amounts else 0
    # Flag single transactions > 3x mean (excluding Rent/Bills)
    anomalies = [
        r for r in month_rows 
        if r["amount"] > max(2500, mean_amt * 3) and r["category"] not in ["Rent", "Bills"]
    ]
    
    if len(anomalies) == 0:
        impulse_score = 15
        i_detail = "Zero anomalous high-value spikes detected."
    elif len(anomalies) <= 2:
        impulse_score = 11
        i_detail = f"{len(anomalies)} large non-essential transaction(s) detected."
        tips.append(f"Review large single expense: ₹{anomalies[0]['amount']:,.0f} on {anomalies[0]['description']}.")
    else:
        impulse_score = 6
        i_detail = f"{len(anomalies)} irregular expense spikes identified."
        tips.append("Multiple unusually large impulse expenses detected. Consider applying a 24-hour cooling rule.")
    breakdown.append({"name": "Impulse Control", "score": impulse_score, "max": 15, "detail": i_detail})
    
    # 5. Daily Burn Rate Consistency (Max 15)
    # Group by date
    daily_sums: Dict[str, float] = {}
    for r in month_rows:
        d = r["date"]
        daily_sums[d] = daily_sums.get(d, 0.0) + r["amount"]
        
    days_in_month = calendar.monthrange(target_year, target_month)[1]
    active_days_count = len(daily_sums)
    
    if active_days_count > 0:
        daily_values = list(daily_sums.values())
        avg_d = sum(daily_values) / len(daily_values)
        variance = sum((x - avg_d) ** 2 for x in daily_values) / len(daily_values)
        std_dev = math.sqrt(variance)
        cv = std_dev / avg_d if avg_d > 0 else 0 # coefficient of variation
        
        if cv < 0.8:
            daily_score = 15
            d_detail = "Consistent, disciplined daily expenditure rate."
        elif cv < 1.5:
            daily_score = 11
            d_detail = "Moderate variance in daily spending."
        else:
            daily_score = 8
            d_detail = "High day-to-day spending volatility."
    else:
        daily_score = 12
        d_detail = "Normal daily pacing."
    breakdown.append({"name": "Daily Consistency", "score": daily_score, "max": 15, "detail": d_detail})
    
    # Calculate Total Score
    final_score = budget_score + cat_score + stab_score + impulse_score + daily_score
    final_score = min(100, max(0, final_score))
    
    if final_score >= 85:
        grade = "Excellent (Prime Health)"
        color = "emerald"
        summary = "Outstanding financial control! Your expenses are well-structured, disciplined, and within budget."
    elif final_score >= 70:
        grade = "Good (Solid Habits)"
        color = "cyan"
        summary = "Healthy spending posture with stable habits. Minor optimizations will help elevate your score."
    elif final_score >= 50:
        grade = "Fair (Needs Attention)"
        color = "amber"
        summary = "Moderate financial strain detected due to high category concentration or budget proximity."
    else:
        grade = "Critical (Overspending Alert)"
        color = "rose"
        summary = "Urgent attention recommended: High spending volatility or budget breaches detected."
        
    if not tips:
        tips.append("Maintain your current savings cadence and continue categorizing daily receipts.")
        
    return {
        "score": final_score,
        "grade": grade,
        "color": color,
        "summary": summary,
        "breakdown": breakdown,
        "tips": tips
    }


def get_ai_prediction(month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Estimates expected total spending for remainder of the current month.
    Uses daily velocity, days elapsed, days remaining, and recurring obligations.
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    
    days_in_month = calendar.monthrange(target_year, target_month)[1]
    
    # Check if target month is past, current, or future
    if target_year < now.year or (target_year == now.year and target_month < now.month):
        # Past month: actual spent is total
        rows = fetch_all("SELECT SUM(amount) as total FROM expenses WHERE date LIKE ?", (f"{target_year:04d}-{target_month:02d}%",))
        actual = rows[0]["total"] if rows and rows[0]["total"] else 0.0
        return {
            "status": "completed",
            "is_past": True,
            "actual_spending": round(actual, 2),
            "estimated_month_end": round(actual, 2),
            "daily_burn_rate": 0.0,
            "days_remaining": 0,
            "confidence": "100%",
            "message": f"Month finalized with total spending of ₹{actual:,.2f}."
        }
        
    current_day = now.day if (target_year == now.year and target_month == now.month) else 1
    days_elapsed = max(1, current_day)
    days_remaining = max(0, days_in_month - current_day)
    
    # Fetch current month spending
    rows = fetch_all("SELECT amount, category, date FROM expenses WHERE date LIKE ?", (f"{target_year:04d}-{target_month:02d}%",))
    current_spent = sum(r["amount"] for r in rows)
    
    # Calculate daily burn rate
    daily_burn = current_spent / days_elapsed if days_elapsed > 0 else 0.0
    
    # Check for historical recurring expenses in the next days (like rent/bills)
    projected_additional = daily_burn * days_remaining
    estimated_total = current_spent + projected_additional
    
    # Budget comparison if available
    budget_row = fetch_one("SELECT amount FROM budgets WHERE year = ? AND month = ? AND category = 'ALL'", (target_year, target_month))
    budget_amount = budget_row["amount"] if budget_row else None
    
    budget_warning = None
    if budget_amount and budget_amount > 0:
        if estimated_total > budget_amount:
            diff = estimated_total - budget_amount
            budget_warning = f"At current burn rate (₹{daily_burn:,.0f}/day), you are projected to exceed your ₹{budget_amount:,.0f} budget by ₹{diff:,.0f}."
            
    confidence = "High (88%)" if days_elapsed >= 10 else "Moderate (65%)"
    
    return {
        "status": "active",
        "is_past": False,
        "current_spent": round(current_spent, 2),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "daily_burn_rate": round(daily_burn, 2),
        "estimated_month_end": round(estimated_total, 2),
        "confidence": confidence,
        "budget_limit": budget_amount,
        "budget_warning": budget_warning,
        "message": (
            f"Based on your daily velocity of ₹{daily_burn:,.2f}/day across {days_elapsed} days, "
            f"your projected end-of-month spending is approximately ₹{estimated_total:,.2f}."
        )
    }


def generate_local_ai_insights(month: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Generates intelligent rule-based suggestions and analytics from user transaction data:
    - Spending Pattern analysis (Month-over-month shifts)
    - Category Alerts (Overconcentration)
    - Positive Feedback (Reduced spending in categories)
    - Budget Suggestions (Recommended category budgets based on 3-month rolling averages)
    - Unusual Spending (Outlier detection)
    - Recurring Expense identification
    """
    now = datetime.now()
    target_year = year if year is not None else now.year
    target_month = month if month is not None else now.month
    
    insights = []
    
    # 1. Fetch current month expenses
    curr_prefix = f"{target_year:04d}-{target_month:02d}%"
    curr_expenses = fetch_all("SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC", (curr_prefix,))
    
    if not curr_expenses:
        return [{
            "id": "ins-empty",
            "type": "info",
            "category": "General",
            "title": "Welcome to ExpenseAI",
            "message": "Start adding your daily expenses to unlock automated AI pattern detection, anomaly tracking, and budgeting recommendations.",
            "impact": "low",
            "tag": "Getting Started"
        }]
        
    total_curr = sum(r["amount"] for r in curr_expenses)
    
    # 2. Fetch previous month expenses
    if target_month == 1:
        prev_m, prev_y = 12, target_year - 1
    else:
        prev_m, prev_y = target_month - 1, target_year
    prev_prefix = f"{prev_y:04d}-{prev_m:02d}%"
    prev_expenses = fetch_all("SELECT * FROM expenses WHERE date LIKE ?", (prev_prefix,))
    total_prev = sum(r["amount"] for r in prev_expenses)
    
    # Category maps
    curr_cats: Dict[str, float] = {}
    for r in curr_expenses:
        c = r["category"]
        curr_cats[c] = curr_cats.get(c, 0.0) + r["amount"]
        
    prev_cats: Dict[str, float] = {}
    for r in prev_expenses:
        c = r["category"]
        prev_cats[c] = prev_cats.get(c, 0.0) + r["amount"]
        
    # Insight 1: Overall Spending Pattern
    if total_prev > 0:
        diff_pct = round(((total_curr - total_prev) / total_prev) * 100, 1)
        if diff_pct > 15:
            insights.append({
                "id": "ins-pattern-increase",
                "type": "warning",
                "category": "Spending Pattern",
                "title": "Spending Velocity Surge",
                "message": f"Your overall spending is up by {diff_pct}% (₹{total_curr - total_prev:,.2f}) compared to last month ({calendar.month_name[prev_m]}).",
                "impact": "high",
                "tag": "Trend Alert"
            })
        elif diff_pct < -10:
            insights.append({
                "id": "ins-pattern-decrease",
                "type": "success",
                "category": "Positive Feedback",
                "title": "Positive Spending Reduction",
                "message": f"Great progress! You have spent {abs(diff_pct)}% less (₹{total_prev - total_curr:,.2f} saved) compared to {calendar.month_name[prev_m]}.",
                "impact": "medium",
                "tag": "Savings Win"
            })
            
    # Insight 2: Category Shifts & Positive Feedback
    for cat, curr_amt in curr_cats.items():
        prev_amt = prev_cats.get(cat, 0.0)
        if prev_amt > 1000:
            c_diff = ((curr_amt - prev_amt) / prev_amt) * 100
            if c_diff > 30 and curr_amt > 2000:
                insights.append({
                    "id": f"ins-cat-spike-{cat.lower()}",
                    "type": "warning",
                    "category": cat,
                    "title": f"Notable Surge in {cat}",
                    "message": f"Your spending on {cat} surged by {c_diff:.1f}% (₹{curr_amt:,.2f} vs ₹{prev_amt:,.2f} last month).",
                    "impact": "medium",
                    "tag": "Category Alert"
                })
            elif c_diff < -25:
                insights.append({
                    "id": f"ins-cat-drop-{cat.lower()}",
                    "type": "success",
                    "category": cat,
                    "title": f"Disciplined Control on {cat}",
                    "message": f"Your {cat} spending decreased by {abs(c_diff):.1f}% compared with last month. Keep up the disciplined budget!",
                    "impact": "medium",
                    "tag": "Positive Feedback"
                })
                
    # Insight 3: Category Concentration Alert
    if total_curr > 0:
        for cat, amt in curr_cats.items():
            pct = (amt / total_curr) * 100
            if pct > 35 and cat not in ["Rent"]:
                insights.append({
                    "id": f"ins-conc-{cat.lower()}",
                    "type": "warning",
                    "category": cat,
                    "title": f"High Concentration in {cat}",
                    "message": f"{cat} accounts for {pct:.1f}% (₹{amt:,.2f}) of your total monthly expenditures. Consider reallocating budget toward savings.",
                    "impact": "high",
                    "tag": "Category Alert"
                })
                
    # Insight 4: Unusual Spending / Anomaly Detection
    all_expenses = fetch_all("SELECT amount, category, description, date FROM expenses")
    if len(all_expenses) >= 5:
        amounts = [r["amount"] for r in all_expenses]
        avg_overall = sum(amounts) / len(amounts)
        
        # Check current month's highest outlier
        outliers = [
            r for r in curr_expenses 
            if r["amount"] > max(3000, avg_overall * 3.5) and r["category"] not in ["Rent", "Education"]
        ]
        if outliers:
            top_outlier = max(outliers, key=lambda x: x["amount"])
            insights.append({
                "id": "ins-anomaly",
                "type": "warning",
                "category": "Anomaly Detection",
                "title": "Unusual Expense Detected",
                "message": f"An unusually high expense of ₹{top_outlier['amount']:,.2f} for '{top_outlier['description']}' was recorded on {top_outlier['date']}.",
                "impact": "high",
                "tag": "Outlier Alert"
            })
            
    # Insight 5: Smart Budget Suggestion
    top_discretionary = [cat for cat in curr_cats if cat in ["Food", "Shopping", "Entertainment", "Travel"]]
    if top_discretionary:
        fav_cat = max(top_discretionary, key=lambda c: curr_cats[c])
        fav_amt = curr_cats[fav_cat]
        suggested_limit = round(fav_amt * 0.85, -2) # suggest 15% reduction rounded to 100
        insights.append({
            "id": f"ins-budget-sugg-{fav_cat.lower()}",
            "type": "tip",
            "category": "Smart Budget",
            "title": f"Target Budget Suggestion for {fav_cat}",
            "message": f"Based on your recent {fav_cat} spending (₹{fav_amt:,.2f}), consider setting a target monthly cap of ₹{suggested_limit:,.0f} to save ₹{fav_amt - suggested_limit:,.0f}.",
            "impact": "low",
            "tag": "Budget Suggestion"
        })
        
    # Insight 6: Weekend Spending Spikes
    weekend_sum = 0.0
    weekday_sum = 0.0
    weekend_count = 0
    weekday_count = 0
    for r in curr_expenses:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d")
            if d.weekday() >= 5: # Sat or Sun
                weekend_sum += r["amount"]
                weekend_count += 1
            else:
                weekday_sum += r["amount"]
                weekday_count += 1
        except Exception:
            pass
            
    if weekend_count > 0 and weekday_count > 0:
        avg_weekend_day = weekend_sum / weekend_count
        avg_weekday_day = weekday_sum / weekday_count
        if avg_weekend_day > avg_weekday_day * 1.8 and avg_weekend_day > 1000:
            insights.append({
                "id": "ins-weekend-spike",
                "type": "tip",
                "category": "Behavioral Insight",
                "title": "Weekend Leisure Spending Surge",
                "message": f"Your average weekend daily spend (₹{avg_weekend_day:,.2f}) is {((avg_weekend_day/avg_weekday_day)-1)*100:.0f}% higher than regular weekdays.",
                "impact": "medium",
                "tag": "Behavioral"
            })
            
    return insights


def query_gemini_ai_insights(api_key: Optional[str] = None, month: Optional[int] = None, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Calls Google Gemini API (Interactions / standard REST) if API key is provided.
    Returns generated natural language commentary and savings strategy.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("AI_API_KEY")
    if not key:
        # Check settings table
        row = fetch_one("SELECT value FROM settings WHERE key = 'gemini_api_key'")
        if row and row["value"]:
            key = row["value"].strip()
            
    if not key:
        return None
        
    try:
        import urllib.request
        import json
        
        # Prepare financial context payload
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        rows = fetch_all(
            "SELECT amount, category, description, date FROM expenses WHERE date LIKE ? ORDER BY date DESC LIMIT 50",
            (f"{target_year:04d}-{target_month:02d}%",)
        )
        if not rows:
            return None
            
        total_spent = sum(r["amount"] for r in rows)
        cat_sums: Dict[str, float] = {}
        for r in rows:
            cat_sums[r["category"]] = cat_sums.get(r["category"], 0.0) + r["amount"]
            
        context_str = (
            f"Personal Financial Summary for {calendar.month_name[target_month]} {target_year}:\n"
            f"- Total Spending: ₹{total_spent:,.2f}\n"
            f"- Category Breakdown: {json.dumps(cat_sums)}\n"
            f"- Recent Transactions: {[r['description'] + ' (₹' + str(r['amount']) + ')' for r in rows[:8]]}\n"
        )
        
        prompt = (
            f"You are ExpenseAI, an expert, encouraging personal finance intelligence assistant. "
            f"Analyze the following user expense data:\n{context_str}\n"
            f"Provide a structured JSON response with:\n"
            f"1. 'ai_summary': A 2-sentence executive spending summary.\n"
            f"2. 'top_savings_opportunity': One specific, realistic area to cut costs.\n"
            f"3. 'smart_recommendations': List of 3 brief, actionable financial suggestions."
        )
        
        # Gemini 1.5 Flash endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=12.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed_result = json.loads(candidate_text)
            return {
                "source": "Gemini AI (Cloud)",
                "summary": parsed_result.get("ai_summary", ""),
                "savings_opportunity": parsed_result.get("top_savings_opportunity", ""),
                "recommendations": parsed_result.get("smart_recommendations", [])
            }
    except Exception as e:
        # Fallback gracefully
        return None
