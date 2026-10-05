/**
 * KisanMitra — frontend/app.js
 * UI State Machine & Interaction Controller per PRD §8, DESIGN.md, and RULES.md §2.
 */

class KisanApp {
  constructor() {
    this.currentLanguage = 'mr'; // Default: Marathi
    this.activeDistrict = 'nashik';
    this.speech = new KisanSpeech();
    this.i18nData = {};
    this.currentCard = null;
    this.autoSendTimer = null;
    this.isListening = false;
    this.isPlayingAudio = false;

    // Default mock data map
    this.mockFiles = {
      what_to_grow: 'mock/what_to_grow_mr.json',
      weather_today: 'mock/weather_today_mr.json',
      prices: 'mock/prices_mr.json',
      how_to_grow: 'mock/how_to_grow_mr.json'
    };

    this.init();
  }

  async init() {
    await this.loadAllI18n();
    this.applyLanguage(this.currentLanguage);
    this.setupSpeechEvents();
  }

  async loadAllI18n() {
    const langs = ['mr', 'hi', 'en'];
    for (const lang of langs) {
      try {
        const res = await fetch(`i18n/${lang}.json`);
        if (res.ok) {
          this.i18nData[lang] = await res.json();
        }
      } catch (err) {
        console.warn(`Could not load i18n for ${lang}:`, err);
      }
    }
  }

