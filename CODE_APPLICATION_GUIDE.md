# 🔧 Code Application Guide - Applying AI Changes to Your Codebase

## Overview

The Multi-Agent Team can now **automatically apply code changes** to your existing projects! This guide shows you how to safely apply AI-suggested modifications with full Git safety and PR creation.

---

## 🎯 How It Works

```
1. Agents analyze your code → 2. Suggest changes → 3. You approve → 4. System applies changes
                                                                    ↓
                                                    5. Creates Git branch → 6. Commits changes → 7. Opens PR
```

**Safety Features:**
- ✅ Creates a new Git branch (never modifies main directly)
- ✅ Validates repository state before changes
- ✅ Provides full rollback capability
- ✅ Creates PR for human review
- ✅ Shows complete diff of all changes

---

## 📋 Prerequisites

### 1. GitHub CLI (for PR creation)
```bash
# Install gh CLI
# Windows (using winget):
winget install GitHub.cli

# Or download from: https://cli.github.com/

# Verify installation:
gh --version

# Authenticate:
gh auth login
```

### 2. Git Repository
Your target project must be:
- ✅ A valid Git repository
- ✅ No uncommitted changes (commit or stash first)
- ✅ Connected to a GitHub remote (for PR creation)

---

## 🚀 Usage - Step by Step

The system supports TWO ways to apply changes:
1. **Local Repository**: Provide a local file path (e.g., `C:\MyProject`)
2. **GitHub Repository**: Provide a GitHub URL (e.g., `https://github.com/username/repo`)

### Method 1: Local Repository

For local projects on your machine.

### Scenario: AI Reviews and Fixes Your Code

Let's say you want AI agents to review and fix issues in your existing project.

#### Step 1: Run Code Review
```
1. Open http://127.0.0.1:7860
2. Agent Preset: "Code Review"
3. Code Review Mode: ✅ Enabled
4. Model Preset: "Quality (Critical=Opus, Rest=Sonnet)"

5. Project Description:
```
Review and fix the authentication system at C:\Users\jacob\MyProject

Files to analyze:
- src/auth/login.ts
- src/auth/signup.ts
- src/middleware/auth.ts

Find and fix:
1. Security vulnerabilities
2. Error handling gaps
3. TypeScript type issues
4. Missing validation

For each issue found, provide the COMPLETE fixed file content in code blocks like:

File: src/auth/login.ts
```typescript
// Complete fixed file content here
export function login(email: string, password: string) {
  // Fixed implementation
}
```

6. Click "▶️ Run Team"
7. Wait for agents to complete analysis
```

#### Step 2: Review Agent Suggestions

Check the **Agent Outputs** section:
- **Senior Agent**: Architecture issues and fixes
- **QA Agent**: Test gaps and recommendations
- **Verifier Agent**: Security vulnerabilities and fixes

**Look for code blocks** in the outputs that contain complete file content.

---

#### Step 3: Apply Changes to Your Repository

Once you've reviewed and approve the suggestions:

```
1. In the "Feedback / Apply Target" field, enter:
   APPLY: C:\Users\jacob\MyProject

2. In the "Action" dropdown, select:
   Approve

3. Click "▶️ Run Team" again
```

**What Happens Next:**

```
[System] Applying changes to: C:\Users\jacob\MyProject
[System] Repository validated
[System] Created and switched to branch: ai-agents/changes-20260110_143025
[System] Found 3 code suggestions
[System] ✓ Modified: src/auth/login.ts (by Senior)
[System] ✓ Modified: src/auth/signup.ts (by Verifier)
[System] ✓ Modified: src/middleware/auth.ts (by QA)
[System] Committed 3 changes
[System] Pull request created: https://github.com/you/MyProject/pull/42

✅ Successfully applied 3 changes!

Branch: ai-agents/changes-20260110_143025
Pull Request: https://github.com/you/MyProject/pull/42

