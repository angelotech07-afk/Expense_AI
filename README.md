# ExpenseAI — AI-Powered Personal Expense Analysis System

> *"Understand your spending. Make smarter decisions."*

**ExpenseAI** is a complete, modern, professional financial analysis web application designed to help individuals log, understand, visualize, and optimize their spending habits. It combines automated transaction accounting, dynamic 12-month analytics, interactive multi-chart visualizations, category allocation tracking, proactive budget management, and an intelligent dual-mode AI analysis layer with statistical anomaly detection and financial health scoring.

---

## 🌟 Key Features

### 1. Dashboard Overview & KPI Metrics
- **Total Expenses:** All-time cumulative financial expenditure.
- **This Month Spend:** Real-time spending for the active month with Month-over-Month (MoM) % trend badges.
- **Daily Average Pace:** Daily burn rate calculation based on calendar days elapsed.
- **Highest Individual Expense:** Identification of the largest single purchase.
- **Top Category Sink:** Primary expense driver with total amount and % of overall spend.
- **Transaction Counter:** Total logged transactions.
- **Dynamic AI Banner:** Prominent live insight pill highlighting immediate spending alerts.

### 2. Interactive Visual Analytics & Charts (Chart.js)
- **Monthly Spending Graph:** Smooth spline area chart tracking expenditure across all 12 months (January to December).
- **Category Spending Bar Chart:** Side-by-side comparative expenditure bars.
- **Category Distribution Donut:** Doughnut chart detailing proportional spending with custom color palettes.
- **Daily Spending Timeline:** 30-day chronological bar activity timeline with transaction density tooltips.
- **Live Recalculations:** Instant chart re-renders upon adding, editing, or deleting expenses without full page refresh.

### 3. "Where Is My Money Going?" Deep Dive
- Highlights the single highest purchase, biggest category cost center, peak expenditure day, and highest spending month.
- Ranked list of top 5 largest transactions with date and category details.

### 4. AI Expense Engine & Smart Suggestions
- **Spending Patterns:** Identifies MoM category acceleration or significant lifestyle inflation.
- **Category Concentration Alerts:** Flags non-essential categories consuming >30% of total budget.
- **Positive Feedback & Achievements:** Recognizes reductions in discretionary expenditure.
- **Smart Budget Suggestions:** Recommends optimal monthly targets based on 3-month rolling averages.
- **Statistical Anomaly Detection:** Identifies outlier purchases ($>2.5\sigma$ from mean).
- **Recurring Expense Detector:** Detects fixed repeating subscriptions and commitments.
- **End-of-Month Forecast:** Projects estimated final monthly spend based on daily run-rate velocity.

### 5. Expense Health Score (0–100)
A transparent, multi-factor scoring model:
- **Budget Adherence (30 pts):** Compliance with monthly targets and prorated daily burn rate.
- **Category Diversification (25 pts):** Balance across essential and discretionary categories.
- **Spending Trajectory (25 pts):** Month-over-month stability.
- **Impulse & Outlier Control (20 pts):** Frequency and magnitude of erratic large purchases.

### 6. Proactive Budget Tracking
- User-configurable monthly budget limit in Indian Rupees (₹).
- Visual progress bar with animated color transitions (Green $\to$ Amber $\to$ Rose).
- Live remaining safe spend and automated overage warnings.

### 7. Expense History & Filter Studio
- Real-time search by keyword (description, category, notes).
- Multi-dimensional filters: Category, Payment Method (UPI, Credit Card, Debit Card, Cash, Net Banking), and Sorting (Date, Amount, Category).
- Inline action buttons: Edit Modal, Delete with confirmation, and one-click **Export to CSV**.

---

## 🏗️ Project Architecture

