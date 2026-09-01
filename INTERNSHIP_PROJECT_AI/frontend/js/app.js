/**
 * ExpenseAI - Core Application Controller & Router
 */

const AppState = {
  selectedMonth: new Date().getMonth() + 1,
  selectedYear: new Date().getFullYear(),
  currencySymbol: '₹',
  currencyCode: 'INR',
  activeTab: 'dashboard',
  metadata: null,

  // Initialize App
  async init() {
    try {
      // 1. Populate Month & Year Dropdowns
      this.initPeriodSelectors();

      // 2. Fetch App Metadata & Settings
      this.metadata = await API.getMetadata();
      if (this.metadata && this.metadata.settings) {
        if (this.metadata.settings.currency_symbol) {
          this.currencySymbol = this.metadata.settings.currency_symbol;
        }
        if (this.metadata.settings.currency_code) {
          this.currencyCode = this.metadata.settings.currency_code;
        }
      }

      // Populate Category and Payment Method Dropdowns
      this.populateSelects();

      // 3. Setup Navigation & Global Event Handlers
      this.setupNavigation();
      this.setupGlobalHandlers();

      // Set default date picker to today
      const todayStr = new Date().toISOString().split('T')[0];
      const addExpDate = document.getElementById('exp-date');
      if (addExpDate) addExpDate.value = todayStr;

      // 4. Initial Render
      await this.refreshActiveView();
      await this.refreshSidebarHealth();

    } catch (err) {
      console.error('[App Init Error]', err);
      this.showToast('Initialization error: ' + err.message, 'error');
    }
  },

  initPeriodSelectors() {
    const monthSelect = document.getElementById('global-month-select');
    const yearSelect = document.getElementById('global-year-select');

    if (monthSelect) {
      monthSelect.value = this.selectedMonth;
      monthSelect.addEventListener('change', (e) => {
        this.selectedMonth = parseInt(e.target.value, 10);
        this.refreshActiveView();
        this.refreshSidebarHealth();
      });
    }

    if (yearSelect) {
      yearSelect.value = this.selectedYear;
      yearSelect.addEventListener('change', (e) => {
        this.selectedYear = parseInt(e.target.value, 10);
        this.refreshActiveView();
        this.refreshSidebarHealth();
      });
    }
  },

  populateSelects() {
    const categories = (this.metadata && this.metadata.categories) || [
      'Food', 'Travel', 'Shopping', 'Education', 'Healthcare', 'Bills',
      'Entertainment', 'Rent', 'Groceries', 'Transportation', 'Other'
    ];

    const paymentMethods = (this.metadata && this.metadata.payment_methods) || [
      'UPI', 'Credit Card', 'Debit Card', 'Cash', 'Net Banking', 'Other'
    ];

    // Populate Add Expense Category Select
    const expCat = document.getElementById('exp-category');
    if (expCat) {
      expCat.innerHTML = '<option value="" disabled selected>Select Category</option>' +
        categories.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Populate Edit Expense Category Select
    const editExpCat = document.getElementById('edit-exp-category');
    if (editExpCat) {
      editExpCat.innerHTML = categories.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Populate Filter Category Select
    const filterCat = document.getElementById('filter-category');
    if (filterCat) {
      filterCat.innerHTML = '<option value="ALL">All Categories</option>' +
        categories.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Populate Budget Category Select
    const budgetCat = document.getElementById('budget-cat-select');
    if (budgetCat) {
      budgetCat.innerHTML = '<option value="" disabled selected>Select Category</option>' +
        categories.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    // Populate Payment Methods
    const expPm = document.getElementById('exp-payment');
    if (expPm) {
      expPm.innerHTML = paymentMethods.map(p => `<option value="${p}">${p}</option>`).join('');
    }

    const editExpPm = document.getElementById('edit-exp-payment');
    if (editExpPm) {
      editExpPm.innerHTML = paymentMethods.map(p => `<option value="${p}">${p}</option>`).join('');
    }

    const filterPm = document.getElementById('filter-payment');
    if (filterPm) {
      filterPm.innerHTML = '<option value="ALL">All Payment Methods</option>' +
        paymentMethods.map(p => `<option value="${p}">${p}</option>`).join('');
    }
  },

  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = item.getAttribute('data-tab');
        if (tab) this.switchTab(tab);
      });
    });

    // Mobile Sidebar toggle
    const toggleBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('app-sidebar');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  },

  switchTab(tabName) {
    this.activeTab = tabName;

    // Update Nav Link Active States
    document.querySelectorAll('.nav-item').forEach(el => {
      if (el.getAttribute('data-tab') === tabName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Update Views
    document.querySelectorAll('.view-section').forEach(view => {
      view.classList.remove('active');
    });

    const targetView = document.getElementById(`view-${tabName}`);
    if (targetView) targetView.classList.add('active');

    // Update Page Header Titles
    const titleEl = document.getElementById('header-view-title');
    const descEl = document.getElementById('header-view-desc');

    const viewTitles = {
      dashboard: { title: 'Financial Dashboard', desc: 'Real-time overview of your personal cash flow & analytics' },
      'add-expense': { title: 'Add New Expense', desc: 'Record and categorize daily payments with instant analytics update' },
      expenses: { title: 'Expense History', desc: 'Search, filter, edit, and export your recorded transactions' },
      analytics: { title: 'Monthly & Category Analytics', desc: 'Interactive visual progression, yearly totals, and spending patterns' },
      'where-is-money': { title: 'Where Is My Money Going?', desc: 'Deep-dive analysis of your highest expenses, categories, and peak days' },
      ai: { title: 'AI Insights & Health Score', desc: 'Predictive intelligence, financial health scoring, and smart recommendations' },
      budget: { title: 'Budget Planner', desc: 'Set monthly and category-specific budget caps with threshold alerts' },
      settings: { title: 'App Settings', desc: 'Configure currency, AI API integrations, and database records' }
    };

    if (viewTitles[tabName]) {
      if (titleEl) titleEl.textContent = viewTitles[tabName].title;
      if (descEl) descEl.textContent = viewTitles[tabName].desc;
    }

    // Close mobile sidebar if open
    const sidebar = document.getElementById('app-sidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Render active view data
    this.refreshActiveView();
  },

  async refreshActiveView() {
    switch (this.activeTab) {
      case 'dashboard':
        await DashboardView.render();
        break;
      case 'expenses':
        await ExpensesView.render();
        break;
      case 'analytics':
      case 'where-is-money':
        await AnalyticsView.render();
        break;
      case 'ai':
        await AiInsightsView.render();
        break;
      case 'budget':
        await BudgetView.render();
        break;
      case 'settings':
        this.loadSettings();
        break;
      default:
        break;
    }
  },

  async refreshSidebarHealth() {
    try {
      const data = await API.getHealthScore(this.selectedMonth, this.selectedYear);
      const score = data.score || 0;

      const elScore = document.getElementById('sb-health-score');
      if (elScore) elScore.innerHTML = `${score}<span>/100</span>`;

      const elFill = document.getElementById('sb-health-fill');
      if (elFill) elFill.style.width = `${score}%`;

      const elGrade = document.getElementById('sb-health-grade');
      if (elGrade) elGrade.textContent = data.grade;

    } catch (_) {}
  },

  setupGlobalHandlers() {
    // Top Quick Add Button
    const topAddBtn = document.getElementById('btn-top-add-expense');
    if (topAddBtn) {
      topAddBtn.addEventListener('click', () => {
        this.openModal('add-expense-modal');
      });
    }

    // Top Demo Data Button
    const topDemoBtn = document.getElementById('btn-top-demo-data');
    if (topDemoBtn) {
      topDemoBtn.addEventListener('click', () => this.handleLoadDemoData());
    }

    // Top Reset Data Button
    const topResetBtn = document.getElementById('btn-top-reset-data');
    if (topResetBtn) {
      topResetBtn.addEventListener('click', () => this.handleResetData());
    }
  },

  async handleLoadDemoData() {
    try {
      const res = await API.loadSampleData();
      this.showToast(res.message || 'Demo data loaded successfully!', 'success');
      this.refreshActiveView();
      this.refreshSidebarHealth();
    } catch (err) {
      this.showToast('Failed to load sample data: ' + err.message, 'error');
    }
  },

  async handleResetData() {
    if (!confirm('Are you sure you want to clear all expense records and reset?')) return;
    try {
      await API.clearAllData();
      this.showToast('All expense records wiped.', 'info');
      this.refreshActiveView();
      this.refreshSidebarHealth();
    } catch (err) {
      this.showToast('Failed to reset data: ' + err.message, 'error');
    }
  },

  // Settings
  async loadSettings() {
    try {
      const settings = await API.getSettings();
      const currSelect = document.getElementById('settings-currency');
      if (currSelect && settings.currency_symbol) {
        currSelect.value = settings.currency_symbol;
      }
      const geminiInput = document.getElementById('settings-gemini-key');
      if (geminiInput && settings.gemini_api_key) {
        geminiInput.value = settings.gemini_api_key;
      }
    } catch (_) {}
  },

  async handleSaveSettings(e) {
    if (e) e.preventDefault();
    const currSelect = document.getElementById('settings-currency');
    const geminiInput = document.getElementById('settings-gemini-key');

    const symbol = currSelect ? currSelect.value : '₹';
    const key = geminiInput ? geminiInput.value.trim() : '';

    let code = 'INR';
    let name = 'Indian Rupee';
    if (symbol === '$') { code = 'USD'; name = 'US Dollar'; }
    else if (symbol === '€') { code = 'EUR'; name = 'Euro'; }
    else if (symbol === '£') { code = 'GBP'; name = 'British Pound'; }
    else if (symbol === '¥') { code = 'JPY'; name = 'Japanese Yen'; }

    try {
      await API.saveSettings({
        currency_symbol: symbol,
        currency_code: code,
        currency_name: name,
        gemini_api_key: key
      });

      this.currencySymbol = symbol;
      this.currencyCode = code;

      this.showToast('Settings saved successfully!', 'success');
      this.refreshActiveView();
    } catch (err) {
      this.showToast(err.message, 'error');
    }
  },

  // Modals
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  },

  // Toasts
  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
      <i class="fa-solid ${icon}" style="font-size:1.1rem;"></i>
      <span style="flex:1;">${this.escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // Formatting Helpers
  formatCurrency(amount) {
    if (amount === undefined || amount === null || isNaN(amount)) return `${this.currencySymbol}0.00`;
    return `${this.currencySymbol}${Number(amount).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  },

  formatCompact(amount) {
    if (amount >= 10000000) return `${this.currencySymbol}${(amount / 10000000).toFixed(1)}Cr`;
    if (amount >= 100000) return `${this.currencySymbol}${(amount / 100000).toFixed(1)}L`;
    if (amount >= 1000) return `${this.currencySymbol}${(amount / 1000).toFixed(1)}k`;
    return `${this.currencySymbol}${amount}`;
  },

  getCategoryIcon(cat) {
    const map = {
      'Food': '<i class="fa-solid fa-utensils" style="color:#fbbf24;"></i>',
      'Travel': '<i class="fa-solid fa-plane-departure" style="color:#38bdf8;"></i>',
      'Shopping': '<i class="fa-solid fa-bag-shopping" style="color:#f472b6;"></i>',
      'Education': '<i class="fa-solid fa-graduation-cap" style="color:#a78bfa;"></i>',
      'Healthcare': '<i class="fa-solid fa-heart-pulse" style="color:#fb7185;"></i>',
      'Bills': '<i class="fa-solid fa-file-invoice-dollar" style="color:#fb923c;"></i>',
      'Entertainment': '<i class="fa-solid fa-film" style="color:#c084fc;"></i>',
      'Rent': '<i class="fa-solid fa-house" style="color:#60a5fa;"></i>',
      'Groceries': '<i class="fa-solid fa-cart-shopping" style="color:#34d399;"></i>',
      'Transportation': '<i class="fa-solid fa-car" style="color:#2dd4bf;"></i>',
      'Other': '<i class="fa-solid fa-tags" style="color:#94a3b8;"></i>'
    };
    return map[cat] || '<i class="fa-solid fa-tag"></i>';
  },

  getPaymentIcon(pm) {
    const map = {
      'UPI': '<i class="fa-solid fa-mobile-screen-button"></i>',
      'Credit Card': '<i class="fa-regular fa-credit-card"></i>',
      'Debit Card': '<i class="fa-solid fa-credit-card"></i>',
      'Cash': '<i class="fa-solid fa-money-bill-wave"></i>',
      'Net Banking': '<i class="fa-solid fa-building-columns"></i>',
      'Other': '<i class="fa-solid fa-wallet"></i>'
    };
    return map[pm] || '<i class="fa-solid fa-credit-card"></i>';
  },

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  formatMarkdown(text) {
    if (!text) return '';
    let parsed = this.escapeHtml(text);
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\*(.*?)\*/g, '<em>$1</em>');
    parsed = parsed.replace(/\n/g, '<br/>');
    return parsed;
  }
};

// Bootstrap application on window load
document.addEventListener('DOMContentLoaded', () => {
  AppState.init();
});
