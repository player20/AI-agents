// Audit Capture Extension - Background Service Worker

// Listen for tab updates to detect navigation
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    chrome.storage.local.get(['isRecording'], (state) => {
      if (state.isRecording) {
        // Notify popup about page change
        chrome.runtime.sendMessage({
          action: 'pageChanged',
          url: tab.url,
          title: tab.title
        }).catch(() => {
          // Popup might not be open, that's okay
        });
      }
    });
  }
});

// Handle extension icon click when popup is not shown
chrome.action.onClicked.addListener((tab) => {
  // This won't fire if popup is set, but keeping for future flexibility
});

// Listen for keyboard shortcuts (optional enhancement)
chrome.commands?.onCommand?.addListener((command) => {
  if (command === 'capture-screenshot') {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs[0]) {
        const dataUrl = await chrome.tabs.captureVisibleTab(null, {
          format: 'png',
          quality: 100
        });

        chrome.storage.local.get(['isRecording', 'session'], async (state) => {
          if (state.session) {
            const screenshot = {
              id: (state.session.screenshots?.length || 0) + 1,
              filename: `${String((state.session.screenshots?.length || 0) + 1).padStart(3, '0')}-screenshot.png`,
              url: tabs[0].url,
              title: tabs[0].title,
              timestamp: new Date().toISOString(),
              dataUrl: dataUrl
            };

            state.session.screenshots = state.session.screenshots || [];
            state.session.screenshots.push(screenshot);

            await chrome.storage.local.set({ session: state.session });
          }
        });
      }
    });
  }
});

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('Audit Capture extension installed');

  // Set initial state
  chrome.storage.local.set({
    isRecording: false,
    session: {
      startTime: null,
      pages: [],
      screenshots: [],
      clicks: [],
      formInteractions: []
    }
  });
});

console.log('Audit Capture: Background service worker started');
