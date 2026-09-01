"""
ExpenseAI - Live End-to-End Test & Verification Script
"""

import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import app
from backend.database import init_db
from backend.seed_data import seed_demo_data


def test_full_pipeline():
    print("[*] Starting live end-to-end verification...")
    init_db()
    seed_demo_data(clear_existing=True)
    
    client = app.test_client()
    
    # 1. Health
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.status_code}"
    print("✅ 1. /api/health passed")
    
    # 2. Metadata
    res = client.get("/api/metadata")
    assert res.status_code == 200
    assert "Food" in res.get_json()["categories"]
    print("✅ 2. /api/metadata passed")
    
    # 3. Create expense
    exp_payload = {
        "amount": 1450.0,
        "category": "Food",
        "description": "Team Buffet Lunch",
        "date": "2026-08-19",
        "payment_method": "UPI",
        "notes": "Verified lunch expense"
    }
    res = client.post("/api/expenses", json=exp_payload)
    assert res.status_code == 201
    created_id = res.get_json()["expense"]["id"]
    print("✅ 3. /api/expenses POST passed")
    
    # 4. Get and update expense
    res = client.get(f"/api/expenses/{created_id}")
    assert res.status_code == 200
    res = client.put(f"/api/expenses/{created_id}", json={"amount": 1600.0})
    assert res.status_code == 200
    assert res.get_json()["expense"]["amount"] == 1600.0
    print("✅ 4. /api/expenses/<id> PUT passed")
    
    # 5. Summary Analytics
    res = client.get("/api/analytics/summary?month=8&year=2026")
    assert res.status_code == 200
    summary = res.get_json()
    assert summary["this_month_total"] > 0
    assert summary["avg_daily_spending"] > 0
    assert summary["top_category"]["name"] != "None"
    print(f"✅ 5. /api/analytics/summary passed (Total: ₹{summary['this_month_total']:,.2f}, Top Cat: {summary['top_category']['name']})")
    
    # 6. Monthly Analytics
    res = client.get("/api/analytics/monthly?year=2026")
    assert res.status_code == 200
    monthly = res.get_json()
    assert len(monthly["monthly_breakdown"]) == 12
    assert monthly["total_yearly_spending"] > 0
    print(f"✅ 6. /api/analytics/monthly passed (Yearly Total: ₹{monthly['total_yearly_spending']:,.2f})")
    
    # 7. Category Analytics
    res = client.get("/api/analytics/categories?month=8&year=2026")
    assert res.status_code == 200
    cats = res.get_json()
    assert len(cats["categories"]) > 0
    print(f"✅ 7. /api/analytics/categories passed ({len(cats['categories'])} active categories)")
    
    # 8. Highest Analysis (Where is my money going)
    res = client.get("/api/analytics/highest")
    assert res.status_code == 200
    highest = res.get_json()
    assert highest["highest_individual_expense"] is not None
    print(f"✅ 8. /api/analytics/highest passed (Max: ₹{highest['highest_individual_expense']['amount']:,.2f} on {highest['highest_individual_expense']['description']})")
    
    # 9. AI Insights & Health Score
    res = client.get("/api/ai/insights?month=8&year=2026")
    assert res.status_code == 200
    ins = res.get_json()
    assert len(ins["insights"]) > 0
    print(f"✅ 9. /api/ai/insights passed ({len(ins['insights'])} generated insights)")
    
    res = client.get("/api/ai/health-score?month=8&year=2026")
    assert res.status_code == 200
    hs = res.get_json()
    assert 0 <= hs["score"] <= 100
    print(f"✅ 10. /api/ai/health-score passed (Score: {hs['score']}/100 - {hs['grade']})")
    
    res = client.get("/api/ai/predict?month=8&year=2026")
    assert res.status_code == 200
    pred = res.get_json()
    assert pred["estimated_month_end"] > 0
    print(f"✅ 11. /api/ai/predict passed (Projected: ₹{pred['estimated_month_end']:,.2f})")
    
    # 10. AI Chat
    res = client.post("/api/ai/chat", json={"query": "How can I cut my Food budget?"})
    assert res.status_code == 200
    chat_resp = res.get_json()
    assert len(chat_resp["reply"]) > 0
    print("✅ 12. /api/ai/chat passed")
    
    # 11. Budget
    res = client.get("/api/budget?month=8&year=2026")
    assert res.status_code == 200
    b_data = res.get_json()
    assert b_data["overall_budget"]["budget_amount"] > 0
    print(f"✅ 13. /api/budget passed (Budget: ₹{b_data['overall_budget']['budget_amount']:,.2f}, Spent: ₹{b_data['overall_budget']['spent_amount']:,.2f})")
    
    # 12. Frontend index serve
    res = client.get("/")
    assert res.status_code == 200
    assert "ExpenseAI" in res.data.decode("utf-8")
    print("✅ 14. Frontend Single-Page Application (index.html) served successfully")
    
    print("\n🎉 ALL 14 PIPELINE CHECKS PASSED WITH 100% SUCCESS!")


if __name__ == "__main__":
    test_full_pipeline()
