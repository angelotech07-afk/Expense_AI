/**
 * ExpenseAI — Client Application State & Controller
 * Powers reactive state, REST API integration, modals, filters, and dynamic dashboard recalculations.
 */

const AppState = {
  activeView: 'dashboard',
  currency: '₹',
  selectedYear: 2026,
  expenses: [],
  filters: {
    search: '',
    category: 'ALL',
    paymentMethod: 'ALL',
    month: null,
    startDate: '',
    endDate: '',
    minAmount: null,
    maxAmount: null,
    sortBy: 'date',
    sortOrder: 'desc',
    page: 1,
    pageSize: 20
  },
  summaryData: null,
  monthlyData: null,
  categoryData: null,
  dailyData: null,
  whereData: null,
  aiInsights: null,
  healthScore: null,
  predictionData: null,
  budgetData: null,
  editingExpenseId: null
};

// API Base URL
const API_BASE = '/api';

// Icon Map for Categories
const CategoryIcons = {
  "Food": "utensils",
  "Groceries": "shopping-basket",
  "Shopping": "shopping-bag",
  "Bills": "file-invoice-dollar",
  "Rent": "home",
  "Travel": "plane",
  "Transportation": "car",
  "Healthcare": "heartbeat",
  "Entertainment": "film",
  "Education": "graduation-cap",
  "Other": "tag"
};

// ==========================================
// Toast Notification Utility
// ==========================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let iconName = 'info-circle';
  if (type === 'success') iconName = 'check-circle';
  if (type === 'error') iconName = 'exclamation-circle';
  
  toast.innerHTML = `
    <i class="fas fa-${iconName}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// Currency & Number Formatter
// ==========================================
function formatMoney(amount, currency = AppState.currency) {
  const num = Number(amount || 0);
  return `${currency}${num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

// ==========================================
// Data Fetching & State Updates
// ==========================================

async function fetchSummary() {
  try {
    const res = await fetch(`${API_BASE}/analytics/summary`);
    if (!res.ok) throw new Error('Failed to fetch summary');
    AppState.summaryData = await res.json();
    renderSummaryKPIs();
    renderTopAiBanner();
  } catch (err) {
    console.error('fetchSummary error:', err);
  }
}

async function fetchMonthlyAnalytics(year = AppState.selectedYear) {
  try {
    const res = await fetch(`${API_BASE}/analytics/monthly?year=${year}`);
    if (!res.ok) throw new Error('Failed to fetch monthly analytics');
    AppState.monthlyData = await res.json();
    renderMonthlySection();
  } catch (err) {
    console.error('fetchMonthlyAnalytics error:', err);
  }
}

async function fetchCategoryAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/categories`);
    if (!res.ok) throw new Error('Failed to fetch category analytics');
    AppState.categoryData = await res.json();
    renderCategorySection();
  } catch (err) {
    console.error('fetchCategoryAnalytics error:', err);
  }
}

async function fetchDailyAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/daily?days=30`);
    if (!res.ok) throw new Error('Failed to fetch daily analytics');
    AppState.dailyData = await res.json();
    renderDailySection();
  } catch (err) {
    console.error('fetchDailyAnalytics error:', err);
  }
}

async function fetchWhereMoneyGoes() {
  try {
    const res = await fetch(`${API_BASE}/analytics/where-money-goes`);
    if (!res.ok) throw new Error('Failed to fetch where money goes');
    AppState.whereData = await res.json();
    renderWhereMoneyGoes();
  } catch (err) {
    console.error('fetchWhereMoneyGoes error:', err);
  }
}

async function fetchAIInsights() {
  try {
    const [resInsights, resHealth, resPred] = await Promise.all([
      fetch(`${API_BASE}/ai/insights`),
      fetch(`${API_BASE}/ai/health-score`),
      fetch(`${API_BASE}/ai/prediction`)
    ]);

    if (resInsights.ok) AppState.aiInsights = await resInsights.json();
    if (resHealth.ok) AppState.healthScore = await resHealth.json();
    if (resPred.ok) AppState.predictionData = await resPred.json();

    renderAIInsightsSection();
  } catch (err) {
    console.error('fetchAIInsights error:', err);
  }
}

async function fetchBudget() {
  try {
    const res = await fetch(`${API_BASE}/budget`);
    if (!res.ok) throw new Error('Failed to fetch budget');
    AppState.budgetData = await res.json();
    renderBudgetSection();
  } catch (err) {
    console.error('fetchBudget error:', err);
  }
}

