/**
 * ExpenseAI — Chart.js Visual Analytics Engine
 * Manages responsive, dark-mode themed financial charts with dynamic updates.
 */

const ChartManager = {
  instances: {
    monthlyTrend: null,
    categoryBar: null,
    categoryDonut: null,
    dailyActivity: null
  },

  // Color Mapping for standard expense categories
  categoryColors: {
    "Food": "#f97316",
    "Groceries": "#10b981",
    "Shopping": "#ec4899",
    "Bills": "#eab308",
    "Rent": "#8b5cf6",
    "Travel": "#06b6d4",
    "Transportation": "#3b82f6",
    "Healthcare": "#ef4444",
    "Entertainment": "#a855f7",
    "Education": "#14b8a6",
    "Other": "#64748b"
  },

  // Global Chart.js dark theme defaults
  applyGlobalDefaults() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
    Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
  },

  /**
   * Format currency values for tooltips and axis ticks
   */
  formatCurrency(value, symbol = '₹') {
    return `${symbol}${Number(value || 0).toLocaleString('en-IN')}`;
  },

  /**
   * 1. Render / Update Monthly Spending Area Chart
   */
  renderMonthlyTrend(canvasId, monthlyData, currency = '₹') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const labels = monthlyData.map(m => m.month_name.substring(0, 3));
    const dataValues = monthlyData.map(m => m.total);

    // Gradient background fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.45)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    if (this.instances.monthlyTrend) {
      this.instances.monthlyTrend.data.labels = labels;
      this.instances.monthlyTrend.data.datasets[0].data = dataValues;
      this.instances.monthlyTrend.update('active');
      return;
    }

    this.instances.monthlyTrend = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Monthly Spend',
          data: dataValues,
          borderColor: '#6366f1',
          borderWidth: 3,
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#818cf8',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Spending: ${this.formatCurrency(ctx.parsed.y, currency)}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              callback: (val) => `${currency}${val >= 1000 ? (val/1000) + 'k' : val}`
            }
          }
        }
      }
    });
  },

  /**
   * 2. Render / Update Category Spending Bar Chart
   */
  renderCategoryBar(canvasId, categories, currency = '₹') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const labels = categories.map(c => c.category);
    const dataValues = categories.map(c => c.total);
    const colors = categories.map(c => this.categoryColors[c.category] || '#6366f1');

    if (this.instances.categoryBar) {
      this.instances.categoryBar.data.labels = labels;
      this.instances.categoryBar.data.datasets[0].data = dataValues;
      this.instances.categoryBar.data.datasets[0].backgroundColor = colors;
      this.instances.categoryBar.update('active');
      return;
    }

    this.instances.categoryBar = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Spent',
          data: dataValues,
          backgroundColor: colors,
          borderRadius: 6,
          borderSkipped: false,
          maxBarThickness: 36
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Total: ${this.formatCurrency(ctx.parsed.y, currency)}`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              callback: (val) => `${currency}${val >= 1000 ? (val/1000) + 'k' : val}`
            }
          }
        }
      }
    });
  },

  /**
   * 3. Render / Update Category Distribution Donut Chart
   */
  renderCategoryDonut(canvasId, categories, currency = '₹') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const labels = categories.map(c => c.category);
    const dataValues = categories.map(c => c.total);
    const colors = categories.map(c => this.categoryColors[c.category] || '#6366f1');

    if (this.instances.categoryDonut) {
      this.instances.categoryDonut.data.labels = labels;
      this.instances.categoryDonut.data.datasets[0].data = dataValues;
      this.instances.categoryDonut.data.datasets[0].backgroundColor = colors;
      this.instances.categoryDonut.update('active');
      return;
    }

    this.instances.categoryDonut = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: colors,
          borderColor: '#111a30',
          borderWidth: 3,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              boxWidth: 12,
              padding: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              color: '#cbd5e1'
            }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const val = ctx.parsed;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${ctx.label}: ${this.formatCurrency(val, currency)} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  },

  /**
   * 4. Render / Update Daily Spending Activity Timeline
   */
  renderDailyActivity(canvasId, dailyData, currency = '₹') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const labels = dailyData.map(d => {
      const parts = d.date.split('-');
      return `${parts[2]}/${parts[1]}`;
    });
    const dataValues = dailyData.map(d => d.total);

    if (this.instances.dailyActivity) {
      this.instances.dailyActivity.data.labels = labels;
      this.instances.dailyActivity.data.datasets[0].data = dataValues;
      this.instances.dailyActivity.update('active');
      return;
    }

    this.instances.dailyActivity = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Daily Spending',
          data: dataValues,
          backgroundColor: 'rgba(6, 182, 212, 0.75)',
          borderRadius: 4,
          hoverBackgroundColor: '#06b6d4'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) => `Date: ${dailyData[items[0].dataIndex]?.date || ''}`,
              label: (ctx) => ` Spent: ${this.formatCurrency(ctx.parsed.y, currency)} (${dailyData[ctx.dataIndex]?.transaction_count || 1} transactions)`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxRotation: 45, minRotation: 45 }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              callback: (val) => `${currency}${val >= 1000 ? (val/1000) + 'k' : val}`
            }
          }
        }
      }
    });
  },

  /**
   * Destroy all chart instances (useful during reset or full reload)
   */
  destroyAll() {
    Object.keys(this.instances).forEach(key => {
      if (this.instances[key]) {
        this.instances[key].destroy();
        this.instances[key] = null;
      }
    });
  }
};
