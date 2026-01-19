# Manual Screenshot Workflow for App Audits

When Weaver Pro's automated crawling fails (blocked by auth, custom components, etc.), use this manual workflow to capture app screens for analysis.

---

## Quick Start (5 minutes)

### 1. Open Your App in Chrome

```
1. Open Chrome
2. Navigate to your app URL (localhost or production)
3. Press F12 to open DevTools
```

### 2. Set Mobile Viewport

```
1. Press Ctrl+Shift+M (Toggle Device Toolbar)
2. Select device: "iPhone 14 Pro" (390 x 844)
3. Or custom: 390 x 844
```

### 3. Capture Screenshots

At each screen, press:
```
Ctrl+Shift+P → Type "screenshot" → Select "Capture full size screenshot"
```

Save with naming convention:
```
001-landing.png
002-signup-form.png
003-email-verification.png
004-onboarding-step1.png
005-onboarding-step2.png
...
```

---

## Detailed Workflow

### Step 1: Prepare Your Environment

1. **Clear browser data** (optional but recommended for clean test):
   - Chrome Settings → Privacy → Clear browsing data
   - Or use Incognito mode (Ctrl+Shift+N)

2. **Open DevTools**:
   - Press F12 or Right-click → Inspect

3. **Enable Device Mode**:
   - Click the device icon in DevTools (or Ctrl+Shift+M)
   - Select "iPhone 14 Pro" from device dropdown
   - Dimensions: 390 x 844

4. **Create output folder**:
   ```
   Create: audit_screenshots/[app-name]/[date]/
   Example: audit_screenshots/juicenet/2026-01-15/
   ```

### Step 2: Capture Key Flows

#### Guest/User Flow
| # | Screen | What to Capture |
|---|--------|-----------------|
| 001 | Landing | Initial load, before any interaction |
| 002 | Signup Form | Empty form state |
| 003 | Signup Form (filled) | With sample data entered |
| 004 | Signup Form (errors) | If validation errors appear |
| 005 | Email Verification | Pending state |
| 006 | Email Received | Screenshot of actual email |
| 007 | Post-Verification | After clicking email link |
| 008 | Onboarding Step 1 | Profile info |
| 009 | Onboarding Step 2 | Additional details |
| 010 | Success/Dashboard | Final state |

#### Host Flow (if different)
| # | Screen | What to Capture |
|---|--------|-----------------|
| 020 | Host Landing | Host-specific entry |
| 021 | Host Signup | Different form if applicable |
| 022 | Host Onboarding 1 | Profile |
| 023 | Host Onboarding 2 | Listing details |
| 024 | Host Onboarding 3 | Pricing |
| 025 | Host Onboarding 4 | Payment |
| 026 | Host Success | Completion state |

### Step 3: Capture Error States

Don't forget to capture:
- [ ] Form validation errors
- [ ] API error messages
- [ ] Loading states
- [ ] Empty states
- [ ] 404/error pages

### Step 4: Capture Mobile-Specific Issues

Look for:
- [ ] Text too small to read
- [ ] Buttons too close together
- [ ] Content cut off
- [ ] Horizontal scrolling
- [ ] Keyboard overlapping inputs

---

## Screenshot Naming Convention

```
[NNN]-[flow]-[screen]-[state].png

Examples:
001-guest-landing.png
002-guest-signup-empty.png
003-guest-signup-filled.png
004-guest-signup-error.png
005-guest-verification-pending.png
010-guest-dashboard.png
020-host-landing.png
021-host-signup.png
```

---

## Alternative: Chrome Extension Method

If you have the Audit Capture extension installed:

1. Click extension icon in toolbar
2. Click "Start Recording"
3. Navigate through your app normally
4. Click "Stop Recording"
5. Export session (JSON + screenshots)

---

## Feeding Screenshots to Weaver Pro

### Method 1: Manual Analysis Request

In Weaver Pro UI:
1. Upload screenshots as a ZIP file
2. In the input field, describe what you want analyzed:
   ```
   "Analyze these screenshots of our signup flow.
   Identify UX issues, drop-off risks, and provide recommendations."
   ```

### Method 2: Structured Analysis

Create a JSON file with your screenshots:

```json
{
  "app_name": "JuiceNet",
  "audit_date": "2026-01-15",
  "screenshots": [
    {
      "filename": "001-landing.png",
      "flow": "guest",
      "step": "landing",
      "notes": "Initial load"
    },
    {
      "filename": "002-signup.png",
      "flow": "guest",
      "step": "signup",
      "notes": "Form with validation visible"
    }
  ],
  "known_issues": [
    "Users report signup is confusing",
    "High drop-off at step 3"
  ]
}
```

---

## Quick Checklist

Before starting:
- [ ] Chrome open in Incognito
- [ ] DevTools open (F12)
- [ ] Device mode enabled (390x844)
- [ ] Output folder created

During capture:
- [ ] Landing page captured
- [ ] All signup steps captured
- [ ] All onboarding steps captured
- [ ] Error states captured
- [ ] Success state captured
- [ ] Mobile issues noted

After capture:
- [ ] Screenshots organized and named
- [ ] Notes added for context
- [ ] ZIP created for upload to Weaver Pro

---

## Troubleshooting

### Can't access certain screens?
- Use test credentials provided by client
- Ask client to create a demo account
- Screen record a video and extract frames

### App requires authentication?
- Capture up to auth wall
- Ask client for staging environment access
- Use test account credentials

### Dynamic content changes?
- Capture multiple states
- Note what triggers each state
- Take video if needed

---

## Time Estimate

| App Complexity | Screens | Time |
|----------------|---------|------|
| Simple (landing + signup) | 5-10 | 10-15 min |
| Medium (full onboarding) | 15-25 | 20-30 min |
| Complex (multiple flows) | 30-50 | 45-60 min |

---

*This workflow ensures consistent, high-quality screenshots for app audits when automated crawling isn't possible.*
