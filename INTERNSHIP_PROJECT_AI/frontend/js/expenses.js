/**
 * ExpenseAI - Expenses Management & History Module
 */

const ExpensesView = {
  currentFilters: {
    search: '',
    category: 'ALL',
    payment_method: 'ALL',
    start_date: '',
    end_date: '',
    min_amount: '',
    max_amount: '',
    sort_by: 'date',
    order: 'desc',
    limit: 15,
    offset: 0
  },

  activeEditId: null,

  async render() {
    await this.loadExpenses();
  },

  async loadExpenses() {
    try {
      const res = await API.getExpenses(this.currentFilters);
      const tbody = document.getElementById('expenses-table-tbody');
      if (!tbody) return;

      const list = res.expenses || [];
      const totalCount = res.total_count || 0;
      const totalAmount = res.total_amount || 0;

      // Update Summary footer
      const elCount = document.getElementById('filter-summary-count');
      if (elCount) elCount.textContent = `${totalCount} item${totalCount === 1 ? '' : 's'}`;

      const elSum = document.getElementById('filter-summary-amount');
      if (elSum) elSum.textContent = `Total: ${AppState.formatCurrency(totalAmount)}`;

      if (list.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:48px 20px;">
              <div style="font-size:2rem; color:#475569; margin-bottom:8px;"><i class="fa-solid fa-receipt"></i></div>
              <p style="color:#94a3b8; font-weight:600;">No matching expenses found</p>
              <p style="color:#64748b; font-size:0.8rem;">Try adjusting your filters or search keywords.</p>
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = list.map(exp => `
        <tr>
          <td><span style="color:#cbd5e1; font-weight:500;">${exp.date}</span></td>
          <td>
            <div style="font-weight:600; color:#fff;">${AppState.escapeHtml(exp.description)}</div>
            ${exp.notes ? `<div style="font-size:0.75rem; color:#64748b; margin-top:2px;">${AppState.escapeHtml(exp.notes)}</div>` : ''}
          </td>
          <td>
            <span class="category-tag">${AppState.getCategoryIcon(exp.category)} ${exp.category}</span>
          </td>
          <td class="amount-cell">${AppState.formatCurrency(exp.amount)}</td>
          <td>
            <span class="pm-tag">${AppState.getPaymentIcon(exp.payment_method)} ${exp.payment_method}</span>
          </td>
          <td>
            <div class="table-actions">
              <button class="action-btn" title="View Details" onclick="ExpensesView.viewDetails(${exp.id})">
                <i class="fa-regular fa-eye"></i>
              </button>
              <button class="action-btn" title="Edit" onclick="ExpensesView.openEditModal(${exp.id})">
                <i class="fa-solid fa-pen"></i>
              </button>
              <button class="action-btn delete-btn" title="Delete" onclick="ExpensesView.confirmDelete(${exp.id})">
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </div>
          </td>
        </tr>
      `).join('');

    } catch (err) {
      console.error('[Load Expenses Error]', err);
      AppState.showToast('Failed to load expense history: ' + err.message, 'error');
    }
  },

  applySearch(query) {
    this.currentFilters.search = query.trim();
    this.currentFilters.offset = 0;
    this.loadExpenses();
  },

  applyFilter(key, value) {
    this.currentFilters[key] = value;
    this.currentFilters.offset = 0;
    this.loadExpenses();
  },

  sortBy(field) {
    if (this.currentFilters.sort_by === field) {
      this.currentFilters.order = this.currentFilters.order === 'asc' ? 'desc' : 'asc';
    } else {
      this.currentFilters.sort_by = field;
      this.currentFilters.order = 'desc';
    }
    this.loadExpenses();
  },

  resetFilters() {
    this.currentFilters = {
      search: '',
      category: 'ALL',
      payment_method: 'ALL',
      start_date: '',
      end_date: '',
      min_amount: '',
      max_amount: '',
      sort_by: 'date',
      order: 'desc',
      limit: 15,
      offset: 0
    };

    // Reset UI Inputs
    const searchInput = document.getElementById('expense-search-input');
    if (searchInput) searchInput.value = '';
    const catSelect = document.getElementById('filter-category');
    if (catSelect) catSelect.value = 'ALL';
    const pmSelect = document.getElementById('filter-payment');
    if (pmSelect) pmSelect.value = 'ALL';
    const startDate = document.getElementById('filter-start-date');
    if (startDate) startDate.value = '';
    const endDate = document.getElementById('filter-end-date');
    if (endDate) endDate.value = '';

    this.loadExpenses();
  },

  // Save new expense from Form
  async handleAddExpenseForm(e) {
    if (e) e.preventDefault();

    const amountInput = document.getElementById('exp-amount');
    const catInput = document.getElementById('exp-category');
    const descInput = document.getElementById('exp-description');
    const dateInput = document.getElementById('exp-date');
    const pmInput = document.getElementById('exp-payment');
    const notesInput = document.getElementById('exp-notes');

    const amount = parseFloat(amountInput.value);
    const category = catInput.value;
    const description = descInput.value.trim();
    const date = dateInput.value;
    const payment_method = pmInput.value;
    const notes = notesInput.value.trim();

    if (!amount || amount <= 0) {
      AppState.showToast('Please enter a valid amount greater than 0', 'error');
      amountInput.focus();
      return;
    }
    if (!category) {
      AppState.showToast('Please select a category', 'error');
      catInput.focus();
      return;
    }
    if (!description) {
      AppState.showToast('Please enter a description', 'error');
      descInput.focus();
      return;
    }
    if (!date) {
      AppState.showToast('Please select a date', 'error');
      dateInput.focus();
      return;
    }

    try {
      await API.createExpense({
        amount,
        category,
        description,
        date,
        payment_method,
        notes
      });

      AppState.showToast(`Saved ₹${amount.toLocaleString()} on ${category}!`, 'success');

      // Clear Form fields
      amountInput.value = '';
      descInput.value = '';
      notesInput.value = '';
      dateInput.value = new Date().toISOString().split('T')[0];

      // Refresh data
      AppState.refreshActiveView();
      AppState.refreshSidebarHealth();

      // Close modal if open
      AppState.closeModal('add-expense-modal');
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  // Open Edit Modal
  async openEditModal(id) {
    try {
      const res = await API.getExpense(id);
      const exp = res.expense;
      if (!exp) return;

      this.activeEditId = id;
      document.getElementById('edit-exp-id').value = exp.id;
      document.getElementById('edit-exp-amount').value = exp.amount;
      document.getElementById('edit-exp-category').value = exp.category;
      document.getElementById('edit-exp-description').value = exp.description;
      document.getElementById('edit-exp-date').value = exp.date;
      document.getElementById('edit-exp-payment').value = exp.payment_method;
      document.getElementById('edit-exp-notes').value = exp.notes || '';

      AppState.openModal('edit-expense-modal');
    } catch (err) {
      AppState.showToast('Failed to load expense for editing: ' + err.message, 'error');
    }
  },

  // Submit Edit
  async handleEditSubmit(e) {
    if (e) e.preventDefault();
    const id = this.activeEditId;
    if (!id) return;

    const amount = parseFloat(document.getElementById('edit-exp-amount').value);
    const category = document.getElementById('edit-exp-category').value;
    const description = document.getElementById('edit-exp-description').value.trim();
    const date = document.getElementById('edit-exp-date').value;
    const payment_method = document.getElementById('edit-exp-payment').value;
    const notes = document.getElementById('edit-exp-notes').value.trim();

    if (!amount || amount <= 0) {
      AppState.showToast('Please enter a valid amount', 'error');
      return;
    }

    try {
      await API.updateExpense(id, {
        amount,
        category,
        description,
        date,
        payment_method,
        notes
      });

      AppState.showToast('Expense updated successfully!', 'success');
      AppState.closeModal('edit-expense-modal');
      AppState.refreshActiveView();
      AppState.refreshSidebarHealth();
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  // View Details Modal
  async viewDetails(id) {
    try {
      const res = await API.getExpense(id);
      const exp = res.expense;
      if (!exp) return;

      document.getElementById('detail-amount').textContent = AppState.formatCurrency(exp.amount);
      document.getElementById('detail-description').textContent = exp.description;
      document.getElementById('detail-category').innerHTML = `${AppState.getCategoryIcon(exp.category)} ${exp.category}`;
      document.getElementById('detail-date').textContent = exp.date;
      document.getElementById('detail-payment').innerHTML = `${AppState.getPaymentIcon(exp.payment_method)} ${exp.payment_method}`;
      document.getElementById('detail-notes').textContent = exp.notes ? exp.notes : 'No extra notes provided.';
      document.getElementById('detail-created').textContent = exp.created_at || '-';

      AppState.openModal('details-modal');
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  // Confirm and Delete
  async confirmDelete(id) {
    if (!confirm('Are you sure you want to delete this expense record?')) return;

    try {
      await API.deleteExpense(id);
      AppState.showToast('Expense deleted.', 'info');
      AppState.refreshActiveView();
      AppState.refreshSidebarHealth();
    } catch (err) {
      AppState.showToast(err.message, 'error');
    }
  },

  // Export CSV
  exportCSV() {
    window.location.href = '/api/export?format=csv';
  }
};
