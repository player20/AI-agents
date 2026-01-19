// Audit Capture Extension - Popup Script

class AuditCapture {
  constructor() {
    this.isRecording = false;
    this.session = {
      startTime: null,
      pages: [],
      screenshots: [],
      clicks: [],
      formInteractions: []
    };

    this.init();
  }

  async init() {
    // Load saved state
    const state = await chrome.storage.local.get(['isRecording', 'session']);
    if (state.isRecording) {
      this.isRecording = true;
      this.session = state.session || this.session;
    }

    this.updateUI();
    this.bindEvents();
  }

  bindEvents() {
    document.getElementById('start-btn').addEventListener('click', () => this.startRecording());
    document.getElementById('stop-btn').addEventListener('click', () => this.stopRecording());
    document.getElementById('capture-btn').addEventListener('click', () => this.captureScreenshot());
    document.getElementById('export-btn').addEventListener('click', () => this.exportSession());
    document.getElementById('clear-btn').addEventListener('click', () => this.clearSession());
  }

  async startRecording() {
    this.isRecording = true;
    this.session = {
      startTime: new Date().toISOString(),
      appName: '',
      pages: [],
      screenshots: [],
      clicks: [],
      formInteractions: []
    };

    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      try {
        const url = new URL(tab.url);
        this.session.appName = url.hostname;
      } catch (e) {
        this.session.appName = 'Unknown App';
      }

      // Add initial page
      this.addPage(tab.url, tab.title);

      // Capture initial screenshot
      await this.captureScreenshot();
    }

    // Save state
    await chrome.storage.local.set({
      isRecording: true,
      session: this.session
    });

    // Notify content script
    chrome.tabs.sendMessage(tab.id, { action: 'startRecording' });

