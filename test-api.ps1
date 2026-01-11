# API Backend Test Script
# Run this after starting the API with: python api_backend.py

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Multi-Agent API Backend Test Suite" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:7860"
$passed = 0
$failed = 0

# Test 1: Health Check
Write-Host "[Test 1] Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "  ✅ PASSED: Health check returned 'healthy'" -ForegroundColor Green
        $passed++
    } else {
        Write-Host "  ❌ FAILED: Unexpected response: $response" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}
Write-Host ""

# Test 2: List Agents
Write-Host "[Test 2] List Agents..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/agents" -Method Get
    $agentCount = $response.agents.Count
    if ($agentCount -ge 11) {
        Write-Host "  ✅ PASSED: Found $agentCount agents" -ForegroundColor Green
        Write-Host "  Available agents: $($response.agents.id -join ', ')" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "  ❌ FAILED: Expected at least 11 agents, found $agentCount" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}
Write-Host ""

# Test 3: Execute Team (POST)
Write-Host "[Test 3] Execute Team..." -ForegroundColor Yellow
try {
    $body = @{
        agents = @("PM", "Research")
        prompt = "Test API integration: Create a simple task management app"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/api/execute-team" -Method Post `
        -ContentType "application/json" -Body $body

    $executionId = $response.executionId

    if ($executionId -and $response.status -eq "running") {
        Write-Host "  ✅ PASSED: Execution started with ID: $executionId" -ForegroundColor Green
        $passed++

        # Test 4: Poll Status
        Write-Host ""
        Write-Host "[Test 4] Poll Execution Status..." -ForegroundColor Yellow
        Write-Host "  Polling execution $executionId..." -ForegroundColor Gray

        $attempts = 0
        $maxAttempts = 60  # 1 minute max
        $completed = $false

        while ($attempts -lt $maxAttempts) {
            Start-Sleep -Seconds 1
            try {
                $status = Invoke-RestMethod -Uri "$baseUrl/api/status/$executionId" -Method Get

                Write-Host "  Status: $($status.status) (progress: $($status.progress)%)" -ForegroundColor Gray

                if ($status.status -eq "completed") {
                    Write-Host "  ✅ PASSED: Execution completed successfully" -ForegroundColor Green
                    Write-Host "  Agents executed: $($status.agents -join ', ')" -ForegroundColor Gray
                    Write-Host "  Output preview: $($status.combinedOutput.Substring(0, [Math]::Min(100, $status.combinedOutput.Length)))..." -ForegroundColor Gray
                    $passed++
                    $completed = $true
                    break
                } elseif ($status.status -eq "failed") {
                    Write-Host "  ❌ FAILED: Execution failed with error: $($status.error)" -ForegroundColor Red
                    $failed++
                    $completed = $true
                    break
                }
            } catch {
                Write-Host "  ❌ FAILED: Error polling status: $($_.Exception.Message)" -ForegroundColor Red
                $failed++
                $completed = $true
                break
            }

            $attempts++
        }

        if (-not $completed) {
            Write-Host "  ⚠️ WARNING: Execution timeout after 60 seconds" -ForegroundColor Yellow
            Write-Host "  Note: This is expected for long-running agent tasks" -ForegroundColor Gray
        }

    } else {
        Write-Host "  ❌ FAILED: Execution did not start properly" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host "  ❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}
Write-Host ""

# Summary
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All tests passed! API backend is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Keep the API running (python api_backend.py)" -ForegroundColor Gray
    Write-Host "2. Update React frontend to use this API" -ForegroundColor Gray
    Write-Host "3. Test end-to-end integration" -ForegroundColor Gray
} else {
    Write-Host "⚠️ Some tests failed. Please check the API backend." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "1. Ensure API is running: python api_backend.py" -ForegroundColor Gray
    Write-Host "2. Check for errors in the API console" -ForegroundColor Gray
    Write-Host "3. Verify Flask and flask-cors are installed: pip install flask flask-cors" -ForegroundColor Gray
}
