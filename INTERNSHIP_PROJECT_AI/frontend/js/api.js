/**
 * ExpenseAI - REST API Client Module
 */

const API = {
  baseUrl: '/api',

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}`;
        try {
          const errData = await response.json();
          errorMsg = errData.error || errData.message || errorMsg;
        } catch (_) {}
        throw new Error(errorMsg);
      }

      // Check if response is JSON
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      return await response.text();
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  // Health & Metadata
  getMetadata() {
    return this.request('/metadata');
  },

  // Expenses CRUD
  getExpenses(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/expenses?${query}`);
  },

  getExpense(id) {
    return this.request(`/expenses/${id}`);
  },

  createExpense(data) {
    return this.request('/expenses', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  updateExpense(id, data) {
    return this.request(`/expenses/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  deleteExpense(id) {
    return this.request(`/expenses/${id}`, {
      method: 'DELETE'
    });
  },

  // Analytics
  getSummary(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/analytics/summary?${q}`);
  },

  getMonthlyAnalytics(year) {
    const q = new URLSearchParams({ ...(year ? { year } : {}) }).toString();
    return this.request(`/analytics/monthly?${q}`);
  },

  getCategoryAnalytics(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/analytics/categories?${q}`);
  },

  getDailyAnalytics(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/analytics/daily?${q}`);
  },

  getHighestAnalytics() {
    return this.request('/analytics/highest');
  },

  // AI & Health Score
  getAiInsights(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/ai/insights?${q}`);
  },

  getHealthScore(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/ai/health-score?${q}`);
  },

  getPrediction(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/ai/predict?${q}`);
  },

  sendAiChat(query) {
    return this.request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
  },

  // Budgets
  getBudgets(month, year) {
    const q = new URLSearchParams({ ...(month ? { month } : {}), ...(year ? { year } : {}) }).toString();
    return this.request(`/budget?${q}`);
  },

  saveBudget(data) {
    return this.request('/budget', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  deleteBudget(id) {
    return this.request(`/budget/${id}`, {
      method: 'DELETE'
    });
  },

  // Sample Data & Settings
  loadSampleData() {
    return this.request('/sample-data', { method: 'POST' });
  },

  clearAllData() {
    return this.request('/sample-data', { method: 'DELETE' });
  },

  getSettings() {
    return this.request('/settings');
  },

  saveSettings(data) {
    return this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};
