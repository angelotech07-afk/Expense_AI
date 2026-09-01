"""
ExpenseAI - Data Models and Validation Logic
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

VALID_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Education",
    "Healthcare",
    "Bills",
    "Entertainment",
    "Rent",
    "Groceries",
    "Transportation",
    "Other"
]

VALID_PAYMENT_METHODS = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Cash",
    "Net Banking",
    "Other"
]


def validate_expense_data(data: Dict[str, Any], is_update: bool = False) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate expense input fields.
    Returns (is_valid, error_message, sanitized_data).
    """
    if not isinstance(data, dict):
        return False, "Invalid payload format. Expected JSON object.", {}
    
    sanitized: Dict[str, Any] = {}
    
    # 1. Amount validation
    if "amount" not in data and not is_update:
        return False, "Amount is required.", {}
    if "amount" in data:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                return False, "Amount must be a positive number greater than 0.", {}
            if amount > 100_000_000:
                return False, "Amount exceeds maximum allowable limit (₹100,000,000).", {}
            sanitized["amount"] = round(amount, 2)
        except (ValueError, TypeError):
            return False, "Amount must be a valid number.", {}
            
    # 2. Category validation
    if "category" not in data and not is_update:
        return False, "Category is required.", {}
    if "category" in data:
        cat = str(data["category"]).strip()
        # Case-insensitive match against allowed categories
        matched_cat = next((c for c in VALID_CATEGORIES if c.lower() == cat.lower()), None)
        if not matched_cat:
            # Allow custom category if nonempty or fallback to Other
            sanitized["category"] = cat if cat else "Other"
        else:
            sanitized["category"] = matched_cat
            
    # 3. Description validation
    if "description" not in data and not is_update:
        return False, "Description is required.", {}
    if "description" in data:
        desc = str(data["description"]).strip()
        if not desc and not is_update:
            return False, "Description cannot be empty.", {}
        sanitized["description"] = desc[:255] # sanitize length
        
    # 4. Date validation (YYYY-MM-DD)
    if "date" not in data and not is_update:
        # Default to today's date if not provided
        sanitized["date"] = datetime.now().strftime("%Y-%m-%d")
    elif "date" in data:
        date_str = str(data["date"]).strip()
        try:
            # Validate ISO format YYYY-MM-DD
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            sanitized["date"] = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            return False, "Invalid date format. Expected YYYY-MM-DD.", {}
            
    # 5. Payment Method
    if "payment_method" in data:
        pm = str(data["payment_method"]).strip()
        matched_pm = next((p for p in VALID_PAYMENT_METHODS if p.lower() == pm.lower()), None)
        sanitized["payment_method"] = matched_pm if matched_pm else "UPI"
    elif not is_update:
        sanitized["payment_method"] = "UPI"
        
    # 6. Notes
    if "notes" in data:
        sanitized["notes"] = str(data["notes"]).strip()[:1000]
    elif not is_update:
        sanitized["notes"] = ""
        
    return True, None, sanitized


def validate_budget_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate monthly or category budget data."""
    if not isinstance(data, dict):
        return False, "Invalid budget payload format.", {}
        
    sanitized: Dict[str, Any] = {}
    
    # Month
    try:
        month = int(data.get("month", datetime.now().month))
        if not 1 <= month <= 12:
            return False, "Month must be between 1 and 12.", {}
        sanitized["month"] = month
    except (ValueError, TypeError):
        return False, "Month must be an integer.", {}
        
    # Year
    try:
        year = int(data.get("year", datetime.now().year))
        if year < 2000 or year > 2100:
            return False, "Year must be between 2000 and 2100.", {}
        sanitized["year"] = year
    except (ValueError, TypeError):
        return False, "Year must be an integer.", {}
        
    # Category ('ALL' or specific)
    cat = str(data.get("category", "ALL")).strip()
    sanitized["category"] = cat if cat else "ALL"
    
    # Amount
    try:
        amount = float(data.get("amount", 0))
        if amount < 0:
            return False, "Budget amount cannot be negative.", {}
        sanitized["amount"] = round(amount, 2)
    except (ValueError, TypeError):
        return False, "Amount must be a valid number.", {}
        
    return True, None, sanitized
