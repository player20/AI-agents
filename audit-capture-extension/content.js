// Audit Capture Extension - Content Script
// Runs on all pages to detect user interactions

(function() {
  let isRecording = false;

  // Listen for messages from popup
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'startRecording') {
      isRecording = true;
      console.log('Audit Capture: Recording started');
      attachListeners();
    }

    if (message.action === 'stopRecording') {
      isRecording = false;
      console.log('Audit Capture: Recording stopped');
      detachListeners();
    }
  });

  // Check initial state
  chrome.storage.local.get(['isRecording'], (state) => {
    if (state.isRecording) {
      isRecording = true;
      attachListeners();
    }
  });

  function attachListeners() {
    document.addEventListener('click', handleClick, true);
    document.addEventListener('input', handleInput, true);
    document.addEventListener('submit', handleSubmit, true);

    // Detect page navigation
    const observer = new MutationObserver(() => {
      if (isRecording) {
        // Check if URL changed (for SPAs)
        const currentUrl = window.location.href;
        if (currentUrl !== lastUrl) {
          lastUrl = currentUrl;
          notifyPageChange();
        }
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  function detachListeners() {
    document.removeEventListener('click', handleClick, true);
    document.removeEventListener('input', handleInput, true);
    document.removeEventListener('submit', handleSubmit, true);
  }

  let lastUrl = window.location.href;

  function handleClick(event) {
    if (!isRecording) return;

    const element = event.target;
    const tagName = element.tagName.toLowerCase();
    const text = element.innerText?.substring(0, 50) || '';
    const className = element.className;
    const id = element.id;

    // Log button, link, and interactive element clicks
    if (['button', 'a', 'input', 'ion-button', 'app-button'].includes(tagName) ||
        element.getAttribute('role') === 'button' ||
        element.onclick) {

      chrome.runtime.sendMessage({
        action: 'clickDetected',
        element: {
          tag: tagName,
          id: id,
          class: className,
          type: element.type || null
        },
        text: text,
        url: window.location.href
      });

      console.log('Audit Capture: Click detected', { tag: tagName, text, id, className });
    }
  }

  function handleInput(event) {
    if (!isRecording) return;

    const element = event.target;
    const tagName = element.tagName.toLowerCase();

    if (['input', 'textarea', 'select'].includes(tagName)) {
      chrome.runtime.sendMessage({
        action: 'formInteraction',
        field: {
          tag: tagName,
          type: element.type || 'text',
          name: element.name || null,
          id: element.id || null,
          placeholder: element.placeholder || null
        },
        type: 'input',
        url: window.location.href
      });
    }
  }

  function handleSubmit(event) {
    if (!isRecording) return;

    chrome.runtime.sendMessage({
      action: 'formInteraction',
      field: {
        formId: event.target.id,
        formAction: event.target.action
      },
      type: 'submit',
      url: window.location.href
    });

    console.log('Audit Capture: Form submitted');
  }

  function notifyPageChange() {
    chrome.runtime.sendMessage({
      action: 'pageChanged',
      url: window.location.href,
      title: document.title
    });

    console.log('Audit Capture: Page changed to', window.location.href);
  }

  // Initial page notification
  if (isRecording) {
    notifyPageChange();
  }

  // Handle SPA navigation
  window.addEventListener('popstate', () => {
    if (isRecording) {
      setTimeout(notifyPageChange, 100);
    }
  });

  // Intercept history.pushState for SPAs
  const originalPushState = history.pushState;
  history.pushState = function() {
    originalPushState.apply(this, arguments);
    if (isRecording) {
      setTimeout(notifyPageChange, 100);
    }
  };

  const originalReplaceState = history.replaceState;
  history.replaceState = function() {
    originalReplaceState.apply(this, arguments);
    if (isRecording) {
      setTimeout(notifyPageChange, 100);
    }
  };

  console.log('Audit Capture: Content script loaded');
})();