Details:
Repository validated
Created and switched to branch: ai-agents/changes-20260110_143025
Found 3 code suggestions
✓ Modified: src/auth/login.ts (by Senior)
✓ Modified: src/auth/signup.ts (by Verifier)
✓ Modified: src/middleware/auth.ts (by QA)
Committed 3 changes
Pull request created: https://github.com/you/MyProject/pull/42
```

---

#### Step 4: Review the Pull Request

1. Click the PR link: `https://github.com/you/MyProject/pull/42`
2. Review all changes in the GitHub diff view
3. Check the PR description for:
   - Which agents made which changes
   - Summary of modifications
   - Review checklist

4. **If changes look good**: Merge the PR
5. **If issues found**: Add review comments, then:
   - Use "Reject and Rerun" in the system
   - Provide feedback about what to fix
   - Run again to get improved suggestions

---

### Method 2: GitHub Repository

For analyzing and fixing public GitHub repositories directly.

#### Step 1: Provide GitHub URL

```
1. Open http://127.0.0.1:7860
2. Agent Preset: "Code Review"
3. Code Review Mode: ✅ Enabled
4. Model Preset: "Quality (Critical=Opus, Rest=Sonnet)"

5. GitHub Repository URL field:
   https://github.com/username/repository

6. Project Description:
```
Review the authentication system in this repository.

Find and fix:
1. Security vulnerabilities
2. Error handling gaps
3. TypeScript type issues

For each issue found, provide the COMPLETE fixed file content in code blocks.
```

7. Click "▶️ Run Team"
```

**What Happens:**
- System clones the GitHub repository to a temporary directory
- Agents analyze the code from the cloned repository
- Suggestions are generated based on the actual code

---

#### Step 2: Review Agent Suggestions

Same as Method 1 - check the agent outputs for code blocks with fixes.

---

#### Step 3: Apply Changes (Two Options)

**Option A: Using Feedback Field**
```
1. In the "Feedback / Apply Target" field, enter:
   APPLY: https://github.com/username/repository

2. In the "Action" dropdown, select:
   Approve

3. Click "▶️ Run Team" again
```

**Option B: Automatic Application**
If you provided the GitHub URL in Step 1 and select "Approve", the system will automatically apply changes to that repository.

**What Happens Next:**

```
[System] Applying changes to GitHub repository: https://github.com/username/repository
[System] Cloned https://github.com/username/repository to /tmp/ai-agents-abc123
[System] Repository validated
[System] Created and switched to branch: ai-agents/changes-20260110_143025
[System] Found 3 code suggestions
[System] ✓ Modified: src/auth/login.ts (by Senior)
[System] ✓ Modified: src/auth/signup.ts (by Verifier)
[System] ✓ Modified: src/middleware/auth.ts (by QA)
[System] Committed 3 changes
[System] Pull request created: https://github.com/username/repository/pull/42
[System] Cleaned up temporary directory: /tmp/ai-agents-abc123

✅ Successfully applied 3 changes!

Branch: ai-agents/changes-20260110_143025
Pull Request: https://github.com/username/repository/pull/42
```

**Key Differences from Local Method:**
- Repository is cloned to a temporary directory
- Temporary directory is automatically cleaned up after PR creation
- You don't need local access to the repository
- Works with any public GitHub repository

---

#### Step 4: Review the Pull Request

Same as Method 1 - review and merge the PR on GitHub.

---

## 🎨 Advanced Usage

### Custom Branch Names

By default, branches are named: `ai-agents/changes-TIMESTAMP`

To use a custom name, modify `code_applicator.py:60`:
```python
branch_name = "feature/ai-security-fixes"  # Your custom name
```

### Skip PR Creation (Direct Commit)

If you want to commit directly without creating a PR:

Modify the apply workflow in `multi_agent_team.py:804-811`:
```python
apply_result = apply_agent_changes_workflow(
    agent_outputs=outputs,
    target_repo_path=target_repo,
    create_branch=True,
    create_pr=False,  # ← Change this to False
    auto_commit=True,
    create_new_files=False
)
```

