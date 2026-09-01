"""
ExpenseAI - Seed Data Generator
Populates realistic sample financial records with Indian Rupee (₹) transactions,
covering multiple months, varied categories, and sensible payment methods.
"""

from datetime import datetime, timedelta
import random
from backend.database import get_connection, init_db, execute_query

DEMO_EXPENSES = [
    # August 2026 (Current Month)
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-08-01", "payment_method": "Net Banking", "notes": "Monthly house rent for 2BHK"},
    {"amount": 1850.0, "category": "Bills", "description": "Electricity Bill (BESCOM)", "date": "2026-08-03", "payment_method": "UPI", "notes": "July usage bill"},
    {"amount": 1199.0, "category": "Bills", "description": "Airtel Fiber Broadband", "date": "2026-08-04", "payment_method": "Credit Card", "notes": "High-speed internet 200Mbps"},
    {"amount": 3450.0, "category": "Groceries", "description": "Nature's Basket Organic Groceries", "date": "2026-08-05", "payment_method": "UPI", "notes": "Weekly vegetables, milk, fruits"},
    {"amount": 680.0, "category": "Food", "description": "Lunch with Colleagues", "date": "2026-08-06", "payment_method": "UPI", "notes": "Biryani combo"},
    {"amount": 420.0, "category": "Transportation", "description": "Uber Ride to Office", "date": "2026-08-07", "payment_method": "UPI", "notes": "Peak hour cab"},
    {"amount": 4500.0, "category": "Shopping", "description": "Zara Casual Shirts & Jeans", "date": "2026-08-08", "payment_method": "Credit Card", "notes": "Weekend sale discount"},
    {"amount": 1250.0, "category": "Entertainment", "description": "PVR IMAX Movie Tickets & Popcorn", "date": "2026-08-09", "payment_method": "Debit Card", "notes": "Weekend movie night"},
    {"amount": 2800.0, "category": "Groceries", "description": "Blinkit Quick Delivery", "date": "2026-08-11", "payment_method": "UPI", "notes": "Household essentials & snacks"},
    {"amount": 1600.0, "category": "Healthcare", "description": "Dentist Checkup & Medication", "date": "2026-08-12", "payment_method": "UPI", "notes": "Routine dental check"},
    {"amount": 550.0, "category": "Food", "description": "Swiggy Dinner Order", "date": "2026-08-14", "payment_method": "UPI", "notes": "Healthy salad bowl"},
    {"amount": 3200.0, "category": "Travel", "description": "Weekend Road Trip Petrol / Fuel", "date": "2026-08-15", "payment_method": "Credit Card", "notes": "Full tank HP petrol"},
    {"amount": 950.0, "category": "Food", "description": "Cafe Coffee Day Meeting", "date": "2026-08-17", "payment_method": "UPI", "notes": "Coffee & dessert"},
    {"amount": 1999.0, "category": "Education", "description": "Udemy System Design Masterclass", "date": "2026-08-18", "payment_method": "Credit Card", "notes": "AI & Cloud architecture course"},
    {"amount": 750.0, "category": "Food", "description": "Family Dinner at Restaurant", "date": "2026-08-19", "payment_method": "UPI", "notes": "Evening meal"},

    # July 2026 (Previous Month)
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-07-01", "payment_method": "Net Banking", "notes": "Monthly house rent"},
    {"amount": 1720.0, "category": "Bills", "description": "Electricity Bill", "date": "2026-07-03", "payment_method": "UPI", "notes": "BESCOM power bill"},
    {"amount": 1199.0, "category": "Bills", "description": "Airtel Fiber Broadband", "date": "2026-07-04", "payment_method": "Credit Card", "notes": "Broadband renewal"},
    {"amount": 8200.0, "category": "Shopping", "description": "Myntra End of Reason Sale", "date": "2026-07-07", "payment_method": "Credit Card", "notes": "Sneakers and sports apparel"},
    {"amount": 4100.0, "category": "Groceries", "description": "BigBasket Monthly Stock", "date": "2026-07-09", "payment_method": "Debit Card", "notes": "Rice, oil, pulses, spices"},
    {"amount": 1450.0, "category": "Food", "description": "Barbeque Nation Buffet", "date": "2026-07-12", "payment_method": "Credit Card", "notes": "Team celebration dinner"},
    {"amount": 6500.0, "category": "Travel", "description": "Flight Ticket to Goa", "date": "2026-07-16", "payment_method": "Credit Card", "notes": "IndiGo return flight"},
    {"amount": 3800.0, "category": "Travel", "description": "Goa Hotel Stay", "date": "2026-07-18", "payment_method": "UPI", "notes": "2-night stay"},
    {"amount": 1200.0, "category": "Healthcare", "description": "Pharmacy Health Supplements", "date": "2026-07-22", "payment_method": "UPI", "notes": "Vitamin D & Multivitamins"},
    {"amount": 2600.0, "category": "Groceries", "description": "Supermarket Weekly Supplies", "date": "2026-07-25", "payment_method": "Cash", "notes": "Local organic market"},
    {"amount": 1800.0, "category": "Entertainment", "description": "Concert Music Pass", "date": "2026-07-28", "payment_method": "UPI", "notes": "Live indie music performance"},

    # June 2026
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-06-01", "payment_method": "Net Banking", "notes": "June rent"},
    {"amount": 2100.0, "category": "Bills", "description": "Summer AC Electricity Bill", "date": "2026-06-03", "payment_method": "UPI", "notes": "High summer AC usage"},
    {"amount": 5400.0, "category": "Groceries", "description": "Whole Foods & Provisions", "date": "2026-06-08", "payment_method": "Credit Card", "notes": "Monthly dry grocery supplies"},
    {"amount": 3200.0, "category": "Shopping", "description": "Noise Smartwatch & Earbuds", "date": "2026-06-15", "payment_method": "UPI", "notes": "Amazon lightning deal"},
    {"amount": 2400.0, "category": "Food", "description": "Weekend Fine Dining", "date": "2026-06-20", "payment_method": "Credit Card", "notes": "Italian trattoria dinner"},
    {"amount": 1800.0, "category": "Transportation", "description": "Monthly Metro Smartcard Recharge", "date": "2026-06-22", "payment_method": "UPI", "notes": "Metro commute pass"},

    # May 2026
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-05-01", "payment_method": "Net Banking", "notes": "May rent"},
    {"amount": 4900.0, "category": "Groceries", "description": "Groceries & Fresh Dairy", "date": "2026-05-06", "payment_method": "UPI", "notes": "Weekly orders"},
    {"amount": 3500.0, "category": "Education", "description": "Annual O'Reilly Tech Subscription", "date": "2026-05-14", "payment_method": "Credit Card", "notes": "Learning platform"},
    {"amount": 1800.0, "category": "Entertainment", "description": "Gaming & Steam Sale", "date": "2026-05-25", "payment_method": "Debit Card", "notes": "Games bundle"},

    # Earlier 2026 Months for rich historical trend graphs
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-04-01", "payment_method": "Net Banking", "notes": "April rent"},
    {"amount": 6200.0, "category": "Food", "description": "Dining & Food Delivery Total", "date": "2026-04-18", "payment_method": "UPI", "notes": "April culinary spending"},
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-03-01", "payment_method": "Net Banking", "notes": "March rent"},
    {"amount": 8900.0, "category": "Shopping", "description": "Spring Wardrobe & Home Decor", "date": "2026-03-15", "payment_method": "Credit Card", "notes": "IKEA and clothes"},
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-02-01", "payment_method": "Net Banking", "notes": "February rent"},
    {"amount": 4500.0, "category": "Travel", "description": "Weekend Getaway Fuel & Tolls", "date": "2026-02-14", "payment_method": "UPI", "notes": "Valentine weekend trip"},
    {"amount": 22000.0, "category": "Rent", "description": "Apartment Monthly Rent", "date": "2026-01-01", "payment_method": "Net Banking", "notes": "New year rent"},
    {"amount": 5100.0, "category": "Entertainment", "description": "New Year Party & Celebrations", "date": "2026-01-02", "payment_method": "Credit Card", "notes": "Celebration events"}
]

