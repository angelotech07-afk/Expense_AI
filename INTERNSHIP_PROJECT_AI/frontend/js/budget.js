/**
 * ExpenseAI - Budget Planner & Threshold Monitoring Module
 */

const BudgetView = {
  async render() {
    try {
      const month = AppState.selectedMonth;
      const year = AppState.selectedYear;

      const data = await API.getBudgets(month, year);
      this.renderOverallBudget(data.overall_budget);
      this.renderCategoryBudgets(data.category_budgets);

    } catch (err) {
      console.error('[Budget Render Error]', err);
      AppState.showToast('Failed to load budgets: ' + err.message, 'error');
    }
  },

  renderOverallBudget(overall) {
    const elBudgetAmt = document.getElementById('budget-total-set');
    const elSpent = document.getElementById('budget-spent-amt');
    const elRemaining = document.getElementById('budget-remaining-amt');
    const elPct = document.getElementById('budget-pct-used');
    const elFill = document.getElementById('budget-hero-fill');
    const elDailyAllowance = document.getElementById('budget-daily-allowance');
    const elWarning = document.getElementById('budget-hero-warning');
    const inputAmount = document.getElementById('input-monthly-budget');

    if (overall && overall.budget_amount > 0) {
      if (elBudgetAmt) elBudgetAmt.textContent = AppState.formatCurrency(overall.budget_amount);
      if (elSpent) elSpent.textContent = AppState.formatCurrency(overall.spent_amount);
      if (elRemaining) elRemaining.textContent = AppState.formatCurrency(overall.remaining_amount);
      if (elPct) elPct.textContent = `${overall.percentage_used}%`;
      if (inputAmount) inputAmount.value = overall.budget_amount;

      if (elDailyAllowance) {
        elDailyAllowance.textContent = `${AppState.formatCurrency(overall.daily_remaining_allowance)} / day (${overall.days_left} days left)`;
      }

      // Progress bar fill
      if (elFill) {
        const cappedPct = Math.min(100, overall.percentage_used);
        elFill.style.width = `${cappedPct}%`;

        if (overall.percentage_used >= 100) {
          elFill.className = 'budget-progress-fill danger';
        } else if (overall.percentage_used >= 80) {
          elFill.className = 'budget-progress-fill warning';
        } else {
          elFill.className = 'budget-progress-fill';
        }
      }

      // Friendly threshold warning
      if (elWarning) {
        if (overall.is_exceeded) {
          elWarning.style.display = 'block';
          elWarning.className = 'ai-spotlight-banner';
          elWarning.style.borderColor = 'rgba(244,63,94,0.4)';
          elWarning.style.background = 'rgba(244,63,94,0.12)';
          elWarning.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
              <i class="fa-solid fa-triangle-exclamation" style="color:#fb7185; font-size:1.4rem;"></i>
              <div>
                <div style="font-weight:700; color:#fff;">Budget Limit Exceeded!</div>
                <div style="font-size:0.82rem; color:#fecdd3;">You have spent ${AppState.formatCurrency(overall.spent_amount)}, which is ${AppState.formatCurrency(overall.spent_amount - overall.budget_amount)} over your planned cap.</div>
              </div>
            </div>
          `;
        } else if (overall.percentage_used >= 80) {
          elWarning.style.display = 'block';
          elWarning.className = 'ai-spotlight-banner';
          elWarning.style.borderColor = 'rgba(245,158,11,0.4)';
          elWarning.style.background = 'rgba(245,158,11,0.12)';
          elWarning.innerHTML = `
            <div style="display:flex; align-items:center; gap:12px;">
              <i class="fa-solid fa-circle-exclamation" style="color:#fbbf24; font-size:1.4rem;"></i>
              <div>
                <div style="font-weight:700; color:#fff;">Budget Caution (${overall.percentage_used}% Used)</div>
                <div style="font-size:0.82rem; color:#fef08a;">You have ${AppState.formatCurrency(overall.remaining_amount)} remaining for the next ${overall.days_left} days.</div>
              </div>
            </div>
          `;
        } else {
          elWarning.style.display = 'none';
        }
      }
    } else {
      if (elBudgetAmt) elBudgetAmt.textContent = 'Not Set';
      if (elSpent) elSpent.textContent = overall ? AppState.formatCurrency(overall.spent_amount) : '₹0';
      if (elRemaining) elRemaining.textContent = '-';
      if (elPct) elPct.textContent = '0%';
      if (elFill) elFill.style.width = '0%';
      if (elDailyAllowance) elDailyAllowance.textContent = 'Set a monthly budget to calculate daily allowance';
      if (elWarning) elWarning.style.display = 'none';
    }
  },

  renderCategoryBudgets(catBudgets) {
    const tbody = document.getElementById('category-budgets-tbody');
    if (!tbody) return;

    if (!catBudgets || catBudgets.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#64748b; padding:24px;">No category budgets configured yet. Add specific category caps below.</td></tr>`;
      return;
    }

    tbody.innerHTML = catBudgets.map(b => {
      let statusBadge = `<span class="badge-pill" style="background:rgba(16,185,129,0.2); color:#34d399;">On Track</span>`;
      if (b.is_exceeded) {
        statusBadge = `<span class="badge-pill" style="background:rgba(244,63,94,0.2); color:#fb7185;">Over Limit</span>`;
      } else if (b.percentage_used >= 80) {
        statusBadge = `<span class="badge-pill" style="background:rgba(245,158,11,0.2); color:#fbbf24;">Near Limit</span>`;
      }

      return `
        <tr>
          <td><span class="category-tag">${AppState.getCategoryIcon(b.category)} ${b.category}</span></td>
          <td class="amount-cell">${AppState.formatCurrency(b.budget_amount)}</td>
          <td>${AppState.formatCurrency(b.spent_amount)}</td>
          <td style="color:${b.remaining_amount > 0 ? '#34d399' : '#fb7185'}; font-weight:600;">
            ${AppState.formatCurrency(b.remaining_amount)}
          </td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="flex:1; height:6px; background:rgba(255,255,255,0.08); border-radius:999px; overflow:hidden;">
                <div style="width:${Math.min(100, b.percentage_used)}%; height:100%; background:${b.is_exceeded ? 'var(--rose)' : (b.percentage_used >= 80 ? 'var(--amber)' : 'var(--emerald)')}; border-radius:999px;"></div>
              </div>
              <span style="font-size:0.75rem; color:#94a3b8; font-weight:600;">${b.percentage_used}%</span>
            </div>
          </td>
          <td>
            <div style="display:flex; align-items:center; gap:8px;">
              ${statusBadge}
              <button class="action-btn delete-btn" title="Delete Budget" onclick="BudgetView.deleteBudget(${b.id})">
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  async handleSaveMonthlyBudget(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('input-monthly-budget');
    const amount = parseFloat(input.value);

    if (isNaN(amount) || amount < 0) {
      AppState.showToast('Please enter a valid positive budget amount', 'error');
      return;
    }

    try {
      await API.saveBudget({
        month: AppState.selectedMonth,
        year: AppState.selectedYear,
        category: 'ALL',
        amount: amount
      });

      AppState.showToast(`Monthly budget set to ${AppState.formatCurrency(amount)}!`, 'success');
      this.render();
      AppState.refreshSidebarHealth();
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  async handleAddCategoryBudget(e) {
    if (e) e.preventDefault();
    const catSelect = document.getElementById('budget-cat-select');
    const amtInput = document.getElementById('budget-cat-amount');

    const category = catSelect.value;
    const amount = parseFloat(amtInput.value);

    if (!category) {
      AppState.showToast('Please select a category', 'error');
      return;
    }
    if (isNaN(amount) || amount <= 0) {
      AppState.showToast('Please enter a valid amount', 'error');
      return;
    }

    try {
      await API.saveBudget({
        month: AppState.selectedMonth,
        year: AppState.selectedYear,
        category: category,
        amount: amount
      });

      AppState.showToast(`Budget for ${category} saved!`, 'success');
      amtInput.value = '';
      this.render();
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  async deleteBudget(id) {
    if (!confirm('Are you sure you want to remove this budget limit?')) return;
    try {
      await API.deleteBudget(id);
      AppState.showToast('Budget limit removed.', 'info');
      this.render();
      AppState.refreshSidebarHealth();
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  }
};
