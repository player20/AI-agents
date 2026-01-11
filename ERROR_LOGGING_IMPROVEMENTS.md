# Error Logging Improvements - Agent Execution Debugging

**Date**: 2026-01-11
**Purpose**: Add detailed error tracking to identify why agents are failing silently

## Problem Identified

When running the UX evaluation with 11 agents using "Speed (All Haiku)" model:
- **4 agents succeeded**: PM, UXResearcher, ProductDesigner, Ideas
- **7 agents failed silently**: UIDesigner, ProductOwner, TechnicalWriter, Architect, AccessibilitySpecialist, Senior, Verifier
- **No error messages** were logged explaining why they failed

## Root Cause Analysis

### Issue #1: Silent Error Suppression
```python
# OLD CODE (Line 1346)
except Exception as e:
    log_agent_message("System", f"Warning: Could not extract task outputs: {str(e)}")
```
**Problem**: Errors were caught and only logged as warnings, hiding the real issue.

### Issue #2: No Crew-Level Error Handling
```python
# OLD CODE (Line 1316)
result = crew.kickoff()  # No try/except!
```
**Problem**: If `crew.kickoff()` encountered errors, they weren't caught or logged.

### Issue #3: No Task-Level Diagnostics
**Problem**: When a task had no output, we didn't inspect why (error, timeout, etc.)

## Changes Made

### 1. Added Crew Execution Error Handling (Lines 1316-1335)

```python
log_agent_message("System", "🔍 Starting crew execution with detailed error tracking...")

try:
    result = crew.kickoff()
    log_agent_message("System", f"✅ Crew execution completed successfully")
except Exception as crew_error:
    error_type = type(crew_error).__name__
    log_agent_message("System", f"❌ CREW EXECUTION FAILED: {error_type}")
    log_agent_message("System", f"Error message: {str(crew_error)}")

    import traceback
    tb = traceback.format_exc()
    log_agent_message("System", f"Full traceback:\n{tb}")

    # Return early with error
    return f"Crew execution failed: {str(crew_error)}", {}, None
```

**Benefits**:
- ✅ Catches crew-level failures immediately
- ✅ Logs full error type and message
- ✅ Provides complete traceback for debugging
- ✅ Returns early instead of continuing with partial data

### 2. Enhanced Task Output Extraction (Lines 1337-1401)

```python
log_agent_message("System", "🔍 Extracting task outputs...")

for i, task in enumerate(tasks):
    agent_role = sorted_agents[i] if i < len(sorted_agents) else "Unknown"

    try:
        log_agent_message("System", f"📝 Processing {agent_role} (Task {i+1}/{len(tasks)})...")

        if hasattr(task, 'output') and task.output:
            # SUCCESS PATH - log output normally
            ...
        else:
            # FAILURE PATH - detailed diagnostics
            log_agent_message("System", f"⚠️  WARNING: {agent_role} task has no output!")

            # Inspect task attributes
            task_attrs = dir(task)
            log_agent_message("System", f"   Available task attributes: {[attr for attr in task_attrs if not attr.startswith('_')]}")

            # Check status
            if hasattr(task, 'status'):
                log_agent_message("System", f"   Task status: {task.status}")

            # Check for errors
            if hasattr(task, 'error') and task.error:
                log_agent_message("System", f"❌ {agent_role} FAILED with error: {task.error}")

            # Check result
            if hasattr(task, 'result'):
                log_agent_message("System", f"   Task result: {task.result}")

            # Check raw output
            if hasattr(task, 'output_raw'):
                log_agent_message("System", f"   Task output_raw: {task.output_raw}")

            # Check agent info
            if hasattr(task, 'agent'):
                agent_info = f"{task.agent.role}" if hasattr(task.agent, 'role') else "Unknown"
                log_agent_message("System", f"   Agent: {agent_info}")

    except Exception as task_error:
        error_type = type(task_error).__name__
        log_agent_message("System", f"❌ ERROR processing {agent_role}: {error_type}")
        log_agent_message("System", f"   Error message: {str(task_error)}")

        import traceback
        tb = traceback.format_exc()
        log_agent_message("System", f"   Traceback:\n{tb}")
```

