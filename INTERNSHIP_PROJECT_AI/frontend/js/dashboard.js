/**
 * ExpenseAI - Dashboard Module
 */

const DashboardView = {
  async render() {
    try {
      const month = AppState.selectedMonth;
      const year = AppState.selectedYear;

      // Parallel Data Fetching
      const [summary, monthly, categories, daily, highest, insights] = await Promise.all([
        API.getSummary(month, year),
        API.getMonthlyAnalytics(year),
        API.getCategoryAnalytics(month, year),
        API.getDailyAnalytics(month, year),
        API.getHighestAnalytics(),
        API.getAiInsights(month, year)
      ]);

      // Check Empty State
      const emptyContainer = document.getElementById('dashboard-empty-state');
      const dataContainer = document.getElementById('dashboard-data-view');

      if (!summary.total_transactions || summary.total_transactions === 0) {
        if (emptyContainer) emptyContainer.style.display = 'flex';
        if (dataContainer) dataContainer.style.display = 'none';
        return;
      } else {
        if (emptyContainer) emptyContainer.style.display = 'none';
        if (dataContainer) dataContainer.style.display = 'block';
      }

      // 1. Update Metric Cards
      this.updateMetrics(summary);

      // 2. Update AI Spotlight Banner
      this.updateAiSpotlight(insights);

      // 3. Update 'Where Is My Money Going' Section
      this.updateMoneyGoing(highest, summary);

      // 4. Render Interactive Charts
      ChartsEngine.renderMonthlyChart('dash-monthly-chart', monthly);
      ChartsEngine.renderCategoryBarChart('dash-category-chart', categories);
      ChartsEngine.renderCategoryDonutChart('dash-donut-chart', categories);
      ChartsEngine.renderDailyChart('dash-daily-chart', daily);

      // 5. Update Recent Expenses Preview
      await this.loadRecentExpenses();

    } catch (err) {
      console.error('[Dashboard Render Error]', err);
      AppState.showToast('Failed to load dashboard data: ' + err.message, 'error');
    }
  },

  updateMetrics(summary) {
    // Total Spending
    const elTotal = document.getElementById('kpi-total-spending');
    if (elTotal) elTotal.textContent = AppState.formatCurrency(summary.total_spending);

    // This Month
    const elThisMonth = document.getElementById('kpi-this-month');
    if (elThisMonth) elThisMonth.textContent = AppState.formatCurrency(summary.this_month_total);

    const elMomBadge = document.getElementById('kpi-mom-badge');
    if (elMomBadge) {
      const diff = summary.mom_change_pct;
      if (diff > 0) {
        elMomBadge.className = 'badge-pill badge-up';
        elMomBadge.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> +${diff}% vs last mo`;
      } else if (diff < 0) {
        elMomBadge.className = 'badge-pill badge-down';
        elMomBadge.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> ${diff}% vs last mo`;
      } else {
        elMomBadge.className = 'badge-pill badge-neutral';
        elMomBadge.innerHTML = `<i class="fa-solid fa-minus"></i> 0.0% vs last mo`;
      }
    }

    // Avg Daily
    const elAvgDaily = document.getElementById('kpi-avg-daily');
    if (elAvgDaily) elAvgDaily.textContent = AppState.formatCurrency(summary.avg_daily_spending);

    // Highest Expense
    const elHighestAmt = document.getElementById('kpi-highest-amount');
    if (elHighestAmt) elHighestAmt.textContent = AppState.formatCurrency(summary.highest_expense.amount);

    const elHighestDesc = document.getElementById('kpi-highest-desc');
    if (elHighestDesc) {
      elHighestDesc.textContent = `${summary.highest_expense.description} (${summary.highest_expense.category})`;
    }

    // Top Category
    const elTopCat = document.getElementById('kpi-top-category');
    if (elTopCat) elTopCat.textContent = summary.top_category.name || 'None';

    const elTopCatSub = document.getElementById('kpi-top-cat-sub');
    if (elTopCatSub) {
      elTopCatSub.textContent = `${AppState.formatCurrency(summary.top_category.amount)} (${summary.top_category.percentage}%)`;
    }

    // Total Transactions
    const elTxnCount = document.getElementById('kpi-total-txns');
    if (elTxnCount) elTxnCount.textContent = summary.total_transactions;
  },

  updateAiSpotlight(insightsData) {
    const banner = document.getElementById('dashboard-ai-spotlight');
    if (!banner) return;

    const list = (insightsData && insightsData.insights) || [];
    if (list.length > 0) {
      const topAlert = list[0];
      document.getElementById('ai-spotlight-title').textContent = topAlert.title;
      document.getElementById('ai-spotlight-text').textContent = topAlert.message;
      banner.style.display = 'flex';
    } else {
      banner.style.display = 'none';
    }
  },

  updateMoneyGoing(highest, summary) {
    if (!highest) return;

    const elHiExp = document.getElementById('stat-hi-expense');
    if (elHiExp && highest.highest_individual_expense) {
      elHiExp.textContent = AppState.formatCurrency(highest.highest_individual_expense.amount);
      document.getElementById('stat-hi-expense-sub').textContent = highest.highest_individual_expense.description;
    }

    const elHiCat = document.getElementById('stat-hi-cat');
    if (elHiCat && highest.highest_category) {
      elHiCat.textContent = highest.highest_category.category;
      document.getElementById('stat-hi-cat-sub').textContent = AppState.formatCurrency(highest.highest_category.total);
    }

    const elHiDay = document.getElementById('stat-hi-day');
    if (elHiDay && highest.highest_spending_day) {
      elHiDay.textContent = highest.highest_spending_day.date;
      document.getElementById('stat-hi-day-sub').textContent = AppState.formatCurrency(highest.highest_spending_day.amount);
    }

    const elHiMonth = document.getElementById('stat-hi-month');
    if (elHiMonth && highest.highest_spending_month) {
      elHiMonth.textContent = highest.highest_spending_month.label;
      document.getElementById('stat-hi-month-sub').textContent = AppState.formatCurrency(highest.highest_spending_month.amount);
    }
  },

  async loadRecentExpenses() {
    const tbody = document.getElementById('dashboard-recent-tbody');
    if (!tbody) return;

    const res = await API.getExpenses({ limit: 5, sort_by: 'date', order: 'desc' });
    const list = res.expenses || [];

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#64748b; padding:20px;">No expenses recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(exp => `
      <tr>
        <td>${exp.date}</td>
        <td style="font-weight:600;">${AppState.escapeHtml(exp.description)}</td>
        <td><span class="category-tag">${AppState.getCategoryIcon(exp.category)} ${exp.category}</span></td>
        <td class="amount-cell">${AppState.formatCurrency(exp.amount)}</td>
        <td><span class="pm-tag">${AppState.getPaymentIcon(exp.payment_method)} ${exp.payment_method}</span></td>
        <td>
          <div class="table-actions">
            <button class="action-btn" title="View Details" onclick="ExpensesView.viewDetails(${exp.id})">
              <i class="fa-regular fa-eye"></i>
            </button>
            <button class="action-btn" title="Edit" onclick="ExpensesView.openEditModal(${exp.id})">
              <i class="fa-solid fa-pen"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join('');
  }
};
