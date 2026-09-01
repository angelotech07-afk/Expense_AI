# ExpenseAI — AI-Powered Personal Expense Analysis System

> **"Understand your spending. Make smarter decisions."**

ExpenseAI is a complete, modern, professional web application designed to help individuals understand, analyze, and manage their spending through automated calculations, interactive visual analytics, anomaly detection, financial health scoring, and personalized AI recommendations.

---

## 🌟 Key Features

1. **Intelligent Financial Dashboard**:
   - Real-time KPI summary cards: Total Spending, Current Month Spending (with MoM % delta badge), Average Daily Spending, Highest Expense, Top Category with percentage share, and Total Transaction count.
   - Interactive visual charts: Monthly spending trajectory line chart, Category volume bar chart, Category percentage distribution donut chart, and Daily spending rhythm timeline chart.
   - 1-Click **"Load Demo Data"** button to populate 30+ realistic transactions spanning multiple months.

2. **Expense Management (CRUD)**:
   - Full input validation (Amount > 0, required Category & Description, ISO Date format, Payment Method, optional Notes).
   - Instant live updates across all dashboard cards and charts upon adding, editing, or deleting expenses.

3. **Expense History & Multi-Filter Engine**:
   - Real-time search by description, notes, or category.
   - Filters by category, payment method, date range (start & end), and min/max amount.
   - Multi-column sorting (Date, Amount, Category, Description).
   - One-click CSV and JSON export.

4. **Monthly Expense Analysis (Jan – Dec)**:
   - 12-month breakdown for any selected year (January through December).
   - Calculates Total Yearly Spending, Average Monthly Spend, Highest Spending Month, Lowest Spending Month, and month-over-month deltas.

5. **Expense Categories Deep-Dive**:
   - Automatic calculation of category totals, percentage of total spending, transaction count, average ticket size, and maximum individual expense.
   - Dynamic highlight: *"Your highest spending category this month is Food, accounting for 32% of your total expenses."*

6. **"Where Is My Money Going?" (Highest Expense Analysis)**:
   - Automated identification of the highest individual transaction, highest category, peak spending day, highest spending month, and top 5 largest items.

7. **Dual-Engine AI Financial Intelligence**:
   - **Local Statistical AI Engine** (100% offline):
     - Spending velocity shifts (month-over-month increases/decreases).
     - Category surge alerts & concentration warnings.
     - Anomaly detection using statistical outlier identification (IQR / standard deviation).
     - Weekend leisure spending surge detection.
     - Positive reinforcement for disciplined budgeting.
   - **Optional Cloud Gemini AI Engine**:
     - Seamless integration with Google Gemini 1.5 Flash via `GEMINI_API_KEY` for natural language executive summaries, conversational Q&A, and customized savings strategies.

8. **Expense Health Score (0–100)**:
   - Transparent 5-factor scoring model:
     1. Budget Adherence (30 points)
     2. Category Diversification (20 points)
     3. Month-to-Month Stability (20 points)
     4. Impulse / Anomaly Control (15 points)
     5. Daily Burn Rate Consistency (15 points)
   - Dynamic circular score gauge with qualitative grade (e.g., *Excellent: 88/100*) and actionable tips to elevate the score.

9. **Month-End Burn Rate Prediction**:
   - Estimates projected month-end total spend based on current elapsed days, daily velocity, and remaining days.
   - Proactive warnings if projected spend is on track to breach the monthly budget.

10. **Budget Planner**:
    - Monthly budget target configuration with live visual progress bars (Safe <70%, Caution 70-90%, Overbudget >90%).
    - Remaining daily allowance calculation (`Remaining Budget / Days Left`).
    - Per-category budget limits.

---

## 📁 Project Structure

