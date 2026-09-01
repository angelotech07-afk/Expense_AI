/**
 * ExpenseAI - Analytics & Deep-Dive View Module
 */

const AnalyticsView = {
  async render() {
    try {
      const year = AppState.selectedYear;
      const month = AppState.selectedMonth;

      const [monthlyData, categoryData, highestData] = await Promise.all([
        API.getMonthlyAnalytics(year),
        API.getCategoryAnalytics(month, year),
        API.getHighestAnalytics()
      ]);

      // 1. Monthly Overview
      this.renderMonthlyOverview(monthlyData);

      // 2. Category Breakdown
      this.renderCategoryBreakdown(categoryData);

      // 3. Where Is My Money Going
      this.renderWhereIsMoneyGoing(highestData);

    } catch (err) {
      console.error('[Analytics Render Error]', err);
      AppState.showToast('Failed to load analytics: ' + err.message, 'error');
    }
  },

  renderMonthlyOverview(data) {
    // KPI Cards
    const elYearTotal = document.getElementById('analytic-year-total');
    if (elYearTotal) elYearTotal.textContent = AppState.formatCurrency(data.total_yearly_spending);

    const elYearAvg = document.getElementById('analytic-year-avg');
    if (elYearAvg) elYearAvg.textContent = AppState.formatCurrency(data.avg_monthly_spending);

    const elHiMonth = document.getElementById('analytic-hi-month');
    if (elHiMonth) {
      elHiMonth.textContent = `${data.highest_spending_month.name}`;
      document.getElementById('analytic-hi-month-sub').textContent = AppState.formatCurrency(data.highest_spending_month.amount);
    }

    const elLoMonth = document.getElementById('analytic-lo-month');
    if (elLoMonth) {
      elLoMonth.textContent = `${data.lowest_spending_month.name}`;
      document.getElementById('analytic-lo-month-sub').textContent = AppState.formatCurrency(data.lowest_spending_month.amount);
    }

    // Chart
    ChartsEngine.renderMonthlyChart('analytics-monthly-chart', data);

    // 12 Months Grid Cards
    const grid = document.getElementById('monthly-cards-grid');
    if (!grid) return;

    grid.innerHTML = (data.monthly_breakdown || []).map(m => {
      let badge = '';
      if (m.mom_change_pct > 0) {
        badge = `<span class="badge-pill badge-up"><i class="fa-solid fa-arrow-trend-up"></i> +${m.mom_change_pct}%</span>`;
      } else if (m.mom_change_pct < 0) {
        badge = `<span class="badge-pill badge-down"><i class="fa-solid fa-arrow-trend-down"></i> ${m.mom_change_pct}%</span>`;
      } else {
        badge = `<span class="badge-pill badge-neutral">-</span>`;
      }

      return `
        <div class="card" style="padding:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:700; font-size:0.95rem; color:#f8fafc;">${m.month_name}</span>
            ${badge}
          </div>
          <div style="font-size:1.3rem; font-weight:800; color:#ffffff; margin-bottom:4px;">
            ${AppState.formatCurrency(m.total)}
          </div>
          <div style="font-size:0.75rem; color:#64748b;">
            ${m.transaction_count} transaction${m.transaction_count === 1 ? '' : 's'}
          </div>
        </div>
      `;
    }).join('');
  },

  renderCategoryBreakdown(data) {
    // Dynamic Highlight Text
    const hlBox = document.getElementById('category-highlight-banner');
    if (hlBox) {
      hlBox.textContent = data.highlight_text || 'Categorize your expenses to analyze spending distribution.';
    }

    // Charts
    ChartsEngine.renderCategoryBarChart('analytics-cat-bar-chart', data);
    ChartsEngine.renderCategoryDonutChart('analytics-cat-donut-chart', data);

    // Category Breakdown Cards Grid
    const catGrid = document.getElementById('category-cards-grid');
    if (!catGrid) return;

    const cats = data.categories || [];
    if (cats.length === 0) {
      catGrid.innerHTML = `<p style="color:#64748b;">No category data recorded for this period.</p>`;
      return;
    }

    catGrid.innerHTML = cats.map(c => `
      <div class="card" style="padding:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
          <span style="font-weight:700; font-size:0.95rem; display:flex; align-items:center; gap:8px;">
            <span class="category-tag">${AppState.getCategoryIcon(c.category)} ${c.category}</span>
          </span>
          <span style="font-weight:700; font-size:0.85rem; color:#818cf8;">${c.percentage}%</span>
        </div>
        <div style="font-size:1.4rem; font-weight:800; color:#fff; margin-bottom:8px;">
          ${AppState.formatCurrency(c.total)}
        </div>
        <div style="height:6px; background:rgba(255,255,255,0.08); border-radius:999px; overflow:hidden; margin-bottom:10px;">
          <div style="width:${c.percentage}%; height:100%; background:var(--primary); border-radius:999px;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b;">
          <span>${c.count} txns (Avg: ${AppState.formatCurrency(c.avg_transaction)})</span>
          <span>Max: ${AppState.formatCurrency(c.max_expense)}</span>
        </div>
      </div>
    `).join('');
  },

  renderWhereIsMoneyGoing(highest) {
    if (!highest) return;

    // Top 5 Table
    const tbody = document.getElementById('top-5-tbody');
    if (!tbody) return;

    const list = highest.top_5_expenses || [];
    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#64748b;">No expenses to analyze yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map((exp, idx) => `
      <tr>
        <td style="font-weight:700; color:#818cf8;">#${idx + 1}</td>
        <td style="font-weight:600;">${AppState.escapeHtml(exp.description)}</td>
        <td><span class="category-tag">${AppState.getCategoryIcon(exp.category)} ${exp.category}</span></td>
        <td class="amount-cell">${AppState.formatCurrency(exp.amount)}</td>
        <td style="color:#94a3b8;">${exp.date}</td>
      </tr>
    `).join('');
  }
};