### Allow Creating New Files

By default, the system only modifies existing files. To allow creating new files:

```python
apply_result = apply_agent_changes_workflow(
    agent_outputs=outputs,
    target_repo_path=target_repo,
    create_branch=True,
    create_pr=True,
    auto_commit=True,
    create_new_files=True  # ← Change this to True
)
```

---

## 📝 Code Block Format Requirements

For the system to correctly parse and apply code changes, agents must format their suggestions like this:

### ✅ Correct Format
```
File: src/utils/validation.ts
```typescript
export function validateEmail(email: string): boolean {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}
```
\```

### ✅ Alternative Format
```
Path: src/utils/validation.ts
```typescript
// Code here
```
\```

### ✅ Inline Reference
```
Update `src/utils/validation.ts`:
```typescript
// Code here
```
\```

### ❌ Incorrect Format (Won't Work)
```
Here's the fixed code:
```typescript
// No file path specified!
```
\```

**Key Requirements:**
1. File path must appear **before** the code block
2. Formats: `File:`, `Path:`, or backticks around filename
3. Code block must have language specified (```typescript, ```python, etc.)
4. Provide **complete file content**, not just snippets

---

## 🛡️ Safety & Rollback

### What If Changes Are Wrong?

**Option 1: Don't Merge the PR**
- Simply close the PR on GitHub
- Delete the branch: `git branch -D ai-agents/changes-TIMESTAMP`

**Option 2: Revert the Branch**
```bash
# Switch to the AI branch
git checkout ai-agents/changes-20260110_143025

# See what changed
git diff main

# If you don't like it, switch back and delete
git checkout main
git branch -D ai-agents/changes-20260110_143025
```

**Option 3: Emergency Rollback**

If you already merged and need to undo:
```bash
# Revert the merge commit
git revert -m 1 HEAD

# Or hard reset (DANGEROUS - loses changes)
git reset --hard HEAD~1
```

---

## 🔍 Troubleshooting

### Error: "Repository has uncommitted changes"

**Problem**: Your repo has uncommitted changes

**Solution**:
```bash
# Option 1: Commit them
git add .
git commit -m "WIP: before AI changes"

# Option 2: Stash them
git stash

# Then try again
```

---

### Error: "GitHub CLI (gh) not found"

**Problem**: `gh` CLI not installed

**Solution**:
```bash
# Install gh CLI
winget install GitHub.cli

# Authenticate
gh auth login

# Try again
```

---

### Error: "No code changes to apply"

**Problem**: Agents didn't provide code blocks in the correct format

**Solution**:
1. Check agent outputs for code blocks
2. Ensure code blocks have file paths specified
3. Use custom prompts to explicitly request:
   ```
   For each file that needs changes, provide the COMPLETE file content in a code block with the file path like:

   File: path/to/file.ts
   ```typescript
   // complete file content
   ```
   \```

---

### Error: "Failed to create PR"

**Problem**: Not authenticated with GitHub or repo has no remote

**Solution**:
```bash
# Check remote
git remote -v

# If no remote, add one
git remote add origin https://github.com/you/repo.git

# Authenticate with gh
gh auth login

# Try again
```

---

## 📊 Example Workflows

### Workflow 1: Security Audit + Auto-Fix

```
1. Preset: "Security Audit"
2. Code Review Mode: ✅ Enabled
3. Model: "Premium (All Opus)"
4. Description:
   "Audit C:\Projects\MyApp for OWASP Top 10 vulnerabilities.
   Provide fixed code for each issue found."

5. Run → Review findings
6. Feedback: "APPLY: C:\Projects\MyApp"
7. Action: "Approve"
8. Run → Check PR
```

**Result**: Comprehensive security fixes in a reviewable PR

---

### Workflow 2: Refactor Legacy Code

```
1. Preset: "Architecture Review"
2. Code Review Mode: ✅ Enabled
3. Model: "Quality"
4. Description:
   "Refactor C:\OldProject\legacy.js to modern TypeScript.
   Split into modules, add types, fix patterns."