```text
INTERNSHIP_PROJECT_AI/
│
├── backend/
│   ├── __init__.py          # Package initialization
│   ├── app.py               # REST API Server & static file handler (Flask)
│   ├── database.py          # SQLite connection, schema & query helpers
│   ├── models.py            # Input validation routines & constants
│   ├── analytics.py         # Pure financial calculations & aggregations
│   ├── ai_analysis.py       # AI rule engine, Health Score & Gemini connector
│   ├── seed_data.py         # Realistic Indian Rupee (₹) demo dataset generator
│   └── requirements.txt     # Python dependencies
│
├── frontend/
│   ├── index.html           # Single Page Application HTML5 markup
│   ├── css/
│   │   ├── style.css        # Premium financial-tech glassmorphic styling
│   │   └── animations.css   # Keyframe transitions, pulses & glowing accents
│   └── js/
│       ├── api.js           # REST API client
│       ├── charts.js        # Chart.js visualization engine
│       ├── dashboard.js     # KPI cards & dashboard widgets
│       ├── expenses.js      # Expense table, filters, sorting & CRUD modals
│       ├── analytics_view.js# Monthly & category deep-dive analytics
│       ├── ai_insights.js   # Health score gauge, burn rate prediction & AI chat
│       ├── budget.js        # Budget progress & threshold alerting
│       └── app.js           # Main application state & tab router
│
├── database/
│   └── expenses.db          # SQLite persistent database file
│
├── tests/
│   ├── __init__.py          # Tests package init
│   └── test_api.py          # Automated backend & calculation test suite
│
├── run.py                   # One-click Python server launcher
├── start.bat                # Windows quick launcher batch script
└── README.md                # Documentation & API specifications
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+** (Tested on Python 3.11)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Installation

Open terminal in `INTERNSHIP_PROJECT_AI` directory and install dependencies:

```bash
pip install -r backend/requirements.txt
```

### 2. Running the Application

You can launch ExpenseAI using any of the following methods:

**Method A: Python Launcher (Recommended)**
```bash
python run.py
```

**Method B: Windows Batch Script**
Double-click `start.bat` or run:
```cmd
start.bat
```

The application will start on **`http://127.0.0.1:8000`** and automatically open your default browser.

---

## 🧪 Running Automated Tests

ExpenseAI includes a comprehensive test suite covering API endpoints, input validation, monthly math, category percentage math, health score formulas, and budget tracking:

```bash
python tests/test_api.py
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health check & app status |
| `GET` | `/api/metadata` | Category list, payment methods & settings |
| `GET` | `/api/expenses` | Filter, search, sort, and paginate expenses |
| `POST` | `/api/expenses` | Create a new expense record |
| `GET` | `/api/expenses/<id>` | Retrieve a single expense by ID |
| `PUT` | `/api/expenses/<id>` | Update an existing expense |
| `DELETE`| `/api/expenses/<id>` | Delete an expense by ID |
| `GET` | `/api/analytics/summary` | Dashboard KPI summary cards |
| `GET` | `/api/analytics/monthly` | 12-month yearly spending progression |
| `GET` | `/api/analytics/categories`| Category sums, percentages & averages |
| `GET` | `/api/analytics/daily` | Daily spending timeline series |
| `GET` | `/api/analytics/highest` | Peak transactions & 'Where Is My Money Going' |
| `GET` | `/api/ai/insights` | Statistical AI anomaly & pattern insights |
| `GET` | `/api/ai/health-score` | Expense Health Score (0-100) & factor points |
| `GET` | `/api/ai/predict` | Month-end burn rate prediction |
| `POST`| `/api/ai/chat` | Interactive AI financial advisor response |
| `GET` | `/api/budget` | Monthly and category budget progress |
| `POST`| `/api/budget` | Set or update monthly/category budget |
| `DELETE`| `/api/budget/<id>`| Remove category budget limit |
| `POST`| `/api/sample-data` | Populate 30+ sample demo records |
| `DELETE`| `/api/sample-data`| Reset/wipe all records |
| `GET` | `/api/export?format=csv`| Export expense records as CSV |
| `GET` | `/api/settings` | Retrieve user settings |
| `POST`| `/api/settings` | Save currency and Gemini API settings |

---

## 🧮 Mathematical & AI Calculation Logic

### 1. Financial Aggregations
- **Total Expenses**: \(\sum \text{amount}_i\)
- **Category Percentage**: \(\frac{\text{Category Total}}{\text{Total Spend}} \times 100\)
- **Average Daily Spending**: \(\frac{\text{Total Month Spend}}{\text{Active Elapsed Days}}\)
- **Month-over-Month Change (%)**: \(\frac{\text{Current Month} - \text{Previous Month}}{\text{Previous Month}} \times 100\)
- **Budget Utilization**: \(\frac{\text{Spent Amount}}{\text{Planned Budget}} \times 100\)
- **Daily Remaining Allowance**: \(\frac{\text{Remaining Budget}}{\text{Days Left in Month}}\)

### 2. AI Anomaly & Pattern Logic
- **Outlier Detection**: Identifies transactions exceeding \(\max(₹3000, 3.5 \times \mu)\) in non-fixed categories.
- **Concentration Warning**: Flags non-housing categories that consume \(>35\%\) of monthly expenditures.
- **Weekend Drift**: Calculates \(\frac{\text{Mean Weekend Spend}}{\text{Mean Weekday Spend}}\) to isolate leisure surges.
- **Health Score (0–100)**: Evaluates 5 weighted dimensions (Budget Adherence 30%, Diversification 20%, Stability 20%, Impulse Control 15%, Daily Cadence 15%).

---

## 🔒 Security & Best Practices
- SQL parameterized queries preventing SQL injection.
- Strict data sanitization and length bounds.
- Client-side XSS protection via HTML entity encoding.
- Safe API error handling without exposing stack traces.