```text
ExpenseAI/
├── backend/
│   ├── app.py              # FastAPI REST API, CORS, routes & static file serving
│   ├── database.py         # SQLite connection manager, schema & indices
│   ├── models.py           # Pydantic data schemas for requests and validation
│   ├── analytics.py        # Core financial mathematics, KPI aggregations & statistics
│   ├── ai_analysis.py      # Statistical AI insight generator & Health Score formula
│   ├── seed_data.py        # Realistic multi-month sample dataset generator
│   └── requirements.txt    # Python backend dependencies
│
├── frontend/
│   ├── index.html          # Semantic HTML5 dashboard layout & modals
│   ├── style.css           # Modern dark fin-tech glassmorphic CSS design system
│   ├── app.js              # State manager, API client, live filters & notifications
│   └── charts.js           # Chart.js visualization engine & theme configurations
│
├── database/
│   └── expenses.db         # SQLite persistent database file
│
├── test_backend.py         # Automated unit and integration test suite
├── run.py                  # One-click application runner
└── README.md               # Complete documentation
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10+ installed on your system.

### 1. Clone & Navigate
```bash
cd d:/INTERNSHIP_PROJECT_AI
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Application
```bash
python run.py
```

### 4. Open in Browser
- **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Schema:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/expenses` | Add a new expense record |
| `GET` | `/api/expenses` | List expenses with search, category, date, amount filters & pagination |
| `GET` | `/api/expenses/{id}` | Retrieve single expense by ID |
| `PUT` | `/api/expenses/{id}` | Update existing expense details |
| `DELETE` | `/api/expenses/{id}` | Delete expense record |
| `GET` | `/api/analytics/summary` | Get high-level KPI cards and month-over-month comparisons |
| `GET` | `/api/analytics/monthly` | Get 12-month spending breakdown for specified year |
| `GET` | `/api/analytics/categories` | Get category spending distribution, counts, and percentages |
| `GET` | `/api/analytics/daily` | Get daily spending time series for charts |
| `GET` | `/api/analytics/where-money-goes` | Get "Where Is My Money Going?" breakdown and largest expenses |
| `GET` | `/api/ai/insights` | Get dynamic AI insights (patterns, alerts, positive feedback, anomalies) |
| `GET` | `/api/ai/health-score` | Get 0-100 Expense Health Score and factor ratings |
| `GET` | `/api/ai/prediction` | Get End-of-Month projected spending forecast |
| `GET` | `/api/budget` | Get current monthly budget status and progress |
| `POST` | `/api/budget` | Update monthly budget target |
| `POST` | `/api/sample-data/seed` | Populate realistic sample expenses |
| `POST` | `/api/sample-data/clear` | Reset database and clear all records |
| `GET` | `/api/export/csv` | Download complete expenses dataset as CSV |

---

## 🧮 Financial Calculation Formulas

### 1. Average Daily Spending
$$\text{Daily Avg} = \frac{\sum \text{Expenses in Current Month}}{\max(1, \text{Days Elapsed in Month})}$$

### 2. Category Share Percentage
$$\text{Category Share} = \left( \frac{\sum \text{Category Amount}}{\sum \text{Total Expenses}} \right) \times 100$$

### 3. Month-over-Month (MoM) Growth
$$\text{MoM Change } (\%) = \left( \frac{\text{Spend}_{\text{curr}} - \text{Spend}_{\text{prev}}}{\text{Spend}_{\text{prev}}} \right) \times 100$$

### 4. End-of-Month Projection
$$\text{Projected Spend} = \text{Spend to Date} + \left( \frac{\text{Spend to Date}}{\text{Days Elapsed}} \times \text{Days Remaining} \right)$$

### 5. Anomaly Detection Threshold
$$\text{Outlier Cutoff} = \mu + 2.5 \times \sigma$$
Where $\mu$ is the average transaction amount and $\sigma$ is the standard deviation.

---

## 🧪 Running Automated Tests

To execute the backend test suite:
```bash
python test_backend.py
```
Output verifies:
- Database schema and connection persistence
- High-level KPI aggregations
- 12-month time-series integrity
- Category distribution math
- AI insights and 0-100 Health Score factors
- Full CRUD expense lifecycle
- Budget progress and overage alerts
- CSV file export format

---

## 🎨 Design & Aesthetic System
- **Theme:** Dark Indigo/Navy Financial-Tech (`#070b14`, `#0b1120`, `#10182c`)
- **Effects:** Glassmorphic backdrops (`backdrop-filter: blur(16px)`), subtle glowing borders, interactive card elevation.
- **Typography:** `Outfit` (Headings & Financial Numbers) and `Inter` (UI & Body Text).
- **Responsiveness:** Fluid grid layout supporting Mobile, Tablet, Laptop, and Ultrawide displays with collapsible navigation.