    this.updateUI();
  }

  async stopRecording() {
    this.isRecording = false;

    // Save final state
    await chrome.storage.local.set({
      isRecording: false,
      session: this.session
    });

    // Notify content script
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      chrome.tabs.sendMessage(tab.id, { action: 'stopRecording' });
    }

    this.updateUI();
  }

  async captureScreenshot() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) return;

      // Capture visible tab
      const dataUrl = await chrome.tabs.captureVisibleTab(null, {
        format: 'png',
        quality: 100
      });

      const screenshot = {
        id: this.session.screenshots.length + 1,
        filename: `${String(this.session.screenshots.length + 1).padStart(3, '0')}-${this.sanitizeFilename(tab.title)}.png`,
        url: tab.url,
        title: tab.title,
        timestamp: new Date().toISOString(),
        dataUrl: dataUrl
      };

      this.session.screenshots.push(screenshot);

      // Save state
      await chrome.storage.local.set({ session: this.session });

      this.updateUI();
      this.showNotification('Screenshot captured!');

    } catch (error) {
      console.error('Screenshot error:', error);
      this.showNotification('Failed to capture screenshot');
    }
  }

  addPage(url, title) {
    const page = {
      url: url,
      title: title,
      timestamp: new Date().toISOString()
    };

    // Avoid duplicates
    const lastPage = this.session.pages[this.session.pages.length - 1];
    if (!lastPage || lastPage.url !== url) {
      this.session.pages.push(page);
    }
  }

  sanitizeFilename(name) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 30);
  }

  async exportSession() {
    if (this.session.screenshots.length === 0) {
      this.showNotification('No screenshots to export');
      return;
    }

    // Create export data (without base64 images for JSON)
    const exportData = {
      appName: this.session.appName,
      startTime: this.session.startTime,
      endTime: new Date().toISOString(),
      summary: {
        totalScreenshots: this.session.screenshots.length,
        totalPages: this.session.pages.length,
        totalClicks: this.session.clicks.length,
        totalFormInteractions: this.session.formInteractions.length
      },
      pages: this.session.pages,
      screenshots: this.session.screenshots.map(s => ({
        id: s.id,
        filename: s.filename,
        url: s.url,
        title: s.title,
        timestamp: s.timestamp
      })),
      clicks: this.session.clicks,
      formInteractions: this.session.formInteractions
    };

    // Download JSON
    const jsonBlob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const jsonUrl = URL.createObjectURL(jsonBlob);

    chrome.downloads.download({
      url: jsonUrl,
      filename: `audit-session-${this.session.appName}-${Date.now()}.json`,
      saveAs: true
    });

    // Download screenshots as individual files
    for (const screenshot of this.session.screenshots) {
      chrome.downloads.download({
        url: screenshot.dataUrl,
        filename: `audit-screenshots/${screenshot.filename}`,
        saveAs: false
      });
    }

    this.showNotification('Export started!');
  }

  async clearSession() {
    if (this.isRecording) {
      this.showNotification('Stop recording first');
      return;
    }

    this.session = {
      startTime: null,
      pages: [],
      screenshots: [],
      clicks: [],
      formInteractions: []
    };

    await chrome.storage.local.set({ session: this.session });
    this.updateUI();
    this.showNotification('Session cleared');
  }

  updateUI() {
    const statusEl = document.getElementById('status');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const exportBtn = document.getElementById('export-btn');
    const screenshotCount = document.getElementById('screenshot-count');
    const pageCount = document.getElementById('page-count');
    const clickCount = document.getElementById('click-count');
    const sessionList = document.getElementById('session-list');

    if (this.isRecording) {
      statusEl.textContent = 'Recording...';
      statusEl.className = 'status-value recording';
      startBtn.style.display = 'none';
      stopBtn.style.display = 'flex';
    } else {
      statusEl.textContent = 'Idle';
      statusEl.className = 'status-value idle';
      startBtn.style.display = 'block';
      stopBtn.style.display = 'none';
    }

    screenshotCount.textContent = this.session.screenshots?.length || 0;
    pageCount.textContent = this.session.pages?.length || 0;
    clickCount.textContent = this.session.clicks?.length || 0;

    exportBtn.disabled = (this.session.screenshots?.length || 0) === 0;

    // Update session list
    sessionList.innerHTML = '';
    const recentScreenshots = (this.session.screenshots || []).slice(-5).reverse();
    for (const screenshot of recentScreenshots) {
      const item = document.createElement('div');
      item.className = 'session-item';
      item.innerHTML = `
        <span class="session-url">${screenshot.title || screenshot.url}</span>
        <span class="session-time">${new Date(screenshot.timestamp).toLocaleTimeString()}</span>
      `;
      sessionList.appendChild(item);
    }
  }

  showNotification(message) {
    // Simple notification - could be enhanced with toast UI
    console.log('Audit Capture:', message);
  }
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'pageChanged') {
    // Page navigation detected
    chrome.storage.local.get(['isRecording', 'session'], async (state) => {
      if (state.isRecording && state.session) {
        state.session.pages.push({
          url: message.url,
          title: message.title,
          timestamp: new Date().toISOString()
        });
        await chrome.storage.local.set({ session: state.session });
      }
    });
  }

  if (message.action === 'clickDetected') {
    chrome.storage.local.get(['isRecording', 'session'], async (state) => {
      if (state.isRecording && state.session) {
        state.session.clicks.push({
          element: message.element,
          text: message.text,
          url: message.url,
          timestamp: new Date().toISOString()
        });
        await chrome.storage.local.set({ session: state.session });
      }
    });
  }

  if (message.action === 'formInteraction') {
    chrome.storage.local.get(['isRecording', 'session'], async (state) => {
      if (state.isRecording && state.session) {
        state.session.formInteractions.push({
          field: message.field,
          type: message.type,
          url: message.url,
          timestamp: new Date().toISOString()
        });
        await chrome.storage.local.set({ session: state.session });
      }
    });
  }
});

// Initialize
const auditCapture = new AuditCapture();
