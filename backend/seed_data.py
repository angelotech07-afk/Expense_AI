import sqlite3
from datetime import datetime, date, timedelta
from backend.database import get_db, init_db


SAMPLE_EXPENSES = [
    # August 2026 (Current Active Month)
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-08-01", "payment_method": "Net Banking", "notes": "Apartment #302"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-08-02", "payment_method": "UPI", "notes": "Monthly high-speed plan"},
    {"amount": 2850, "category": "Groceries", "description": "Supermarket Weekly Restock", "date": "2026-08-03", "payment_method": "UPI", "notes": "Fresh vegetables, dairy & staples"},
    {"amount": 650, "category": "Food", "description": "Team Lunch at Bistro", "date": "2026-08-05", "payment_method": "UPI", "notes": "Pasta & iced latte"},
    {"amount": 1200, "category": "Transportation", "description": "Metro Monthly Smart Card Recharge", "date": "2026-08-06", "payment_method": "Debit Card", "notes": "Daily office commute"},
    {"amount": 4200, "category": "Shopping", "description": "Sports Shoes & Apparel", "date": "2026-08-08", "payment_method": "Credit Card", "notes": "Nike summer collection sale"},
    {"amount": 1850, "category": "Groceries", "description": "Organic Fruits & Dry Fruits", "date": "2026-08-10", "payment_method": "UPI", "notes": "Almonds, walnuts, seasonal fruits"},
    {"amount": 550, "category": "Entertainment", "description": "Cinema IMAX Movie Tickets", "date": "2026-08-11", "payment_method": "UPI", "notes": "Weekend movie with friends"},
    {"amount": 2300, "category": "Bills", "description": "Electricity Utility Bill", "date": "2026-08-13", "payment_method": "Net Banking", "notes": "Air conditioning usage"},
    {"amount": 850, "category": "Healthcare", "description": "Pharmacy Prescription Medicines & Vitamins", "date": "2026-08-14", "payment_method": "UPI", "notes": "Multivitamins & allergy tabs"},
    {"amount": 950, "category": "Food", "description": "Weekend Family Dinner", "date": "2026-08-16", "payment_method": "Credit Card", "notes": "North Indian Cuisine"},
    {"amount": 450, "category": "Food", "description": "Specialty Coffee & Bakery", "date": "2026-08-18", "payment_method": "UPI", "notes": "Cafe working session"},
    {"amount": 1400, "category": "Education", "description": "Online Data Science Certification Book", "date": "2026-08-19", "payment_method": "Debit Card", "notes": "Reference manual"},

    # July 2026
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-07-01", "payment_method": "Net Banking", "notes": "July Rent"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-07-02", "payment_method": "UPI", "notes": "July WiFi"},
    {"amount": 3400, "category": "Groceries", "description": "Monthly Staples & Groceries", "date": "2026-07-04", "payment_method": "UPI", "notes": "Rice, oil, pulses"},
    {"amount": 1800, "category": "Food", "description": "Weekend Dining Out", "date": "2026-07-07", "payment_method": "Credit Card", "notes": "Dinner"},
    {"amount": 1500, "category": "Transportation", "description": "Fuel / Petrol refill", "date": "2026-07-10", "payment_method": "Credit Card", "notes": "Full tank"},
    {"amount": 6500, "category": "Shopping", "description": "Noise-Cancelling Headphones", "date": "2026-07-15", "payment_method": "Credit Card", "notes": "Prime Day sale gadget"},
    {"amount": 2100, "category": "Bills", "description": "Electricity Bill", "date": "2026-07-16", "payment_method": "Net Banking", "notes": "State power corp"},
    {"amount": 1200, "category": "Healthcare", "description": "Routine Dental Checkup", "date": "2026-07-20", "payment_method": "UPI", "notes": "Clinic consultation"},
    {"amount": 2900, "category": "Education", "description": "Cloud Architecture Course", "date": "2026-07-24", "payment_method": "Credit Card", "notes": "Udemy course bundle"},
    {"amount": 980, "category": "Food", "description": "Gourmet Pizza Night", "date": "2026-07-28", "payment_method": "UPI", "notes": "Food delivery app"},

    # June 2026
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-06-01", "payment_method": "Net Banking", "notes": "June Rent"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-06-02", "payment_method": "UPI", "notes": "June WiFi"},
    {"amount": 3100, "category": "Groceries", "description": "Supermarket Provisions", "date": "2026-06-05", "payment_method": "UPI", "notes": "General provisions"},
    {"amount": 1400, "category": "Transportation", "description": "Cab Rides & Fuel", "date": "2026-06-08", "payment_method": "UPI", "notes": "Rainy day commutes"},
    {"amount": 8900, "category": "Travel", "description": "Monsoon Weekend Hill Station Trip", "date": "2026-06-14", "payment_method": "Credit Card", "notes": "Resort stay & train tickets"},
    {"amount": 1900, "category": "Bills", "description": "Electricity Bill", "date": "2026-06-17", "payment_method": "Net Banking", "notes": "Power bill"},
    {"amount": 1650, "category": "Food", "description": "Barbecue Dinner with Friends", "date": "2026-06-21", "payment_method": "UPI", "notes": "Weekend celebration"},
    {"amount": 850, "category": "Entertainment", "description": "Gaming Subscription Renewal", "date": "2026-06-25", "payment_method": "Credit Card", "notes": "PlayStation Plus"},

    # May 2026
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-05-01", "payment_method": "Net Banking", "notes": "May Rent"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-05-02", "payment_method": "UPI", "notes": "May WiFi"},
    {"amount": 3200, "category": "Groceries", "description": "Groceries & Kitchen Essentials", "date": "2026-05-06", "payment_method": "UPI", "notes": "Monthly groceries"},
    {"amount": 2600, "category": "Bills", "description": "Summer Electricity Peak Bill", "date": "2026-05-15", "payment_method": "Net Banking", "notes": "Peak summer AC bill"},
    {"amount": 3200, "category": "Shopping", "description": "Summer Cotton Wardrobe", "date": "2026-05-18", "payment_method": "Credit Card", "notes": "Clothing sale"},
    {"amount": 1100, "category": "Food", "description": "Cafe & Snacks", "date": "2026-05-22", "payment_method": "UPI", "notes": "Coffee & snacks"},
    {"amount": 1300, "category": "Transportation", "description": "Metro & Fuel", "date": "2026-05-27", "payment_method": "Debit Card", "notes": "Monthly travel"},

    # April 2026
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-04-01", "payment_method": "Net Banking", "notes": "April Rent"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-04-02", "payment_method": "UPI", "notes": "April WiFi"},
    {"amount": 2900, "category": "Groceries", "description": "Groceries Restock", "date": "2026-04-05", "payment_method": "UPI", "notes": "Groceries"},
    {"amount": 1500, "category": "Healthcare", "description": "Annual Full Body Health Checkup", "date": "2026-04-12", "payment_method": "Credit Card", "notes": "Diagnostic lab test"},
    {"amount": 2100, "category": "Food", "description": "Birthday Celebration Dinner", "date": "2026-04-18", "payment_method": "UPI", "notes": "Dinner party"},
    {"amount": 1200, "category": "Transportation", "description": "Fuel & Taxi", "date": "2026-04-24", "payment_method": "UPI", "notes": "City travel"},

    # March 2026
    {"amount": 15000, "category": "Rent", "description": "Monthly House Rent", "date": "2026-03-01", "payment_method": "Net Banking", "notes": "March Rent"},
    {"amount": 999, "category": "Bills", "description": "Fiber Broadband Internet", "date": "2026-03-02", "payment_method": "UPI", "notes": "March WiFi"},
    {"amount": 3050, "category": "Groceries", "description": "Monthly Grocery Basket", "date": "2026-03-06", "payment_method": "UPI", "notes": "Supermarket essentials"},
    {"amount": 1800, "category": "Bills", "description": "Electricity & Water Bills", "date": "2026-03-14", "payment_method": "Net Banking", "notes": "Utilities"},
    {"amount": 2400, "category": "Education", "description": "Books & Tech Subscriptions", "date": "2026-03-20", "payment_method": "Credit Card", "notes": "Annual digital library"},
    {"amount": 1450, "category": "Food", "description": "Weekend Brunches", "date": "2026-03-27", "payment_method": "UPI", "notes": "Cafe dining"}
]


def seed_database(force: bool = False):
    """Seed the database with sample expense data."""
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) AS cnt FROM expenses")
        count = cursor.fetchone()["cnt"]
        
        if count > 0 and not force:
            print(f"[Seed] Database already has {count} expenses. Skipping seed.")
            return count
            
        if force:
            cursor.execute("DELETE FROM expenses")
            print("[Seed] Cleared existing expenses.")
            
        for exp in SAMPLE_EXPENSES:
            cursor.execute("""
                INSERT INTO expenses (amount, category, description, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                exp["amount"],
                exp["category"],
                exp["description"],
                exp["date"],
                exp["payment_method"],
                exp.get("notes", "")
            ))
            
        # Ensure default budget
        cursor.execute("""
            INSERT OR REPLACE INTO budgets (id, category, monthly_limit, month, year)
            VALUES (1, 'OVERALL', 35000, 8, 2026)
        """)
        
        print(f"[Seed] Successfully populated {len(SAMPLE_EXPENSES)} sample expense records.")
        return len(SAMPLE_EXPENSES)


def clear_database():
    """Clear all expense records and reset sample data."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM budgets")
        print("[Database] Cleared all expenses and budgets.")


if __name__ == "__main__":
    seed_database(force=True)