async function fetchExpenses() {
  try {
    const params = new URLSearchParams();
    if (AppState.filters.search) params.append('search', AppState.filters.search);
    if (AppState.filters.category && AppState.filters.category !== 'ALL') params.append('category', AppState.filters.category);
    if (AppState.filters.paymentMethod && AppState.filters.paymentMethod !== 'ALL') params.append('payment_method', AppState.filters.paymentMethod);
    if (AppState.filters.startDate) params.append('start_date', AppState.filters.startDate);
    if (AppState.filters.endDate) params.append('end_date', AppState.filters.endDate);
    if (AppState.filters.month) params.append('month', AppState.filters.month);
    if (AppState.filters.minAmount) params.append('min_amount', AppState.filters.minAmount);
    if (AppState.filters.maxAmount) params.append('max_amount', AppState.filters.maxAmount);
    params.append('sort_by', AppState.filters.sortBy);
    params.append('sort_order', AppState.filters.sortOrder);
    params.append('page', AppState.filters.page);
    params.append('page_size', AppState.filters.pageSize);

    const res = await fetch(`${API_BASE}/expenses?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch expenses');
    const data = await res.json();
    AppState.expenses = data.items;
    renderExpensesTable(data);
    renderRecentDashboardExpenses();
  } catch (err) {
    console.error('fetchExpenses error:', err);
  }
}

/**
 * Trigger complete recalculation and dashboard refresh
 */
async function refreshAllData() {
  await Promise.all([
    fetchSummary(),
    fetchMonthlyAnalytics(),
    fetchCategoryAnalytics(),
    fetchDailyAnalytics(),
    fetchWhereMoneyGoes(),
    fetchAIInsights(),
    fetchBudget(),
    fetchExpenses()
  ]);
}

// ==========================================
// Rendering Views & Components
// ==========================================

function renderSummaryKPIs() {
  const d = AppState.summaryData;
  if (!d) return;

  // 1. Total Expenses
  document.getElementById('kpi-total-expenses').textContent = formatMoney(d.total_expenses);
  document.getElementById('kpi-total-count-sub').textContent = `${d.transaction_count} recorded expenses`;

  // 2. This Month
  document.getElementById('kpi-this-month').textContent = formatMoney(d.this_month_expenses);
  const momElem = document.getElementById('kpi-mom-badge');
  const momPct = d.month_over_month_change_pct;
  if (momPct >= 0) {
    momElem.className = 'trend-badge up';
    momElem.innerHTML = `<i class="fas fa-arrow-up"></i> +${momPct}% vs last mo`;
  } else {
    momElem.className = 'trend-badge down';
    momElem.innerHTML = `<i class="fas fa-arrow-down"></i> ${momPct}% vs last mo`;
  }

  // 3. Daily Average
  document.getElementById('kpi-avg-daily').textContent = formatMoney(d.avg_daily_spending);
  document.getElementById('kpi-daily-month-name').textContent = `Pace for ${d.current_month_name}`;

  // 4. Highest Expense
  if (d.highest_expense) {
    document.getElementById('kpi-highest-expense').textContent = formatMoney(d.highest_expense.amount);
    document.getElementById('kpi-highest-desc').textContent = `${d.highest_expense.description} (${d.highest_expense.category})`;
  } else {
    document.getElementById('kpi-highest-expense').textContent = formatMoney(0);
    document.getElementById('kpi-highest-desc').textContent = 'No expenses yet';
  }

  // 5. Top Category
  if (d.top_category) {
    document.getElementById('kpi-top-category').textContent = d.top_category.category;
    document.getElementById('kpi-top-cat-sub').textContent = `${formatMoney(d.top_category.total)} (${d.top_category.percentage}% of total)`;
  } else {
    document.getElementById('kpi-top-category').textContent = 'N/A';
    document.getElementById('kpi-top-cat-sub').textContent = 'No category data';
  }

  // 6. Number of Transactions
  document.getElementById('kpi-tx-count').textContent = d.transaction_count.toLocaleString();
}

function renderTopAiBanner() {
  const container = document.getElementById('ai-hero-banner');
  if (!container) return;

  if (AppState.aiInsights && AppState.aiInsights.insights && AppState.aiInsights.insights.length > 0) {
    const topInsight = AppState.aiInsights.insights[0];
    document.getElementById('ai-banner-title').textContent = topInsight.title;
    document.getElementById('ai-banner-text').textContent = topInsight.message;
    container.style.display = 'flex';
  } else {
    container.style.display = 'none';
  }
}

function renderMonthlySection() {
  const d = AppState.monthlyData;
  if (!d) return;

  // Render Charts
  ChartManager.renderMonthlyTrend('chart-monthly-trend', d.months, AppState.currency);
  ChartManager.renderMonthlyTrend('chart-monthly-analytics-page', d.months, AppState.currency);

  // High / Low Month KPIs on Analytics view
  if (d.highest_month) {
    const el = document.getElementById('analytics-highest-month');
    if (el) el.textContent = `${d.highest_month.month_name}: ${formatMoney(d.highest_month.total)}`;
  }
  if (d.lowest_month) {
    const el = document.getElementById('analytics-lowest-month');
    if (el) el.textContent = `${d.lowest_month.month_name}: ${formatMoney(d.lowest_month.total)}`;
  }
  const avgEl = document.getElementById('analytics-avg-monthly');
  if (avgEl) avgEl.textContent = formatMoney(d.avg_monthly_spending);
}

function renderCategorySection() {
  const d = AppState.categoryData;
  if (!d) return;

  // Render Charts
  ChartManager.renderCategoryDonut('chart-category-donut', d.categories, AppState.currency);
  ChartManager.renderCategoryBar('chart-category-bar', d.categories, AppState.currency);
  ChartManager.renderCategoryDonut('chart-category-donut-full', d.categories, AppState.currency);

  // Render Category Breakdown Cards List
  const listContainer = document.getElementById('category-breakdown-list');
  if (!listContainer) return;

  if (d.categories.length === 0) {
    listContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon"><i class="fas fa-tags"></i></div>
        <h4>No Category Expenses</h4>
        <p>Start adding expenses to see your category breakdown.</p>
      </div>
    `;
    return;
  }

  let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
  d.categories.forEach(cat => {
    const icon = CategoryIcons[cat.category] || 'tag';
    html += `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius-md);">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 8px; background: ${cat.color}20; color: ${cat.color}; display: flex; align-items: center; justify-content: center; font-size: 15px;">
            <i class="fas fa-${icon}"></i>
          </div>
          <div>
            <div style="font-weight: 600; font-size: 14px; color: #fff;">${cat.category}</div>
            <div style="font-size: 12px; color: var(--text-dim);">${cat.transaction_count} transactions (avg ${formatMoney(cat.avg_transaction)})</div>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-family: var(--font-heading); font-weight: 700; font-size: 15px; color: #fff;">${formatMoney(cat.total)}</div>
          <div style="font-size: 12px; color: #818cf8; font-weight: 600;">${cat.percentage}% of spend</div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  listContainer.innerHTML = html;
}

function renderDailySection() {
  const d = AppState.dailyData;
  if (!d) return;
  ChartManager.renderDailyActivity('chart-daily-activity', d, AppState.currency);
}

function renderWhereMoneyGoes() {
  const d = AppState.whereData;
  if (!d) return;

  // Highest Individual Expense
  const indEl = document.getElementById('where-highest-individual');
  const indDesc = document.getElementById('where-highest-ind-desc');
  if (d.highest_individual_expense) {
    indEl.textContent = formatMoney(d.highest_individual_expense.amount);
    indDesc.textContent = `${d.highest_individual_expense.description} (${d.highest_individual_expense.category}) on ${d.highest_individual_expense.date}`;
  } else {
    indEl.textContent = formatMoney(0);
    indDesc.textContent = 'No expense records found';
  }

  // Highest Category
  const catEl = document.getElementById('where-highest-cat');
  const catDesc = document.getElementById('where-highest-cat-desc');
  if (d.highest_category) {
    catEl.textContent = d.highest_category.category;
    catDesc.textContent = `${formatMoney(d.highest_category.total)} across ${d.highest_category.count} purchases`;
  } else {
    catEl.textContent = 'N/A';
    catDesc.textContent = 'No category data';
  }

  // Highest Day
  const dayEl = document.getElementById('where-highest-day');
  const dayDesc = document.getElementById('where-highest-day-desc');
  if (d.highest_spending_day) {
    dayEl.textContent = formatMoney(d.highest_spending_day.total);
    dayDesc.textContent = `Peak spending day: ${d.highest_spending_day.date} (${d.highest_spending_day.count} expenses)`;
  } else {
    dayEl.textContent = formatMoney(0);
    dayDesc.textContent = 'No single peak day recorded';
  }

  // Highest Month
  const moEl = document.getElementById('where-highest-month');
  const moDesc = document.getElementById('where-highest-month-desc');
  if (d.highest_spending_month) {
    moEl.textContent = formatMoney(d.highest_spending_month.total);
    moDesc.textContent = `Highest spending month: ${d.highest_spending_month.month_name}`;
  } else {
    moEl.textContent = formatMoney(0);
    moDesc.textContent = 'No monthly records';
  }

  // Top 5 Largest Purchases List
  const topListContainer = document.getElementById('where-top-purchases-list');
  if (topListContainer && d.top_recent_large_expenses) {
    if (d.top_recent_large_expenses.length === 0) {
      topListContainer.innerHTML = '<div style="color: var(--text-dim); padding: 12px;">No purchases logged yet.</div>';
    } else {
      let rows = '';
      d.top_recent_large_expenses.forEach((item, idx) => {
        const catColor = ChartManager.categoryColors[item.category] || '#6366f1';
        rows += `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.04);">
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="font-weight: 700; color: var(--text-dim); width: 18px;">#${idx+1}</span>
              <div>
                <div style="font-weight: 600; color: #fff; font-size: 13px;">${item.description}</div>
                <div style="font-size: 11px; color: var(--text-dim);">${item.date} • <span style="color:${catColor};">${item.category}</span></div>
              </div>
            </div>
            <div style="font-family: var(--font-heading); font-weight: 700; font-size: 14px; color: #fff;">
              ${formatMoney(item.amount)}
            </div>
          </div>
        `;
      });
      topListContainer.innerHTML = rows;
    }
  }
}

function renderAIInsightsSection() {
  const stream = document.getElementById('ai-insights-stream');
  if (!stream) return;

  // 1. Health Score Gauge
  if (AppState.healthScore) {
    const score = AppState.healthScore.score;
    const rating = AppState.healthScore.rating;
    
    document.getElementById('health-score-number').textContent = score;
    document.getElementById('health-score-rating').textContent = rating;
    document.getElementById('health-score-summary').textContent = AppState.healthScore.summary;

    // SVG radial progress stroke offset (440 is circumference for r=70)
    const circle = document.getElementById('health-score-circle');
    if (circle) {
      const circumference = 2 * Math.PI * 70; // ~440
      const offset = circumference - (score / 100) * circumference;
      circle.style.strokeDasharray = `${circumference}`;
      circle.style.strokeDashoffset = `${offset}`;
      
      if (score >= 80) circle.style.stroke = '#10b981';
      else if (score >= 60) circle.style.stroke = '#f59e0b';
      else circle.style.stroke = '#f43f5e';
    }

    // Health factors list
    const factorsList = document.getElementById('health-factors-list');
    if (factorsList && AppState.healthScore.factors) {
      factorsList.innerHTML = AppState.healthScore.factors.map(f => `
        <div class="factor-item">
          <div class="factor-header">
            <span>${f.factor_name}</span>
            <span style="color: ${f.status === 'success' ? '#34d399' : f.status === 'warning' ? '#fbbf24' : '#fb7185'}; font-weight: 700;">
              ${f.score}/${f.max_score}
            </span>
          </div>
          <div class="factor-desc">${f.description}</div>
        </div>
      `).join('');
    }
  }

  // 2. AI Insights List
  if (AppState.aiInsights && AppState.aiInsights.insights) {
    if (AppState.aiInsights.insights.length === 0) {
      stream.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon"><i class="fas fa-robot"></i></div>
          <h4>No Insights Yet</h4>
          <p>Add more expenses to enable deep AI pattern recognition.</p>
        </div>
      `;
    } else {
      stream.innerHTML = AppState.aiInsights.insights.map(item => `
        <div class="insight-card ${item.severity}">
          <div class="insight-icon-box">
            <i class="fas fa-${item.icon}"></i>
          </div>
          <div class="insight-body">
            <h5>${item.title}</h5>
            <p>${item.message}</p>
            ${item.action_tip ? `<div class="insight-action-tip"><i class="fas fa-lightbulb"></i> ${item.action_tip}</div>` : ''}
          </div>
        </div>
      `).join('');
    }
  }

  // 3. Prediction Forecast
  if (AppState.predictionData) {
    const p = AppState.predictionData;
    document.getElementById('pred-current-spent').textContent = formatMoney(p.current_spent);
    document.getElementById('pred-estimated-eom').textContent = formatMoney(p.estimated_eom_total);
    document.getElementById('pred-daily-rate').textContent = formatMoney(p.daily_burn_rate);
    document.getElementById('pred-disclaimer').textContent = p.disclaimer;
  }
}

