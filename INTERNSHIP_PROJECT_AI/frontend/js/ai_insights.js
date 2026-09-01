/**
 * ExpenseAI - AI Insights, Health Score & Predictive Intelligence Module
 */

const AiInsightsView = {
  async render() {
    try {
      const month = AppState.selectedMonth;
      const year = AppState.selectedYear;

      const [healthData, predData, insightsData] = await Promise.all([
        API.getHealthScore(month, year),
        API.getPrediction(month, year),
        API.getAiInsights(month, year)
      ]);

      // 1. Expense Health Score
      this.renderHealthScore(healthData);

      // 2. AI Burn Rate & Month-End Prediction
      this.renderPrediction(predData);

      // 3. Dynamic Suggestions Feed
      this.renderSuggestions(insightsData);

    } catch (err) {
      console.error('[AI Insights Render Error]', err);
      AppState.showToast('Failed to load AI Insights: ' + err.message, 'error');
    }
  },

  renderHealthScore(data) {
    const score = data.score || 0;
    const gaugeEl = document.getElementById('health-gauge-circle');
    if (gaugeEl) {
      gaugeEl.style.setProperty('--score-pct', score);
      // Change color based on score
      if (score >= 80) {
        gaugeEl.style.background = `conic-gradient(#10b981 ${score}%, rgba(255,255,255,0.08) 0)`;
      } else if (score >= 65) {
        gaugeEl.style.background = `conic-gradient(#06b6d4 ${score}%, rgba(255,255,255,0.08) 0)`;
      } else if (score >= 45) {
        gaugeEl.style.background = `conic-gradient(#f59e0b ${score}%, rgba(255,255,255,0.08) 0)`;
      } else {
        gaugeEl.style.background = `conic-gradient(#f43f5e ${score}%, rgba(255,255,255,0.08) 0)`;
      }
    }

    const numEl = document.getElementById('health-gauge-number');
    if (numEl) numEl.textContent = score;

    const gradeEl = document.getElementById('health-grade-text');
    if (gradeEl) gradeEl.textContent = data.grade;

    const summaryEl = document.getElementById('health-summary-text');
    if (summaryEl) summaryEl.textContent = data.summary;

    // Breakdown List
    const breakdownList = document.getElementById('health-breakdown-list');
    if (breakdownList) {
      breakdownList.innerHTML = (data.breakdown || []).map(b => {
        const pct = ((b.score / b.max) * 100).toFixed(0);
        return `
          <div style="margin-bottom:8px;">
            <div class="breakdown-item-header">
              <span style="color:#e2e8f0;">${b.name}</span>
              <span style="color:#94a3b8;">${b.score}/${b.max} pts</span>
            </div>
            <div class="breakdown-item-bar">
              <div class="breakdown-item-fill" style="width:${pct}%;"></div>
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-top:2px;">${b.detail}</div>
          </div>
        `;
      }).join('');
    }

    // Health Tips
    const tipsList = document.getElementById('health-tips-list');
    if (tipsList) {
      tipsList.innerHTML = (data.tips || []).map(t => `
        <li style="margin-bottom:6px; color:#cbd5e1; font-size:0.84rem; display:flex; align-items:start; gap:8px;">
          <i class="fa-solid fa-check" style="color:#10b981; margin-top:3px;"></i>
          <span>${t}</span>
        </li>
      `).join('');
    }
  },

  renderPrediction(pred) {
    const elProj = document.getElementById('pred-projected-amt');
    if (elProj) elProj.textContent = AppState.formatCurrency(pred.estimated_month_end);

    const elBurn = document.getElementById('pred-burn-rate');
    if (elBurn) elBurn.textContent = `${AppState.formatCurrency(pred.daily_burn_rate)} / day`;

    const elDays = document.getElementById('pred-days-left');
    if (elDays) elDays.textContent = `${pred.days_remaining} days remaining`;

    const elConf = document.getElementById('pred-confidence');
    if (elConf) elConf.textContent = pred.confidence;

    const elMsg = document.getElementById('pred-message');
    if (elMsg) elMsg.textContent = pred.message;

    const elWarn = document.getElementById('pred-warning-banner');
    if (elWarn) {
      if (pred.budget_warning) {
        elWarn.style.display = 'block';
        elWarn.textContent = pred.budget_warning;
      } else {
        elWarn.style.display = 'none';
      }
    }
  },

  renderSuggestions(insightsData) {
    const feed = document.getElementById('ai-suggestions-feed');
    if (!feed) return;

    const list = (insightsData && insightsData.insights) || [];
    const gemini = insightsData && insightsData.gemini_analysis;

    let html = '';

    // Gemini Cloud Analysis card if available
    if (gemini && gemini.summary) {
      html += `
        <div class="suggestion-card tip" style="background:linear-gradient(135deg, rgba(99,102,241,0.15), rgba(168,85,247,0.1)); border-color:rgba(168,85,247,0.4);">
          <div class="suggestion-top">
            <div class="suggestion-title" style="color:#c084fc;">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Gemini AI Strategic Summary
            </div>
            <span class="badge-pill" style="background:rgba(168,85,247,0.2); color:#e9d5ff;">Cloud AI</span>
          </div>
          <p class="suggestion-text" style="color:#f1f5f9; font-weight:500;">${gemini.summary}</p>
          ${gemini.savings_opportunity ? `<p class="suggestion-text" style="margin-top:8px; color:#38bdf8;"><strong>Top Savings Opportunity:</strong> ${gemini.savings_opportunity}</p>` : ''}
        </div>
      `;
    }

    if (list.length === 0 && !gemini) {
      feed.innerHTML = `
        <div class="card" style="padding:24px; text-align:center; color:#64748b;">
          No suggestions generated yet. Add more expense transactions to activate AI pattern analysis.
        </div>
      `;
      return;
    }

    html += list.map(item => {
      let icon = 'fa-lightbulb';
      if (item.type === 'warning') icon = 'fa-triangle-exclamation';
      if (item.type === 'danger') icon = 'fa-circle-exclamation';
      if (item.type === 'success') icon = 'fa-circle-check';

      return `
        <div class="suggestion-card ${item.type}">
          <div class="suggestion-top">
            <div class="suggestion-title">
              <i class="fa-solid ${icon}"></i> ${item.title}
            </div>
            <span class="badge-pill" style="background:rgba(255,255,255,0.06); color:#94a3b8;">${item.tag || item.category}</span>
          </div>
          <p class="suggestion-text">${item.message}</p>
        </div>
      `;
    }).join('');

    feed.innerHTML = html;
  },

  async handleAiChat(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('ai-chat-input');
    const query = input.value.trim();
    if (!query) return;

    const respBox = document.getElementById('ai-chat-response');
    const respText = document.getElementById('ai-chat-response-text');
    const btn = document.getElementById('ai-chat-submit-btn');

    try {
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...`;

      respBox.style.display = 'block';
      respText.innerHTML = `<span style="color:#94a3b8;"><i class="fa-solid fa-circle-notch fa-spin"></i> ExpenseAI is reviewing your financial patterns...</span>`;

      const res = await API.sendAiChat(query);
      respText.innerHTML = `<div style="font-weight:600; color:#818cf8; margin-bottom:6px;"><i class="fa-solid fa-robot"></i> ${res.source || 'ExpenseAI Advisor'}:</div><div>${AppState.formatMarkdown(res.reply)}</div>`;
      input.value = '';
    } catch (err) {
      respText.innerHTML = `<span style="color:#f43f5e;">Error: ${err.message}</span>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Ask AI`;
    }
  },

  askPreset(query) {
    const input = document.getElementById('ai-chat-input');
    if (input) {
      input.value = query;
      this.handleAiChat();
    }
  }
};