5. Run → Review refactoring plan
6. Feedback: "APPLY: C:\OldProject"
7. Action: "Approve"
8. Run → Check PR
```

**Result**: Modernized codebase in a reviewable PR

---

### Workflow 3: Add Test Coverage

```
1. Preset: Custom (PM, QA, Verifier)
2. Code Review Mode: ✅ Enabled
3. Model: "Balanced"
4. Description:
   "Add comprehensive tests for C:\API\routes\users.ts
   Include unit tests, integration tests, edge cases."

5. Run → Review test strategy
6. Custom prompt for QA:
   "Create complete test files at tests/routes/users.test.ts
   with all test cases. Provide full file content."

7. Feedback: "APPLY: C:\API"
8. Action: "Approve"
9. Run → Check PR (may create new test files if allowed)
```

**Result**: Complete test suite added to project

---

## 🎯 Best Practices

### 1. **Always Review Before Merging**
Never blindly merge AI-generated PRs. Review:
- Code correctness
- Security implications
- Breaking changes
- Test coverage

### 2. **Use Quality Models for Important Changes**
- Security fixes: Premium preset
- Refactoring: Quality preset
- Documentation: Balanced preset

### 3. **Be Specific in Prompts**
```
❌ Bad: "Fix the code"
✅ Good: "Fix the authentication code in src/auth/login.ts by:
         1. Adding input validation
         2. Improving error handling
         3. Adding rate limiting
         Provide complete fixed file content."
```

### 4. **Start with Small Changes**
- First run: Single file
- Review carefully
- If good, expand to more files

### 5. **Use Branches for Experimentation**
The AI creates branches automatically - use them!
- Try different approaches
- Compare branches
- Merge the best one

### 6. **Export Results for Records**
Always enable auto-export to keep a record of:
- What AI suggested
- What was actually applied
- When it happened

---

## 🔐 Security Considerations

### Never Auto-Apply to Production

**❌ DON'T:**
```
APPLY: /var/www/production
```

**✅ DO:**
```
APPLY: C:\Dev\MyProject  # Local dev copy
# Review PR → Test locally → Then deploy
```

### Review These Areas Carefully

When AI modifies:
1. **Authentication code** - Verify no security regressions
2. **Database queries** - Check for SQL injection
3. **API endpoints** - Ensure validation intact
4. **Environment variables** - No secrets exposed
5. **Dependencies** - No malicious packages added

### Secrets and Credentials

The system **should not** expose secrets, but double-check:
- API keys not in code
- Passwords not hardcoded
- Connection strings not exposed

---

## 📚 Related Documentation

- **[README_ENHANCED.md](README_ENHANCED.md)** - Main documentation
- **[QUICK_START.md](QUICK_START.md)** - Getting started
- **[MODEL_SELECTION_GUIDE.md](MODEL_SELECTION_GUIDE.md)** - Model presets
- **[RATE_LIMITS.md](RATE_LIMITS.md)** - API compliance

---

## 🎉 Summary

**The Multi-Agent Team can now:**
- ✅ Automatically parse code suggestions from agent outputs
- ✅ Create safe Git branches for changes
- ✅ Apply changes to existing files
- ✅ Commit with detailed messages
- ✅ Create GitHub PRs for review
- ✅ Provide full rollback capability

**Usage:**
```
1. Run agents with Code Review Mode
2. Review suggestions
3. In feedback field: "APPLY: /path/to/repo"
4. Select "Approve"
5. Review and merge the PR
```

**Safety:**
- Never modifies main branch directly
- Always creates PR for review
- Full Git history preserved
- Easy rollback if needed

**The system is production-ready for safe, reviewable code modifications!** 🚀

---

**Version**: 1.0
**Last Updated**: January 2026
**Status**: Production Ready ✅