  setLanguage(lang) {
    if (!['en', 'hi', 'mr'].includes(lang)) return;
    this.currentLanguage = lang;
    this.speech.stopSpeaking();
    this.speech.stopListening();
    this.resetMicUI();

    // Update active pill button
    document.querySelectorAll('.lang-opt').forEach(btn => {
      if (btn.getAttribute('data-lang') === lang) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    this.applyLanguage(lang);
  }

  applyLanguage(lang) {
    const dict = this.i18nData[lang];
    if (!dict) return;

    // 1. Branding & Top Bar
    const titleEl = document.getElementById('app-title');
    if (titleEl) titleEl.innerText = dict.app_title;

    const districtPill = document.getElementById('district-pill');
    if (districtPill) {
      districtPill.innerHTML = `<span>${dict.active_district}</span>`;
    }

    // 2. Hero Mic & Status
    const statusText = document.getElementById('mic-status-text');
    if (statusText) statusText.innerText = dict.mic_idle_label;

    const blockedAlert = document.getElementById('mic-blocked-alert');
    if (blockedAlert) blockedAlert.innerText = dict.mic_blocked_warning;

    const heardLabel = document.getElementById('speech-heard-label');
    if (heardLabel) heardLabel.innerText = dict.mic_heard_label;

    // 3. Chat Bar
    const chatInput = document.getElementById('chat-input-field');
    if (chatInput) chatInput.placeholder = dict.chat_placeholder;

    // 4. Prompt Chips
    const chipsTitle = document.getElementById('chips-title');
    if (chipsTitle) chipsTitle.innerText = dict.prompts_title;

    const chipsContainer = document.getElementById('chips-container');
    if (chipsContainer && dict.prompts) {
      chipsContainer.innerHTML = '';
      dict.prompts.forEach(promptText => {
        const chip = document.createElement('div');
        chip.className = 'prompt-chip';
        chip.innerText = promptText;
        chip.onclick = () => this.handlePromptSelect(promptText);
        chipsContainer.appendChild(chip);
      });
    }

    // 5. 2x2 Feature Grid
    if (dict.feature_grid) {
      document.getElementById('feat-grow-title').innerText = dict.feature_grid.grow_title;
      document.getElementById('feat-grow-sub').innerText = dict.feature_grid.grow_sub;

      document.getElementById('feat-weather-title').innerText = dict.feature_grid.weather_title;
      document.getElementById('feat-weather-sub').innerText = dict.feature_grid.weather_sub;

      document.getElementById('feat-price-title').innerText = dict.feature_grid.price_title;
      document.getElementById('feat-price-sub').innerText = dict.feature_grid.price_sub;

      document.getElementById('feat-guide-title').innerText = dict.feature_grid.guide_title;
      document.getElementById('feat-guide-sub').innerText = dict.feature_grid.guide_sub;
    }

    // 6. Thinking State Strings
    if (dict.thinking) {
      document.getElementById('think-weather').innerText = dict.thinking.weather;
      document.getElementById('think-soil').innerText = dict.thinking.soil;
      document.getElementById('think-market').innerText = dict.thinking.market;
    }

    // 7. Result Sheet Static Labels
    if (dict.result) {
      document.getElementById('steps-header').innerText = dict.result.steps_title;
      document.getElementById('btn-call-kvk').querySelector('span').innerText = dict.result.call_kvk;
      document.getElementById('btn-ask-another').querySelector('span').innerText = dict.result.ask_another;
      document.getElementById('listen-again-btn').querySelector('span').innerText = dict.result.listen_again;
    }
  }

  speakWelcomeGreeting() {
    const dict = this.i18nData[this.currentLanguage];
    if (dict && dict.welcome_greeting) {
      this.speech.speak({
        text: dict.welcome_greeting,
        lang: this.currentLanguage,
        onStart: () => this.setAudioPlaying(true),
        onEnd: () => this.setAudioPlaying(false),
        onError: () => this.setAudioPlaying(false)
      });
    }
  }

  /* ---------------- Voice Interaction Logic ---------------- */

  setupSpeechEvents() {
    // Check if STT is supported
    if (!this.speech.isSTTSupported()) {
      const alertEl = document.getElementById('mic-blocked-alert');
      if (alertEl) alertEl.style.display = 'block';
    }
  }

  handleMicToggle() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    this.speech.stopSpeaking();
    this.clearAutoSend();

    const started = this.speech.startListening({
      lang: this.currentLanguage,
      onStart: () => {
        this.isListening = true;
        this.setMicListeningUI(true);
      },
      onInterim: (text) => {
        this.showSpeechPreview(text, false);
      },
      onFinal: (text) => {
        this.showSpeechPreview(text, true);
        this.startAutoSendCountdown(text);
      },
      onError: (err) => {
        console.warn('Speech error:', err);
        this.isListening = false;
        this.setMicListeningUI(false);
        const alertEl = document.getElementById('mic-blocked-alert');
        if (alertEl) {
          alertEl.style.display = 'block';
          setTimeout(() => { alertEl.style.display = 'none'; }, 5000);
        }
      },
      onEnd: (final) => {
        this.isListening = false;
        this.setMicListeningUI(false);
        if (final && !this.autoSendTimer) {
          this.startAutoSendCountdown(final);
        }
      }
    });

    if (!started) {
      const alertEl = document.getElementById('mic-blocked-alert');
      if (alertEl) alertEl.style.display = 'block';
    }
  }

  stopListening() {
    this.speech.stopListening();
    this.isListening = false;
    this.setMicListeningUI(false);
  }

  setMicListeningUI(isListening) {
    const boundary = document.getElementById('mic-boundary');
    const micBtn = document.getElementById('hero-mic-btn');
    const statusText = document.getElementById('mic-status-text');
    const dict = this.i18nData[this.currentLanguage] || {};

    if (isListening) {
      boundary.classList.add('is-listening');
      micBtn.classList.remove('idle');
      statusText.innerText = dict.mic_listening_label || 'Listening...';
    } else {
      boundary.classList.remove('is-listening');
      micBtn.classList.add('idle');
      statusText.innerText = dict.mic_idle_label || 'Speak, we are listening...';
    }
  }

  resetMicUI() {
    this.setMicListeningUI(false);
    this.clearAutoSend();
    const preview = document.getElementById('speech-preview-card');
    if (preview) preview.style.display = 'none';
  }

  showSpeechPreview(text, isFinal) {
    const preview = document.getElementById('speech-preview-card');
    const transcriptEl = document.getElementById('live-transcript-text');
    if (preview && transcriptEl) {
      preview.style.display = 'block';
      transcriptEl.innerText = text;
    }
  }

  startAutoSendCountdown(text) {
    this.clearAutoSend();
    const progressBar = document.getElementById('auto-send-progress');
    if (progressBar) {
      progressBar.style.width = '0%';
      requestAnimationFrame(() => {
        progressBar.style.width = '100%';
      });
    }

    this.autoSendTimer = setTimeout(() => {
      this.clearAutoSend();
      this.sendQuery(text);
    }, 1500);
  }

  cancelSpeechInput() {
    this.clearAutoSend();
    this.stopListening();
    const preview = document.getElementById('speech-preview-card');
    if (preview) preview.style.display = 'none';
  }

  clearAutoSend() {
    if (this.autoSendTimer) {
      clearTimeout(this.autoSendTimer);
      this.autoSendTimer = null;
    }
    const progressBar = document.getElementById('auto-send-progress');
    if (progressBar) progressBar.style.width = '0%';
  }

  /* ---------------- Query Dispatch & Results ---------------- */

  handleChatSubmit() {
    const input = document.getElementById('chat-input-field');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    this.sendQuery(text);
  }

  handlePromptSelect(promptText) {
    this.sendQuery(promptText);
  }

  async triggerFlow(intentKey) {
    this.showThinkingState(true);
    // In Phase 1 mock mode, load mock card for the intent
    try {
      const res = await fetch(`/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          intent: intentKey,
          language: this.currentLanguage,
          district: this.activeDistrict
        })
      });

      if (res.ok) {
        const card = await res.json();
        this.renderResultCard(card);
      } else {
        const mockCard = await this.loadMockCard(intentKey);
        this.renderResultCard(mockCard);
      }
    } catch (e) {
      console.warn('API error, falling back to mock card:', e);
      const mockCard = await this.loadMockCard(intentKey);
      this.renderResultCard(mockCard);
    } finally {
      this.showThinkingState(false);
    }
  }

  async sendQuery(queryText) {
    this.resetMicUI();
    this.showThinkingState(true);

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: queryText,
          language: this.currentLanguage,
          district: this.activeDistrict
        })
      });

      if (res.ok) {
        const card = await res.json();
        this.renderResultCard(card);
      } else {
        // Fallback to what_to_grow mock
        const mockCard = await this.loadMockCard('what_to_grow');
        this.renderResultCard(mockCard);
      }
    } catch (err) {
      console.warn('Chat request failed, loading mock response:', err);
      const mockCard = await this.loadMockCard('what_to_grow');
      this.renderResultCard(mockCard);
    } finally {
      this.showThinkingState(false);
    }
  }

  async loadMockCard(flowName) {
    const filename = `mock/${flowName}_mr.json`;
    try {
      const res = await fetch(filename);
      if (res.ok) {
        const data = await res.json();
        data.language = this.currentLanguage;
        return data;
      }
    } catch (e) {
      console.warn(`Could not load ${filename}:`, e);
    }
    return null;
  }

  showThinkingState(show) {
    const banner = document.getElementById('thinking-banner');
    if (banner) banner.style.display = show ? 'block' : 'none';
  }

  renderResultCard(card) {
    if (!card) return;
    this.currentCard = card;

    // Populate Title
    document.getElementById('card-title').innerText = card.title || 'शेती सल्ला';

    // Populate Metrics (Up to 3) with Traffic-Light styling
    const metricsRow = document.getElementById('card-metrics-row');
    metricsRow.innerHTML = '';
    const metrics = card.metrics || [
      { label: 'कालावधी', value: '११० दिवस' },
      { label: 'अंदाजे उत्पन्न', value: '₹१,४०,०००' },
      { label: 'बाजार कल', value: '↗ स्थिर' }
    ];
    metrics.slice(0, 3).forEach(m => {
      const badge = document.createElement('div');
      badge.className = 'metric-badge';
      const valStr = String(m.value || '');
      const lblStr = String(m.label || '');

      // Traffic-light logic
      if (valStr.includes('✅') || valStr.includes('अनुकूल') || valStr.toLowerCase().includes('favorable') || valStr.includes('सुरक्षित')) {
        badge.classList.add('traffic-green');
      } else if (valStr.includes('⚠️') || valStr.includes('सावध') || valStr.toLowerCase().includes('caution') || valStr.includes('मध्यम')) {
        badge.classList.add('traffic-amber');
      } else if (valStr.includes('⛔') || valStr.includes('धोका') || valStr.toLowerCase().includes('danger') || valStr.includes('टाळा')) {
        badge.classList.add('traffic-red');
      }

      badge.innerHTML = `
        <div class="metric-label">${m.label}</div>
        <div class="metric-value">${m.value}</div>
      `;
      metricsRow.appendChild(badge);
    });

    // Populate Summary Lines (Max 3)
    const summaryBox = document.getElementById('card-summary-lines');
    summaryBox.innerHTML = '';
    (card.summary_lines || []).slice(0, 3).forEach(line => {
      const p = document.createElement('div');
      p.className = 'summary-line';
      p.innerText = line;
      summaryBox.appendChild(p);
    });

    // Populate Actionable Steps (Max 3)
    const stepsList = document.getElementById('card-steps-list');
    stepsList.innerHTML = '';
    const steps = card.steps || [];
    steps.slice(0, 3).forEach((stepText, idx) => {
      const item = document.createElement('div');
      item.className = 'step-item';
      item.innerHTML = `
        <div class="step-num">${idx + 1}</div>
        <div>${stepText.replace(/^[0-9]+[.\-]\s*/, '')}</div>
      `;
      stepsList.appendChild(item);
    });

    // Honesty Tagline
    const honestyTag = document.getElementById('card-honesty-tag');
    const sourcesStr = (card.sources || []).join(', ');
    const labelsStr = (card.labels || []).join(' | ');
    honestyTag.innerText = `स्रोत: ${sourcesStr || 'MPKV'} | ${labelsStr || 'प्रातिनिधिक माहिती'}`;

    // Update KVK Link
    const kvkBtn = document.getElementById('btn-call-kvk');
    if (kvkBtn) {
      // Default to Kisan Call Centre 1800-180-1551 (toll-free national agri helpline)
      kvkBtn.href = "tel:18001801551";
    }

    // Open Bottom-Sheet
    const overlay = document.getElementById('result-overlay');
    if (overlay) overlay.classList.add('active');

    // Auto Read-Aloud
    if (card.speak_text) {
      setTimeout(() => {
        this.speech.speak({
          text: card.speak_text,
          lang: card.language || this.currentLanguage,
          onStart: () => this.setAudioPlaying(true),
          onEnd: () => this.setAudioPlaying(false),
          onError: () => this.setAudioPlaying(false)
        });
      }, 350);
    }
  }

  replayAudio() {
    if (this.isPlayingAudio) {
      this.speech.stopSpeaking();
      this.setAudioPlaying(false);
      return;
    }

    if (this.currentCard && this.currentCard.speak_text) {
      this.speech.speak({
        text: this.currentCard.speak_text,
        lang: this.currentCard.language || this.currentLanguage,
        onStart: () => this.setAudioPlaying(true),
        onEnd: () => this.setAudioPlaying(false),
        onError: () => this.setAudioPlaying(false)
      });
    }
  }

  setAudioPlaying(isPlaying) {
    this.isPlayingAudio = isPlaying;
    const waveAnim = document.getElementById('audio-wave-anim');
    const btnSpan = document.getElementById('listen-again-btn').querySelector('span');
    const dict = this.i18nData[this.currentLanguage] || {};

    if (isPlaying) {
      waveAnim.classList.add('is-playing');
      if (btnSpan) btnSpan.innerText = dict.result ? dict.result.stop_audio : '⏹️ आवाज थांबवा';
    } else {
      waveAnim.classList.remove('is-playing');
      if (btnSpan) btnSpan.innerText = dict.result ? dict.result.listen_again : '🔊 पुन्हा ऐका';
    }
  }

  closeResultAndAskAgain() {
    this.speech.stopSpeaking();
    this.setAudioPlaying(false);
    const overlay = document.getElementById('result-overlay');
    if (overlay) overlay.classList.remove('active');
    setTimeout(() => {
      this.startListening();
    }, 200);
  }

  handleOverlayClick(e) {
    if (e.target.id === 'result-overlay') {
      this.speech.stopSpeaking();
      this.setAudioPlaying(false);
      document.getElementById('result-overlay').classList.remove('active');
    }
  }
}

// Instantiate globally
window.addEventListener('DOMContentLoaded', () => {
  window.app = new KisanApp();
});