function renderBudgetSection() {
  const d = AppState.budgetData;
  if (!d) return;

  const limitEl = document.getElementById('budget-total-limit');
  const spentEl = document.getElementById('budget-spent-amount');
  const remainingEl = document.getElementById('budget-remaining-amount');
  const bar = document.getElementById('budget-progress-bar');
  const pctBadge = document.getElementById('budget-pct-badge');
  const alertBox = document.getElementById('budget-status-alert');

  if (limitEl) limitEl.textContent = formatMoney(d.monthly_limit);
  if (spentEl) spentEl.textContent = formatMoney(d.spent);
  if (remainingEl) remainingEl.textContent = formatMoney(d.remaining);

  if (bar) {
    const fillPct = Math.min(100, d.percentage_used);
    bar.style.width = `${fillPct}%`;
    bar.className = 'progress-bar-fill';
    if (d.percentage_used >= 90) bar.classList.add('danger');
    else if (d.percentage_used >= 75) bar.classList.add('warning');
  }

  if (pctBadge) {
    pctBadge.textContent = `${d.percentage_used}% used`;
  }

  // Sidebar mini widget sync
  const miniBar = document.getElementById('sidebar-budget-bar');
  const miniText = document.getElementById('sidebar-budget-text');
  if (miniBar) {
    miniBar.style.width = `${Math.min(100, d.percentage_used)}%`;
    if (d.percentage_used >= 90) miniBar.className = 'progress-bar-fill danger';
    else if (d.percentage_used >= 75) miniBar.className = 'progress-bar-fill warning';
    else miniBar.className = 'progress-bar-fill';
  }
  if (miniText) {
    miniText.textContent = `${formatMoney(d.spent)} of ${formatMoney(d.monthly_limit)}`;
  }

  if (alertBox) {
    if (d.status === 'exceeded') {
      alertBox.style.display = 'block';
      alertBox.className = 'insight-card critical';
      alertBox.innerHTML = `
        <div class="insight-icon-box"><i class="fas fa-exclamation-triangle"></i></div>
        <div class="insight-body">
          <h5>Monthly Budget Exceeded</h5>
          <p>You have spent ${formatMoney(d.spent)}, which is ${formatMoney(d.spent - d.monthly_limit)} over your ₹${d.monthly_limit.toLocaleString()} budget limit.</p>
        </div>
      `;
    } else if (d.status === 'warning') {
      alertBox.style.display = 'block';
      alertBox.className = 'insight-card warning';
      alertBox.innerHTML = `
        <div class="insight-icon-box"><i class="fas fa-exclamation-circle"></i></div>
        <div class="insight-body">
          <h5>Approaching Monthly Limit</h5>
          <p>You have utilized ${d.percentage_used}% of your budget with ${formatMoney(d.remaining)} remaining for the month.</p>
        </div>
      `;
    } else {
      alertBox.style.display = 'none';
    }
  }
}

