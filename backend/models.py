from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount (must be positive)")
    category: str = Field(..., min_length=1, max_length=50, description="Expense category")
    description: str = Field(..., min_length=1, max_length=200, description="Brief description")
    date: str = Field(..., description="Date of expense in YYYY-MM-DD format")
    payment_method: Optional[str] = Field("UPI", description="Payment method: UPI, Credit Card, Cash, etc.")
    notes: Optional[str] = Field("", description="Optional notes or tags")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            # Validate format YYYY-MM-DD
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=200)
    date: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    total_amount: float


class BudgetCreate(BaseModel):
    category: str = Field("OVERALL", description="Category or OVERALL")
    monthly_limit: float = Field(..., gt=0, description="Monthly budget limit")
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)


class BudgetResponse(BaseModel):
    id: int
    category: str
    monthly_limit: float
    month: Optional[int]
    year: Optional[int]
    spent: float = 0.0
    remaining: float = 0.0
    percentage_used: float = 0.0
    status: str = "ok"  # ok, warning, exceeded
    created_at: str


class SettingsUpdate(BaseModel):
    currency_symbol: Optional[str] = None
    currency_code: Optional[str] = None
    user_name: Optional[str] = None
    monthly_budget: Optional[float] = None
    theme: Optional[str] = None


class SummaryStatsResponse(BaseModel):
    total_expenses: float
    this_month_expenses: float
    prev_month_expenses: float
    month_over_month_change_pct: float
    avg_daily_spending: float
    highest_expense: Optional[Dict[str, Any]]
    top_category: Optional[Dict[str, Any]]
    transaction_count: int
    currency_symbol: str = "₹"
    current_month_name: str
    current_year: int


class MonthlyDataPoint(BaseModel):
    month_num: int
    month_name: str
    year: int
    total: float
    transaction_count: int
    avg_per_transaction: float
    change_pct_prev_month: Optional[float] = None


class MonthlyBreakdownResponse(BaseModel):
    year: int
    months: List[MonthlyDataPoint]
    total_year_spending: float
    avg_monthly_spending: float
    highest_month: Optional[Dict[str, Any]]
    lowest_month: Optional[Dict[str, Any]]


class CategoryDataPoint(BaseModel):
    category: str
    total: float
    percentage: float
    transaction_count: int
    avg_transaction: float
    color: Optional[str] = None


class CategoryBreakdownResponse(BaseModel):
    categories: List[CategoryDataPoint]
    total_amount: float
    highest_category: Optional[Dict[str, Any]]


class DailyDataPoint(BaseModel):
    date: str
    total: float
    transaction_count: int


class WhereMoneyGoesResponse(BaseModel):
    highest_individual_expense: Optional[Dict[str, Any]]
    highest_category: Optional[Dict[str, Any]]
    highest_spending_day: Optional[Dict[str, Any]]
    highest_spending_month: Optional[Dict[str, Any]]
    top_recent_large_expenses: List[Dict[str, Any]]


class AIInsightItem(BaseModel):
    id: str
    type: str  # 'pattern', 'alert', 'positive', 'suggestion', 'anomaly', 'prediction'
    title: str
    message: str
    severity: str  # 'info', 'warning', 'success', 'critical'
    icon: str
    action_tip: Optional[str] = None


class AIInsightsResponse(BaseModel):
    insights: List[AIInsightItem]
    generated_at: str
    mode: str  # 'rule_statistical' or 'gemini_enhanced'


class HealthScoreFactor(BaseModel):
    factor_name: str
    score: int
    max_score: int
    status: str
    description: str


class HealthScoreResponse(BaseModel):
    score: int
    rating: str  # 'Excellent', 'Good', 'Fair', 'Needs Attention'
    summary: str
    factors: List[HealthScoreFactor]


class PredictionResponse(BaseModel):
    current_spent: float
    estimated_eom_total: float
    projected_additional_spend: float
    daily_burn_rate: float
    days_elapsed: int
    days_in_month: int
    budget_comparison: Optional[Dict[str, Any]]
    disclaimer: str