**Benefits**:
- ✅ Logs processing status for each agent
- ✅ Inspects task attributes to understand state
- ✅ Checks for error messages in task object
- ✅ Logs tracebacks for extraction errors
- ✅ Provides detailed diagnostics for failed tasks

### 3. Enhanced Progress Logging

**Before**:
```
Execution completed successfully
Captured output from PM
Captured output from UXResearcher
```

**After**:
```
🔍 Starting crew execution with detailed error tracking...
✅ Crew execution completed successfully
🔍 Extracting task outputs...
📝 Processing PM (Task 1/11)...
✅ Successfully captured output from PM
📝 Processing UXResearcher (Task 2/11)...
✅ Successfully captured output from UXResearcher
📝 Processing UIDesigner (Task 3/11)...
⚠️  WARNING: UIDesigner task has no output!
   Task status: failed
❌ UIDesigner FAILED with error: Timeout waiting for response
```

## What You'll See Now

When you run the evaluation again, you'll see detailed logs like:

### Success Case:
```
📝 Processing PM (Task 1/11)...
PM output: ~1,234 tokens
✅ Successfully captured output from PM
```

### Failure Case (Example):
```
📝 Processing UIDesigner (Task 5/11)...
⚠️  WARNING: UIDesigner task has no output!
   Available task attributes: ['agent', 'description', 'error', 'output', 'result', 'status']
   Task status: failed
❌ UIDesigner FAILED with error: RateLimitError: Rate limit exceeded
   Task result: None
   Agent: UI/UX Designer
```

### Crew-Level Failure (Example):
```
🔍 Starting crew execution with detailed error tracking...
❌ CREW EXECUTION FAILED: APIConnectionError
Error message: Connection timeout after 30s
Full traceback:
  File "multi_agent_team.py", line 1322, in run_dev_team
    result = crew.kickoff()
  File "crewai/crew.py", line 456, in kickoff
    ...
```

## Next Steps

1. **Re-run the evaluation** with the same 11 agents and Haiku model
2. **Check the System logs** in Gradio for detailed error messages
3. **Look for patterns** in which agents fail and why
4. **Adjust strategy** based on findings:
   - If rate limits → slow down or reduce agents
   - If timeouts → switch to Sonnet/Opus for complex tasks
   - If prompt too long → simplify the evaluation prompt
   - If model errors → use higher quality model

## Likely Root Causes (Hypotheses)

Based on the pattern (first 4 succeeded, next 7 failed):

### Hypothesis 1: Rate Limiting
- First 4 agents completed quickly
- By agent 5 (UIDesigner), hit rate limits
- Remaining 6 agents failed due to rate limit errors

**Test**: Check logs for "RateLimitError" or "429" errors

### Hypothesis 2: Model Timeout
- Haiku is fast but has shorter timeouts
- Complex UX evaluation prompt (~5,000 tokens) overwhelmed Haiku
- Later agents timed out

**Test**: Check logs for "TimeoutError" or "Connection timeout"

### Hypothesis 3: Context Length Exceeded
- Each agent adds to context
- After 4 agents, context window exceeded
- Remaining agents failed silently

**Test**: Check if total_tokens_used approached CONTEXT_LIMIT

### Hypothesis 4: Prompt Complexity
- UX evaluation requires deep analysis
- Haiku struggles with complex reasoning
- Haiku returned empty responses (no error, just no output)

**Test**: Look for tasks with status="completed" but output=None

## Recommendations

### Short-term (Immediate)
1. **Re-run with error logging** to identify exact failure cause
2. **Use Sonnet instead of Haiku** for complex evaluation tasks
3. **Reduce agent count** to 6-8 agents max (avoid rate limits)

### Medium-term (This Week)
1. **Add retry logic** for failed tasks with exponential backoff
2. **Implement task-level timeouts** with configurable limits
3. **Add model selection hints** (warn when Haiku used for complex tasks)

### Long-term (Next Sprint)
1. **Implement batch execution** with checkpoints between batches
2. **Add cost estimation** to warn about expensive runs
3. **Create agent profiles** showing which agents work best with which models

---

## Testing the Improvements

Run this command to test the enhanced logging:

```bash
python multi_agent_team.py
```

Then select the same 11 agents with Haiku and watch for detailed error logs in the System output section.

**Expected Result**: You'll now see exactly which agent failed and why, instead of silent "failed_or_empty" statuses.
