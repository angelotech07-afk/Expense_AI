import os
import sys
import unittest

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.app import app
from backend.database import init_db
from backend.seed_data import seed_database, clear_database

client = TestClient(app)

class TestExpenseAI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Initialize and seed clean database for testing."""
        init_db()
        seed_database(force=True)

    def test_01_summary_analytics(self):
        """Test summary KPI calculation."""
        response = client.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_expenses", data)
        self.assertGreater(data["total_expenses"], 0)
        self.assertIn("this_month_expenses", data)
        self.assertIn("avg_daily_spending", data)
        self.assertIn("top_category", data)
        self.assertEqual(data["currency_symbol"], "₹")
        print(f"  [PASS] Summary KPIs verified (Total: INR {data['total_expenses']:,.2f}, Top Cat: {data['top_category']['category']})")

    def test_02_monthly_breakdown(self):
        """Test month-by-month calculations for all 12 months."""
        response = client.get("/api/analytics/monthly?year=2026")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["months"]), 12)
        self.assertGreater(data["total_year_spending"], 0)
        self.assertIsNotNone(data["highest_month"])
        print(f"  [PASS] Monthly breakdown verified (12 months, Total: INR {data['total_year_spending']:,.2f})")

    def test_03_category_breakdown(self):
        """Test category spending distribution and percentages."""
        response = client.get("/api/analytics/categories")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["categories"]), 0)
        
        # Verify percentages sum up to ~100%
        total_pct = sum(c["percentage"] for c in data["categories"])
        self.assertAlmostEqual(total_pct, 100.0, delta=1.5)
        print(f"  [PASS] Category breakdown verified ({len(data['categories'])} categories, Sum %: {total_pct:.1f}%)")

    def test_04_where_money_goes(self):
        """Test 'Where Is My Money Going?' aggregations."""
        response = client.get("/api/analytics/where-money-goes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data["highest_individual_expense"])
        self.assertIsNotNone(data["highest_category"])
        self.assertIsNotNone(data["highest_spending_day"])
        self.assertGreater(len(data["top_recent_large_expenses"]), 0)
        print(f"  [PASS] 'Where Is My Money Going?' verified (Peak single: INR {data['highest_individual_expense']['amount']:,.2f})")

    def test_05_ai_insights_and_health_score(self):
        """Test AI insights, Health Score (0-100), and prediction forecast."""
        # 1. AI Insights
        res_insights = client.get("/api/ai/insights")
        self.assertEqual(res_insights.status_code, 200)
        insights_data = res_insights.json()
        self.assertIn("insights", insights_data)
        self.assertGreater(len(insights_data["insights"]), 0)
        
        # 2. Health Score
        res_health = client.get("/api/ai/health-score")
        self.assertEqual(res_health.status_code, 200)
        health_data = res_health.json()
        self.assertGreaterEqual(health_data["score"], 0)
        self.assertLessEqual(health_data["score"], 100)
        self.assertEqual(len(health_data["factors"]), 4)

        # 3. Prediction
        res_pred = client.get("/api/ai/prediction")
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        self.assertIn("estimated_eom_total", pred_data)
        print(f"  [PASS] AI Engine verified (Health Score: {health_data['score']}/100, Forecast EOM: INR {pred_data['estimated_eom_total']:,.2f})")

    def test_06_crud_expense_workflow(self):
        """Test Create, Read, Filter, Update, and Delete on /api/expenses."""
        # Create
        new_exp = {
            "amount": 750.50,
            "category": "Food",
            "description": "Automated Test Dining Expense",
            "date": "2026-08-19",
            "payment_method": "UPI",
            "notes": "Unit test tag"
        }
        res_create = client.post("/api/expenses", json=new_exp)
        self.assertEqual(res_create.status_code, 201)
        created = res_create.json()
        exp_id = created["id"]
        self.assertEqual(created["amount"], 750.50)
        self.assertEqual(created["description"], "Automated Test Dining Expense")

        # Read single
        res_get = client.get(f"/api/expenses/{exp_id}")
        self.assertEqual(res_get.status_code, 200)

        # Filter
        res_filter = client.get("/api/expenses?search=Automated+Test")
        self.assertEqual(res_filter.status_code, 200)
        self.assertGreaterEqual(res_filter.json()["total_count"], 1)

        # Update
        res_update = client.put(f"/api/expenses/{exp_id}", json={"amount": 890.00, "description": "Updated Test Dining"})
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["amount"], 890.00)

        # Delete
        res_del = client.delete(f"/api/expenses/{exp_id}")
        self.assertEqual(res_del.status_code, 200)

        # Confirm 404 after deletion
        res_after = client.get(f"/api/expenses/{exp_id}")
        self.assertEqual(res_after.status_code, 404)
        print("  [PASS] Full CRUD expense lifecycle verified.")

    def test_07_budget_tracking(self):
        """Test budget setting and progress calculation."""
        res_set = client.post("/api/budget", json={"category": "OVERALL", "monthly_limit": 40000})
        self.assertEqual(res_set.status_code, 200)

        res_get = client.get("/api/budget")
        self.assertEqual(res_get.status_code, 200)
        b_data = res_get.json()
        self.assertEqual(b_data["monthly_limit"], 40000)
        self.assertIn("percentage_used", b_data)
        print(f"  [PASS] Budget tracking verified (Limit: INR {b_data['monthly_limit']:,.0f}, Spent: INR {b_data['spent']:,.0f}, Used: {b_data['percentage_used']}%)")

    def test_08_csv_export(self):
        """Test CSV export endpoint."""
        res = client.get("/api/export/csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("content-type", ""))
        self.assertTrue(len(res.content) > 100)
        print("  [PASS] CSV export verified.")

if __name__ == "__main__":
    unittest.main()
