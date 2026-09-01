"""
ExpenseAI - Automated Test Suite
Tests CRUD operations, mathematical aggregations, AI insights, health score, and budgets.
"""

import os
import sys
import unittest
import json
import tempfile

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import app
from backend.database import init_db, get_connection
from backend.seed_data import seed_demo_data


class ExpenseAITestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for isolated testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.environ["EXPENSEAI_DB_PATH"] = self.db_path
        
        # Configure app testing
        app.config["TESTING"] = True
        self.client = app.test_client()
        
        # Initialize test DB and seed data
        init_db(self.db_path)
        
        # Override database path in database module for test execution
        import backend.database as db_mod
        db_mod.DB_PATH = self.db_path
        
        seed_demo_data(clear_existing=True)

    def tearDown(self):
        try:
            os.close(self.db_fd)
        except Exception:
            pass
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception:
            pass

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["app"], "ExpenseAI")

    def test_get_metadata(self):
        response = self.client.get("/api/metadata")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("categories", data)
        self.assertIn("Food", data["categories"])
        self.assertIn("payment_methods", data)

    def test_list_expenses(self):
        response = self.client.get("/api/expenses")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("expenses", data)
        self.assertGreater(data["total_count"], 0)
        self.assertGreater(data["total_amount"], 0)

    def test_create_and_delete_expense(self):
        # Create
        new_payload = {
            "amount": 999.50,
            "category": "Food",
            "description": "Test Swiggy Order",
            "date": "2026-08-19",
            "payment_method": "UPI",
            "notes": "Automated unit test"
        }
        res = self.client.post("/api/expenses", json=new_payload)
        self.assertEqual(res.status_code, 201)
        created = res.get_json()["expense"]
        self.assertEqual(created["amount"], 999.50)
        self.assertEqual(created["description"], "Test Swiggy Order")
        exp_id = created["id"]

        # Read
        get_res = self.client.get(f"/api/expenses/{exp_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.get_json()["expense"]["amount"], 999.50)

        # Update
        update_res = self.client.put(f"/api/expenses/{exp_id}", json={"amount": 1200.0, "notes": "Updated note"})
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()["expense"]["amount"], 1200.0)

        # Delete
        del_res = self.client.delete(f"/api/expenses/{exp_id}")
        self.assertEqual(del_res.status_code, 200)

        # Verify not found
        get_after_del = self.client.get(f"/api/expenses/{exp_id}")
        self.assertEqual(get_after_del.status_code, 404)

    def test_expense_validation(self):
        # Negative amount
        res = self.client.post("/api/expenses", json={"amount": -50, "category": "Food", "description": "Fail"})
        self.assertEqual(res.status_code, 422)

        # Empty description
        res2 = self.client.post("/api/expenses", json={"amount": 100, "category": "Food", "description": ""})
        self.assertEqual(res2.status_code, 422)

        # Invalid date
        res3 = self.client.post("/api/expenses", json={"amount": 100, "category": "Food", "description": "Fail", "date": "invalid-date"})
        self.assertEqual(res3.status_code, 422)

    def test_analytics_summary(self):
        res = self.client.get("/api/analytics/summary?month=8&year=2026")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("total_spending", data)
        self.assertIn("this_month_total", data)
        self.assertIn("avg_daily_spending", data)
        self.assertIn("top_category", data)
        self.assertIn("highest_expense", data)
        self.assertGreater(data["this_month_total"], 0)

    def test_analytics_monthly(self):
        res = self.client.get("/api/analytics/monthly?year=2026")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data["monthly_breakdown"]), 12)
        self.assertGreater(data["total_yearly_spending"], 0)

    def test_analytics_categories(self):
        res = self.client.get("/api/analytics/categories?month=8&year=2026")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("categories", data)
        self.assertGreater(len(data["categories"]), 0)
        # Check percentage sum is ~100%
        pct_sum = sum(c["percentage"] for c in data["categories"])
        self.assertAlmostEqual(pct_sum, 100.0, delta=1.5)

    def test_ai_insights_and_health_score(self):
        # AI Insights
        res_ins = self.client.get("/api/ai/insights?month=8&year=2026")
        self.assertEqual(res_ins.status_code, 200)
        data_ins = res_ins.get_json()
        self.assertIn("insights", data_ins)
        self.assertIsInstance(data_ins["insights"], list)

        # Health Score
        res_hs = self.client.get("/api/ai/health-score?month=8&year=2026")
        self.assertEqual(res_hs.status_code, 200)
        data_hs = res_hs.get_json()
        self.assertIn("score", data_hs)
        self.assertTrue(0 <= data_hs["score"] <= 100)
        self.assertIn("breakdown", data_hs)

        # AI Prediction
        res_pred = self.client.get("/api/ai/predict?month=8&year=2026")
        self.assertEqual(res_pred.status_code, 200)
        data_pred = res_pred.get_json()
        self.assertIn("estimated_month_end", data_pred)

    def test_budget_flow(self):
        # Set budget
        budget_payload = {
            "month": 8,
            "year": 2026,
            "category": "Food",
            "amount": 10000.0
        }
        res_set = self.client.post("/api/budget", json=budget_payload)
        self.assertEqual(res_set.status_code, 200)

        # Get budget
        res_get = self.client.get("/api/budget?month=8&year=2026")
        self.assertEqual(res_get.status_code, 200)
        data = res_get.get_json()
        self.assertIn("overall_budget", data)
        self.assertIn("category_budgets", data)
        food_b = next((b for b in data["category_budgets"] if b["category"] == "Food"), None)
        self.assertIsNotNone(food_b)
        self.assertEqual(food_b["budget_amount"], 10000.0)

    def test_export_csv(self):
        res = self.client.get("/api/export?format=csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("Content-Type", ""))
        self.assertIn("Amount (INR)", res.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
