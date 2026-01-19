# Audit Tools Suite

A comprehensive toolkit for running professional UX/performance audits and generating client-ready deliverables.

## What Clients Want

From a client perspective:
1. **Visual proof** - See exactly what will change BEFORE development
2. **Business impact** - How issues affect their bottom line
3. **No surprises** - Preview all changes before work starts
4. **Professional deliverables** - PDFs and interactive demos they can share

These tools are designed with the client experience in mind.

---

## Tools Overview

| Tool | Purpose | Output |
|------|---------|--------|
| `lighthouse_batch.py` | Run Lighthouse on multiple URLs | HTML/JSON performance report |
| `tech_scanner.py` | Detect competitor tech stacks | HTML comparison report |
| `accessibility_audit.py` | WCAG accessibility testing | HTML/JSON a11y report |
| `report_generator.py` | Combine data into client report | Professional HTML report |
| `prototype_generator.py` | Create before/after visualizations | Interactive HTML prototype |
| Chrome Extension | Capture app flows manually | Screenshots + JSON session |

---

## Quick Start

### 1. Lighthouse Batch Audit
```bash
# Single URL
python lighthouse_batch.py --url https://example.com --output report.html

# Multiple URLs from file
python lighthouse_batch.py --urls urls.txt --output report.html

# From sitemap
python lighthouse_batch.py --sitemap https://example.com/sitemap.xml --output report.html
```

### 2. Tech Stack Scanner
```bash
# Scan competitors
python tech_scanner.py --urls competitors.txt --output tech_report.html

# Single URL
python tech_scanner.py --url https://competitor.com --output tech_report.html
```

### 3. Accessibility Audit
```bash
# Requires: pip install playwright && playwright install

python accessibility_audit.py --url https://example.com --output a11y_report.html
```

### 4. Generate Client Report
```bash
python report_generator.py \
    --client "Acme Corp" \
    --app "JuiceNet" \
    --url "https://juicenet.app" \
    --lighthouse lighthouse_report.json \
    --screenshots ./screenshots \
    --output client_report.html
```

### 5. Before/After Prototype (MOST IMPORTANT)
```bash
# Generate a template config
python prototype_generator.py --template --output my_prototype.json

# Edit my_prototype.json with your screens...

# Generate the prototype
python prototype_generator.py --config my_prototype.json --output prototype.html
```

---

## Complete Audit Workflow

### Step 1: Gather Client Information
Use the intake template: `../templates/CLIENT_AUDIT_INTAKE.md`

### Step 2: Run Automated Scans
```bash
# Performance
python lighthouse_batch.py --url https://client-app.com --output lh.json --format json

# Accessibility
python accessibility_audit.py --url https://client-app.com --output a11y.json --format json

# Tech stack
python tech_scanner.py --url https://client-app.com --output tech.json --format json
```

### Step 3: Manual Screen Capture (if needed)
1. Install the Chrome Extension from `../audit-capture-extension/`
2. Navigate through the app manually
3. Click screenshots at each screen
4. Export session data

### Step 4: Create Before/After Prototype
```bash
# Create config
python prototype_generator.py --template --output client_prototype.json

# Add your screens, before/after descriptions, and screenshots
# Then generate:
python prototype_generator.py --config client_prototype.json --output prototype.html
```

### Step 5: Generate Final Report
```bash
python report_generator.py \
    --client "Client Name" \
    --app "App Name" \
    --url "https://app.com" \
    --lighthouse lh.json \
    --screenshots ./screenshots \
    --output final_report.html
```

### Step 6: Deliver to Client
- `prototype.html` - Interactive before/after preview (MOST IMPORTANT)
- `final_report.html` - Detailed findings and recommendations
- `a11y_report.html` - Accessibility compliance status
- Screenshots folder - All captured screens

---

## Prototype Configuration Format

```json
{
    "app_name": "ClientApp",
    "client_name": "Client Company",
    "screens": [
        {
            "id": "unique-id",
            "name": "Screen Name",
            "before": {
                "description": "What's wrong with current design",
                "screenshot": "path/to/before.png",
                "issues": [
                    "Issue 1",
                    "Issue 2"
                ]
            },
            "after": {
                "description": "What we're proposing",
                "screenshot": "path/to/after.png",
                "changes": [
                    "Change 1",
                    "Change 2"
                ]
            }
        }
    ]
}
```

You can use:
- `screenshot`: Path to image file
- `html`: Inline HTML mockup (useful for quick prototypes)
- Just `description`: Text-only placeholder

---

## Chrome Extension Installation

1. Open Chrome → Extensions → Developer mode ON
2. Click "Load unpacked"
3. Select `../audit-capture-extension/` folder
4. Click extension icon to start recording

Features:
- Start/Stop recording
- Auto-capture on navigation
- Track clicks and form interactions
- Export session + screenshots

---

## Tips for Client Presentations

### The Before/After Prototype is KEY
- Clients want to SEE changes before development
- Visual comparison builds confidence
- Reduces revision cycles
- Justifies investment

### Focus on Business Impact
- Don't just list technical issues
- Explain how each issue affects revenue/users
- Use metrics: "40% of users drop off here"

### Prioritize Recommendations
- Critical: Fix immediately (blocking users)
- High: Fix soon (hurting conversions)
- Medium: Nice to have
- Low: Polish items

### Keep Reports Professional
- Use client's branding colors if possible
- Include executive summary on first page
- Keep technical details in appendix

---

## Dependencies

```bash
pip install aiohttp playwright
playwright install  # Downloads browser binaries
```

For Lighthouse:
```bash
npm install -g lighthouse
```

---

## File Structure

```
audit-tools/
├── lighthouse_batch.py      # Lighthouse multi-URL runner
├── tech_scanner.py          # Competitor tech detection
├── accessibility_audit.py   # WCAG compliance checker
├── report_generator.py      # Client report builder
├── prototype_generator.py   # Before/after prototype maker
├── sample_prototype_config.json  # Example prototype config
├── README.md               # This file
└── client_portal_template.html   # Portal HTML template

audit-capture-extension/
├── manifest.json
├── popup.html
├── popup.js
├── content.js
└── background.js

templates/
├── CLIENT_AUDIT_INTAKE.md
├── client_metrics_template.csv
└── MANUAL_SCREENSHOT_WORKFLOW.md
```

---

## Pricing Tiers (For Your Audit Service)

| Package | Price | Includes |
|---------|-------|----------|
| Basic | $499 | Lighthouse + A11y audit + recommendations |
| Standard | $999 | Basic + Before/After prototype + tech analysis |
| Premium | $1,999 | Standard + implementation support + follow-up |

---

## Remember

**"If I'm the client, I want to see what is going to be changed BEFORE the changes are made."**

The Before/After Prototype Generator is the most valuable tool. Use it for every client engagement.
