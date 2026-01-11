# Graphviz Setup Guide

Workflow visualization requires both the Python `graphviz` package and Graphviz system binaries.

## Installation Steps

### 1. Install Python Package

```bash
pip install graphviz
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Install Graphviz System Binaries

#### Windows

**Option A: Download Installer (Recommended)**

1. Download Graphviz installer from: https://graphviz.org/download/
2. Choose "Windows" → "Stable Windows Install packages"
3. Download the `.msi` installer (e.g., `graphviz-9.0.0-win64.msi`)
4. Run the installer
5. **Important:** Check "Add Graphviz to PATH" during installation
6. Restart your terminal/IDE

**Option B: Using Chocolatey**

```powershell
choco install graphviz
```

**Option C: Using Winget**

```powershell
winget install graphviz
```

**Verify Installation:**

```bash
dot -V
```

Expected output: `dot - graphviz version X.X.X`

#### macOS

```bash
brew install graphviz
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get install graphviz
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install graphviz
```

### 3. Verify Python Integration

```python
python -c "import graphviz; print('Graphviz Python package:', graphviz.__version__)"
```

## Troubleshooting

### Issue: "Graphviz executables not found"

**Cause:** Graphviz binaries are not in your system PATH.

**Solution:**

1. Find your Graphviz installation directory (usually `C:\Program Files\Graphviz` on Windows)
2. Add the `bin` folder to your PATH:
   - Windows: `C:\Program Files\Graphviz\bin`
   - Add via System Environment Variables or in terminal:
     ```powershell
     $env:PATH += ";C:\Program Files\Graphviz\bin"
     ```
3. Restart your terminal/IDE

### Issue: "dot command not found"

**Cause:** Graphviz binaries not installed or not in PATH.

**Solution:** Follow installation steps above and ensure Graphviz is added to PATH.

### Issue: Workflow visualization shows warning message

**Cause:** Either Python package or system binaries are missing.

**Solution:**
1. Check Python package: `pip show graphviz`
2. Check system binaries: `dot -V`
3. Install whichever is missing

## Features Enabled by Graphviz

Once installed, you'll get:

- ✅ **Visual workflow diagrams** after YAML import
- ✅ **Agent connection visualization** (shows data flow)
- ✅ **Execution status colors** (pending, running, completed, failed)
- ✅ **SVG rendering** (high-quality, scalable graphics)

## Without Graphviz

The platform will still work without Graphviz, but you'll see:
- ⚠️ Warning message: "Workflow visualization not available"
- ✅ All other features work normally (YAML import, agent execution, exports)

## Testing Your Setup

1. Start the Gradio Platform:
   ```bash
   python multi_agent_team.py
   ```

2. Import a YAML workflow (e.g., `sample-workflow-test.yaml`)

3. If Graphviz is correctly installed, you'll see:
   - 📊 Workflow Visualization section with colorful graph
   - Status legend (Pending, Running, Completed, Failed)

4. If Graphviz is missing, you'll see:
   - ⚠️ Warning message with installation instructions

## Alternative: Manual DOT File Generation

If you can't install Graphviz, you can generate DOT files and visualize them online:

1. Create a `.dot` file manually with your workflow structure
2. Use online visualizers:
   - https://dreampuf.github.io/GraphvizOnline/
   - http://www.webgraphviz.com/

## Support

If you encounter issues:
1. Check Graphviz version: `dot -V` (requires 2.30+)
2. Check Python version: `python --version` (requires 3.8+)
3. Verify PATH includes Graphviz bin folder
4. Restart terminal/IDE after installation
5. Open an issue on GitHub with error details
