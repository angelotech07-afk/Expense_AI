/**
 * ExpenseAI - Visual Charts Engine (Chart.js Integration)
 */

const ChartsEngine = {
  instances: {},

  // Vibrant Financial Tech Color Palette
  colors: [
    '#6366f1', // Indigo
    '#06b6d4', // Cyan
    '#10b981', // Emerald
    '#f59e0b', // Amber
    '#f43f5e', // Rose
    '#a855f7', // Purple
    '#3b82f6', // Blue
    '#14b8a6', // Teal
    '#ec4899', // Pink
    '#eab308', // Yellow
    '#8b5cf6'  // Violet
  ],

  // Destroy existing chart instance
  destroy(chartId) {
    if (this.instances[chartId]) {
      this.instances[chartId].destroy();
      delete this.instances[chartId];
    }
  },

  // Base options for dark aesthetic
  getBaseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 12 }
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleColor: '#ffffff',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          usePointStyle: true,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || context.label || '';
              if (label) label += ': ';
              const val = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
              return label + AppState.formatCurrency(val);
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: {
            color: '#64748b',
            font: { family: 'Inter', size: 11 },
            callback: function(value) {
              return AppState.formatCompact(value);
            }
          }
        }
      }
    };
  },

  // 1. Monthly Spending Line / Area Chart
  renderMonthlyChart(canvasId, monthlyData) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = monthlyData.months ? monthlyData.months.map(m => m.substring(0, 3)) : [];
    const totals = monthlyData.totals || [];

    // Create gradient
    const chartCtx = ctx.getContext('2d');
    const gradient = chartCtx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.45)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.01)');

    const config = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: `Spending (${monthlyData.year})`,
          data: totals,
          borderColor: '#818cf8',
          borderWidth: 3,
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: '#6366f1',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 7
        }]
      },
      options: this.getBaseOptions()
    };

    this.instances[canvasId] = new Chart(ctx, config);
  },

  // 2. Category Spending Bar Chart
  renderCategoryBarChart(canvasId, categoryData) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const categories = categoryData.categories || [];
    const labels = categories.map(c => c.category);
    const amounts = categories.map(c => c.total);

    const baseOptions = this.getBaseOptions();
    baseOptions.plugins.legend.display = false;

    const config = {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Spent',
          data: amounts,
          backgroundColor: categories.map((_, i) => this.colors[i % this.colors.length] + 'cc'),
          borderColor: categories.map((_, i) => this.colors[i % this.colors.length]),
          borderWidth: 1.5,
          borderRadius: 6
        }]
      },
      options: baseOptions
    };

    this.instances[canvasId] = new Chart(ctx, config);
  },

  // 3. Category Distribution Donut Chart
  renderCategoryDonutChart(canvasId, categoryData) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const categories = categoryData.categories || [];
    const labels = categories.map(c => c.category);
    const amounts = categories.map(c => c.total);

    const config = {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: amounts,
          backgroundColor: categories.map((_, i) => this.colors[i % this.colors.length]),
          borderColor: '#111827',
          borderWidth: 3,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#94a3b8',
              font: { family: 'Inter', size: 11 },
              boxWidth: 12,
              padding: 10
            }
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#ffffff',
            bodyColor: '#cbd5e1',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const val = context.parsed;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return `${context.label}: ${AppState.formatCurrency(val)} (${pct}%)`;
              }
            }
          }
        }
      }
    };

    this.instances[canvasId] = new Chart(ctx, config);
  },

  // 4. Daily Spending Timeline Chart
  renderDailyChart(canvasId, dailyData) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const labels = dailyData.labels || [];
    const amounts = dailyData.amounts || [];

    const chartCtx = ctx.getContext('2d');
    const gradient = chartCtx.createLinearGradient(0, 0, 0, 220);
    gradient.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
    gradient.addColorStop(1, 'rgba(6, 182, 212, 0.01)');

    const config = {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Daily Expenses',
          data: amounts,
          borderColor: '#22d3ee',
          backgroundColor: gradient,
          borderWidth: 2.5,
          fill: true,
          tension: 0.25,
          pointRadius: 2,
          pointHoverRadius: 6,
          pointBackgroundColor: '#06b6d4'
        }]
      },
      options: this.getBaseOptions()
    };

    this.instances[canvasId] = new Chart(ctx, config);
  }
};