function renderExpensesTable(data) {
  const tbody = document.getElementById('expenses-table-body');
  const emptyState = document.getElementById('expenses-empty-state');
  const countBadge = document.getElementById('filter-results-count');

  if (countBadge) countBadge.textContent = `${data.total_count} expenses found (Total: ${formatMoney(data.total_amount)})`;

  if (!data.items || data.items.length === 0) {
    if (tbody) tbody.innerHTML = '';
    if (emptyState) emptyState.style.display = 'flex';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  if (!tbody) return;

  tbody.innerHTML = data.items.map(item => {
    const icon = CategoryIcons[item.category] || 'tag';
    const color = ChartManager.categoryColors[item.category] || '#6366f1';
    
    return `
      <tr>
        <td style="white-space: nowrap; color: var(--text-muted); font-size: 12px;">${item.date}</td>
        <td>
          <div style="font-weight: 600; color: #fff;">${escapeHtml(item.description)}</div>
          ${item.notes ? `<div style="font-size: 11px; color: var(--text-dim); margin-top: 2px;">${escapeHtml(item.notes)}</div>` : ''}
        </td>
        <td>
          <span class="category-badge" style="background: ${color}15; color: ${color}; border: 1px solid ${color}30;">
            <i class="fas fa-${icon}"></i>
            <span>${item.category}</span>
          </span>
        </td>
        <td class="table-amount">${formatMoney(item.amount)}</td>
        <td>
          <span class="payment-pill-sm">${item.payment_method || 'UPI'}</span>
        </td>
        <td>
          <div class="table-actions">
            <button class="btn btn-secondary btn-icon" onclick="openEditModal(${item.id})" title="Edit Expense">
              <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-danger btn-icon" onclick="confirmDeleteExpense(${item.id})" title="Delete Expense">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderRecentDashboardExpenses() {
  const container = document.getElementById('dashboard-recent-expenses');
  if (!container) return;

  const recent = AppState.expenses.slice(0, 5);
  if (recent.length === 0) {
    container.innerHTML = '<div style="color: var(--text-dim); text-align: center; padding: 24px;">No expenses recorded yet.</div>';
    return;
  }

  container.innerHTML = recent.map(item => {
    const icon = CategoryIcons[item.category] || 'tag';
    const color = ChartManager.categoryColors[item.category] || '#6366f1';
    return `
      <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); transition: var(--transition);">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="width: 36px; height: 36px; border-radius: 8px; background: ${color}20; color: ${color}; display: flex; align-items: center; justify-content: center; font-size: 15px;">
            <i class="fas fa-${icon}"></i>
          </div>
          <div>
            <div style="font-weight: 600; font-size: 13px; color: #fff;">${escapeHtml(item.description)}</div>
            <div style="font-size: 11px; color: var(--text-dim);">${item.date} • ${item.payment_method}</div>
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-family: var(--font-heading); font-weight: 700; font-size: 14px; color: #fff;">${formatMoney(item.amount)}</div>
        </div>
      </div>
    `;
  }).join('');
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/[&<>"']/g, function(m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
  });
}

// ==========================================
// Navigation & View Routing
// ==========================================

function switchView(viewName) {
  AppState.activeView = viewName;

  // Update Nav Menu UI
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update Active View Section
  document.querySelectorAll('.view-section').forEach(sec => {
    if (sec.id === `view-${viewName}`) {
      sec.classList.add('active');
    } else {
      sec.classList.remove('active');
    }
  });

  // Dynamic titles
  const titles = {
    'dashboard': { title: 'Dashboard Overview', sub: 'Understand your spending and make smarter financial decisions' },
    'add-expense': { title: 'Add New Expense', sub: 'Record transactions and update analytics immediately' },
    'expenses': { title: 'Expense History & Filter Studio', sub: 'Explore, search, filter and export your full transaction log' },
    'analytics': { title: 'Visual Analytics & Charts', sub: 'Interactive spending patterns, category shares, and trends' },
    'where-money-goes': { title: 'Where Is My Money Going?', sub: 'Automated breakdown of largest single expenses and primary cost centers' },
    'ai-insights': { title: 'AI Insights & Health Score', sub: 'Actionable financial intelligence, anomaly alerts and run-rate projections' },
    'budget': { title: 'Monthly Budget & Goals', sub: 'Track spending against monthly targets with proactive alerts' },
    'settings': { title: 'Preferences & Demo Data', sub: 'Configure currency, seed demo data, and manage your account' }
  };

  const info = titles[viewName] || { title: 'ExpenseAI', sub: '' };
  document.getElementById('header-title').textContent = info.title;
  document.getElementById('header-subtitle').textContent = info.sub;

  // Auto close mobile drawer if open
  document.getElementById('sidebar').classList.remove('mobile-open');

  // Trigger relevant view refreshes if needed
  if (viewName === 'analytics' || viewName === 'dashboard') {
    setTimeout(() => {
      if (AppState.monthlyData) ChartManager.renderMonthlyTrend('chart-monthly-trend', AppState.monthlyData.months, AppState.currency);
      if (AppState.monthlyData) ChartManager.renderMonthlyTrend('chart-monthly-analytics-page', AppState.monthlyData.months, AppState.currency);
      if (AppState.categoryData) ChartManager.renderCategoryDonut('chart-category-donut', AppState.categoryData.categories, AppState.currency);
      if (AppState.categoryData) ChartManager.renderCategoryBar('chart-category-bar', AppState.categoryData.categories, AppState.currency);
    }, 100);
  }
}

// ==========================================
// Modal Handlers & Form Actions
// ==========================================

function openAddExpenseModal() {
  AppState.editingExpenseId = null;
  document.getElementById('modal-expense-title').textContent = 'Add New Expense';
  document.getElementById('modal-expense-submit-btn').textContent = 'Add Expense';
  
  // Reset form with today's date
  document.getElementById('modal-amount').value = '';
  document.getElementById('modal-category').value = 'Food';
  document.getElementById('modal-description').value = '';
  document.getElementById('modal-date').value = new Date().toISOString().split('T')[0];
  document.getElementById('modal-notes').value = '';
  
  const defaultRadio = document.querySelector('input[name="modal_payment_method"][value="UPI"]');
  if (defaultRadio) defaultRadio.checked = true;

  document.getElementById('expense-modal').classList.add('active');
}

async function openEditModal(expenseId) {
  try {
    const res = await fetch(`${API_BASE}/expenses/${expenseId}`);
    if (!res.ok) throw new Error('Expense not found');
    const exp = await res.json();

    AppState.editingExpenseId = expenseId;
    document.getElementById('modal-expense-title').textContent = `Edit Expense #${expenseId}`;
    document.getElementById('modal-expense-submit-btn').textContent = 'Update Expense';

    document.getElementById('modal-amount').value = exp.amount;
    document.getElementById('modal-category').value = exp.category;
    document.getElementById('modal-description').value = exp.description;
    document.getElementById('modal-date').value = exp.date;
    document.getElementById('modal-notes').value = exp.notes || '';

    const pRadio = document.querySelector(`input[name="modal_payment_method"][value="${exp.payment_method}"]`);
    if (pRadio) pRadio.checked = true;

    document.getElementById('expense-modal').classList.add('active');
  } catch (err) {
    showToast('Failed to load expense for editing', 'error');
  }
}

function closeExpenseModal() {
  document.getElementById('expense-modal').classList.remove('active');
  AppState.editingExpenseId = null;
}

async function handleExpenseFormSubmit(e) {
  e.preventDefault();

  const amount = parseFloat(document.getElementById('modal-amount').value);
  const category = document.getElementById('modal-category').value;
  const description = document.getElementById('modal-description').value.trim();
  const date = document.getElementById('modal-date').value;
  const notes = document.getElementById('modal-notes').value.trim();
  
  const paymentMethodInput = document.querySelector('input[name="modal_payment_method"]:checked');
  const paymentMethod = paymentMethodInput ? paymentMethodInput.value : 'UPI';

  // Client Validation
  if (!amount || isNaN(amount) || amount <= 0) {
    showToast('Please enter a valid expense amount greater than 0', 'error');
    return;
  }
  if (!description) {
    showToast('Please provide a brief description', 'error');
    return;
  }
  if (!date) {
    showToast('Please select a valid date', 'error');
    return;
  }

  const payload = {
    amount,
    category,
    description,
    date,
    payment_method: paymentMethod,
    notes
  };

  try {
    let res;
    if (AppState.editingExpenseId) {
      res = await fetch(`${API_BASE}/expenses/${AppState.editingExpenseId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch(`${API_BASE}/expenses`, {
        method: 'PUT',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Save failed');
    }

    showToast(AppState.editingExpenseId ? 'Expense updated successfully!' : 'Expense added successfully!', 'success');
    closeExpenseModal();
    await refreshAllData();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

// Dedicated inline Add Expense form on view-add-expense
async function handleInlineExpenseSubmit(e) {
  e.preventDefault();

  const amount = parseFloat(document.getElementById('inline-amount').value);
  const category = document.getElementById('inline-category').value;
  const description = document.getElementById('inline-description').value.trim();
  const date = document.getElementById('inline-date').value;
  const notes = document.getElementById('inline-notes').value.trim();
  
  const pInput = document.querySelector('input[name="inline_payment_method"]:checked');
  const paymentMethod = pInput ? pInput.value : 'UPI';

  if (!amount || isNaN(amount) || amount <= 0) {
    showToast('Please enter a valid expense amount', 'error');
    return;
  }
  if (!description) {
    showToast('Please provide a description', 'error');
    return;
  }
  if (!date) {
    showToast('Please select a date', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, category, description, date, payment_method: paymentMethod, notes })
    });

    if (!res.ok) throw new Error('Failed to save expense');
    
    showToast('Expense recorded! Dashboard and charts updated.', 'success');
    document.getElementById('inline-expense-form').reset();
    document.getElementById('inline-date').value = new Date().toISOString().split('T')[0];
    
    await refreshAllData();
    switchView('dashboard');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

async function confirmDeleteExpense(expenseId) {
  if (!confirm(`Are you sure you want to delete expense #${expenseId}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/expenses/${expenseId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Delete failed');
    showToast(`Expense #${expenseId} deleted`, 'info');
    await refreshAllData();
  } catch (err) {
    showToast(`Failed to delete: ${err.message}`, 'error');
  }
}

async function handleBudgetUpdate(e) {
  e.preventDefault();
  const limit = parseFloat(document.getElementById('budget-input-limit').value);
  if (!limit || isNaN(limit) || limit <= 0) {
    showToast('Please enter a valid monthly budget amount', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/budget`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category: 'OVERALL', monthly_limit: limit })
    });

    if (!res.ok) throw new Error('Failed to update budget');
    showToast(`Monthly budget set to ${formatMoney(limit)}`, 'success');
    await fetchBudget();
    await fetchAIInsights();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

// Sample Data Handlers
async function seedSampleData() {
  try {
    const res = await fetch(`${API_BASE}/sample-data/seed?force=true`, { method: 'POST' });
    const d = await res.json();
    showToast(d.message || 'Sample data loaded successfully!', 'success');
    await refreshAllData();
  } catch (err) {
    showToast('Failed to seed sample data', 'error');
  }
}

async function clearAllData() {
  if (!confirm('Are you sure you want to clear ALL expense data? This action cannot be undone.')) return;
  try {
    const res = await fetch(`${API_BASE}/sample-data/clear`, { method: 'POST' });
    const d = await res.json();
    showToast(d.message || 'All expense data cleared', 'info');
    ChartManager.destroyAll();
    await refreshAllData();
  } catch (err) {
    showToast('Failed to clear data', 'error');
  }
}

// ==========================================
// Event Listeners & Initialization
// ==========================================

function setupEventListeners() {
  // Navigation Menu Clicks
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const view = item.getAttribute('data-view');
      if (view) switchView(view);
    });
  });

  // Mobile Menu Toggle
  const mobileBtn = document.getElementById('mobile-menu-btn');
  if (mobileBtn) {
    mobileBtn.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('mobile-open');
    });
  }

  // Quick "+ Add Expense" Header Button
  const btnQuickAdd = document.getElementById('btn-quick-add');
  if (btnQuickAdd) btnQuickAdd.addEventListener('click', openAddExpenseModal);

  // Modal Close Buttons
  const modalCloseBtn = document.getElementById('modal-close-btn');
  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeExpenseModal);
  const modalCancelBtn = document.getElementById('modal-cancel-btn');
  if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeExpenseModal);

  // Form Submissions
  const modalForm = document.getElementById('modal-expense-form');
  if (modalForm) modalForm.addEventListener('submit', handleExpenseFormSubmit);
  
  const inlineForm = document.getElementById('inline-expense-form');
  if (inlineForm) inlineForm.addEventListener('submit', handleInlineExpenseSubmit);

  const budgetForm = document.getElementById('budget-form');
  if (budgetForm) budgetForm.addEventListener('submit', handleBudgetUpdate);

  // Quick Preset Amount Buttons
  document.querySelectorAll('.amount-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const val = pill.getAttribute('data-val');
      const targetInput = document.getElementById('modal-amount') || document.getElementById('inline-amount');
      if (targetInput) targetInput.value = val;
    });
  });

  // Filter Toolbar Events (Instant Debounced Search & Selects)
  const searchInput = document.getElementById('filter-search');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        AppState.filters.search = e.target.value;
        AppState.filters.page = 1;
        fetchExpenses();
      }, 250);
    });
  }

  const catFilter = document.getElementById('filter-category');
  if (catFilter) {
    catFilter.addEventListener('change', (e) => {
      AppState.filters.category = e.target.value;
      AppState.filters.page = 1;
      fetchExpenses();
    });
  }

  const payFilter = document.getElementById('filter-payment');
  if (payFilter) {
    payFilter.addEventListener('change', (e) => {
      AppState.filters.paymentMethod = e.target.value;
      AppState.filters.page = 1;
      fetchExpenses();
    });
  }

  const sortSelect = document.getElementById('filter-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      const [sortBy, sortOrder] = e.target.value.split('-');
      AppState.filters.sortBy = sortBy;
      AppState.filters.sortOrder = sortOrder;
      fetchExpenses();
    });
  }

  // Clear Filter Button
  const clearFilterBtn = document.getElementById('btn-clear-filters');
  if (clearFilterBtn) {
    clearFilterBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      if (catFilter) catFilter.value = 'ALL';
      if (payFilter) payFilter.value = 'ALL';
      if (sortSelect) sortSelect.value = 'date-desc';
      AppState.filters = {
        search: '',
        category: 'ALL',
        paymentMethod: 'ALL',
        month: null,
        startDate: '',
        endDate: '',
        minAmount: null,
        maxAmount: null,
        sortBy: 'date',
        sortOrder: 'desc',
        page: 1,
        pageSize: 20
      };
      fetchExpenses();
    });
  }

  // Export CSV Button
  const btnExport = document.getElementById('btn-export-csv');
  if (btnExport) {
    btnExport.addEventListener('click', () => {
      window.location.href = `${API_BASE}/export/csv`;
      showToast('Downloading expense CSV export...', 'info');
    });
  }

  // Seed / Clear Data Buttons
  const btnSeed = document.getElementById('btn-seed-data');
  if (btnSeed) btnSeed.addEventListener('click', seedSampleData);
  const btnClear = document.getElementById('btn-clear-data');
  if (btnClear) btnClear.addEventListener('click', clearAllData);
  const btnHeaderSeed = document.getElementById('btn-header-seed');
  if (btnHeaderSeed) btnHeaderSeed.addEventListener('click', seedSampleData);

  // Currency Switcher
  const currencySelect = document.getElementById('currency-selector');
  if (currencySelect) {
    currencySelect.addEventListener('change', (e) => {
      AppState.currency = e.target.value;
      document.querySelectorAll('.currency-symbol-display').forEach(el => el.textContent = AppState.currency);
      refreshAllData();
      showToast(`Currency changed to ${AppState.currency}`, 'info');
    });
  }
}

// Initial App Startup
window.addEventListener('DOMContentLoaded', async () => {
  ChartManager.applyGlobalDefaults();
  setupEventListeners();

  // Set default dates for form inputs
  const todayStr = new Date().toISOString().split('T')[0];
  const inlineDate = document.getElementById('inline-date');
  if (inlineDate) inlineDate.value = todayStr;
  const modalDate = document.getElementById('modal-date');
  if (modalDate) modalDate.value = todayStr;

  // Load initial data
  await refreshAllData();
});
