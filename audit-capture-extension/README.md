# Audit Capture - Chrome Extension

A Chrome extension for capturing app screens and user interactions during UX audits. Exports to Weaver Pro format.

## Features

- **Start/Stop Recording**: Track your navigation through an app
- **Auto Screenshot**: Manually capture screenshots at any point
- **Interaction Tracking**: Logs clicks, form inputs, and page navigations
- **Export Session**: Download JSON + screenshots for Weaver Pro

## Installation

### Developer Mode (for testing)

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select this `audit-capture-extension` folder
5. The extension icon will appear in your toolbar

### Creating Icons

Before using, create icon files:
- `icons/icon16.png` (16x16 pixels)
- `icons/icon48.png` (48x48 pixels)
- `icons/icon128.png` (128x128 pixels)

You can use any icon generator or create simple colored squares.

## Usage

### Basic Workflow

1. **Navigate to your app** in Chrome
2. **Click the extension icon** in the toolbar
3. **Click "Start Recording"** - this begins tracking
4. **Navigate through your app** normally
5. **Click "Capture Screenshot Now"** at key screens
6. **Click "Stop Recording"** when done
7. **Click "Export Session"** to download data

### What Gets Captured

- **Screenshots**: PNG images of the visible tab
- **Page Navigations**: URL and title of each page visited
- **Clicks**: Button, link, and interactive element clicks
- **Form Interactions**: Input field interactions (not values for privacy)

### Export Format

The extension exports:

1. **JSON file** (`audit-session-[app]-[timestamp].json`):
```json
{
  "appName": "juicenet.ai",
  "startTime": "2026-01-15T10:30:00.000Z",
  "endTime": "2026-01-15T10:35:00.000Z",
  "summary": {
    "totalScreenshots": 10,
    "totalPages": 8,
    "totalClicks": 15,
    "totalFormInteractions": 5
  },
  "pages": [...],
  "screenshots": [...],
  "clicks": [...],
  "formInteractions": [...]
}
```

2. **Screenshots folder** (`audit-screenshots/`):
   - `001-landing-page.png`
   - `002-signup-form.png`
   - etc.

## Importing to Weaver Pro

1. Run Weaver Pro: `streamlit run app.py`
2. Check "I have code to upgrade"
3. Upload the JSON file
4. Reference screenshots in your analysis prompt:
   ```
   "Analyze these screenshots of the user journey.
   The JSON shows navigation flow and interactions.
   Identify UX issues and drop-off risks."
   ```

## Keyboard Shortcuts (Optional)

To enable keyboard shortcuts:
1. Go to `chrome://extensions/shortcuts`
2. Find "Audit Capture"
3. Set shortcuts for:
   - Capture Screenshot: e.g., `Ctrl+Shift+S`

## Privacy

- Screenshots are stored locally in Chrome storage
- No data is sent to any server
- Form input VALUES are not captured (only field names)
- Clear session to remove all data

## Troubleshooting

### Extension not working on certain pages
- Some pages (chrome://, about:, etc.) block extensions
- Bank/payment pages may block screenshot capture

### Screenshots not capturing
- Make sure the tab is active and visible
- Some pages may block tab capture API

### Export not downloading
- Check Chrome's download settings
- Allow multiple downloads if prompted

## Development

### File Structure
```
audit-capture-extension/
├── manifest.json      # Extension configuration
├── popup.html         # Extension popup UI
├── popup.js           # Popup logic
├── content.js         # Page interaction tracking
├── background.js      # Service worker
├── icons/             # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

### Testing Changes
1. Make your code changes
2. Go to `chrome://extensions/`
3. Click the refresh icon on the extension card
4. Test your changes

## License

Part of the Weaver Pro toolkit.