DEMO_BUDGETS = [
    {"year": 2026, "month": 8, "category": "ALL", "amount": 55000.0},
    {"year": 2026, "month": 8, "category": "Food", "amount": 8000.0},
    {"year": 2026, "month": 8, "category": "Shopping", "amount": 7000.0},
    {"year": 2026, "month": 8, "category": "Travel", "amount": 6000.0},
    {"year": 2026, "month": 7, "category": "ALL", "amount": 60000.0},
    {"year": 2026, "month": 6, "category": "ALL", "amount": 50000.0}
]


def seed_demo_data(clear_existing: bool = True) -> int:
    """Populates database with realistic sample transactions and budgets."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if clear_existing:
            cursor.execute("DELETE FROM expenses")
            cursor.execute("DELETE FROM budgets")
            
        count = 0
        for exp in DEMO_EXPENSES:
            cursor.execute("""
                INSERT INTO expenses (amount, category, description, date, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                exp["amount"],
                exp["category"],
                exp["description"],
                exp["date"],
                exp.get("payment_method", "UPI"),
                exp.get("notes", "")
            ))
            count += 1
            
        for b in DEMO_BUDGETS:
            cursor.execute("""
                INSERT OR REPLACE INTO budgets (year, month, category, amount)
                VALUES (?, ?, ?, ?)
            """, (b["year"], b["month"], b["category"], b["amount"]))
            
        conn.commit()
        return count


def clear_all_data() -> None:
    """Wipes all user expense and budget records."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses")
        cursor.execute("DELETE FROM budgets")
        conn.commit()


if __name__ == "__main__":
    inserted = seed_demo_data(True)
    print(f"Successfully populated {inserted} demo transactions and budgets.")
