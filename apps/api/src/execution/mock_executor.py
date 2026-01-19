"""
Mock Executor for local development and testing

Simulates code execution without requiring Docker or OpenHands.
"""
from typing import Dict, Optional
import asyncio
import logging

from .executor import BaseExecutor, ExecutionResult, ExecutionConfig

logger = logging.getLogger(__name__)


class MockExecutor(BaseExecutor):
    """
    Mock executor that simulates code execution.

    Useful for:
    - Local development without Docker
    - Testing the execution pipeline
    - CI environments without Docker access
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self._simulated_delay = 0.5

    async def execute_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> ExecutionResult:
        """Simulate code execution"""
        await asyncio.sleep(self._simulated_delay)

        # Check for obvious errors
        if not code.strip():
            return ExecutionResult(
                success=False,
                output="",
                error="Empty code provided",
                exit_code=1
            )

        # Simulate successful execution
        return ExecutionResult(
            success=True,
            output=self._generate_mock_output(code, language),
            execution_time=self._simulated_delay
        )

    async def execute_project(
        self,
        files: Dict[str, str],
        entry_command: str
    ) -> ExecutionResult:
        """Simulate project execution"""
        await asyncio.sleep(self._simulated_delay * 2)

        if not files:
            return ExecutionResult(
                success=False,
                output="",
                error="No files provided",
                exit_code=1
            )

        return ExecutionResult(
            success=True,
            output=f"""[MOCK] Project execution simulated
Command: {entry_command}
Files: {len(files)}

Application started successfully.
Listening on http://localhost:3000

Press Ctrl+C to stop.""",
            execution_time=self._simulated_delay * 2
        )

    async def execute_with_feedback(
        self,
        code: str,
        language: str,
        max_iterations: int = 5
    ) -> ExecutionResult:
        """Simulate execution with feedback"""
        # Just execute once - mock always succeeds
        return await self.execute_code(code, language)

    async def run_tests(
        self,
        files: Dict[str, str],
        test_command: str
    ) -> ExecutionResult:
        """Simulate test execution"""
        await asyncio.sleep(self._simulated_delay)

        test_count = sum(1 for f in files if "test" in f.lower())

        return ExecutionResult(
            success=True,
            output=f"""[MOCK] Test execution simulated
Command: {test_command}

Running {test_count} test file(s)...

PASSED: test_main.py::test_example
PASSED: test_main.py::test_another

============================
{test_count * 2} passed in 0.5s
============================""",
            execution_time=self._simulated_delay
        )

    def _generate_mock_output(self, code: str, language: str) -> str:
        """Generate realistic mock output based on language"""
        if language == "python":
            return """[MOCK Python Execution]
>>> Executing script...
Hello, World!
>>> Script completed successfully."""

        elif language in ("javascript", "typescript"):
            return """[MOCK Node.js Execution]
> Running script...
Hello, World!
> Process exited with code 0"""

        elif language == "go":
            return """[MOCK Go Execution]
go run main.go
Hello, World!"""

        elif language == "rust":
            return """[MOCK Rust Execution]
   Compiling mock v0.1.0
    Finished dev [unoptimized + debuginfo] target(s)
     Running `target/debug/mock`
Hello, World!"""

        else:
            return f"""[MOCK {language.upper()} Execution]
Execution completed successfully.
Output: Hello, World!"""
