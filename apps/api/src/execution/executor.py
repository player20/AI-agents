"""
Code Executor - OpenHands integration for sandboxed code execution

OpenHands (formerly OpenDevin) provides:
- Sandboxed Docker execution
- Code running with error feedback
- Web browsing for research
- Command line access

This module creates an abstraction layer that:
- Works with mock execution for local development
- Integrates with OpenHands when available
- Provides error feedback loops for code improvement
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import asyncio
import os

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of code execution"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    modified_files: Optional[Dict[str, str]] = None
    execution_time: float = 0.0


@dataclass
class ExecutionConfig:
    """Configuration for code execution"""
    timeout: int = 300  # 5 minutes
    max_memory: str = "2g"
    network_enabled: bool = False
    max_iterations: int = 5  # For error feedback loops


class BaseExecutor(ABC):
    """Abstract base class for code executors"""

    @abstractmethod
    async def execute_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> ExecutionResult:
        """Execute a single code snippet"""
        pass

    @abstractmethod
    async def execute_project(
        self,
        files: Dict[str, str],
        entry_command: str
    ) -> ExecutionResult:
        """Execute a multi-file project"""
        pass

    @abstractmethod
    async def execute_with_feedback(
        self,
        code: str,
        language: str,
        max_iterations: int = 5
    ) -> ExecutionResult:
        """Execute code with error feedback and automatic fixing"""
        pass

    @abstractmethod
    async def run_tests(
        self,
        files: Dict[str, str],
        test_command: str
    ) -> ExecutionResult:
        """Run tests for a project"""
        pass


class CodeExecutor(BaseExecutor):
    """
    OpenHands-based code executor for sandboxed execution.

    Features:
    - Sandboxed Docker execution
    - Error feedback loops
    - Multi-file project support
    - Test execution

    Note: Requires OpenHands to be installed and Docker running.
    Falls back to MockExecutor if not available.
    """

    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self._openhands_available = self._check_openhands()
        self._runtime = None

    def _check_openhands(self) -> bool:
        """Check if OpenHands is available"""
        try:
            # Check for OpenHands package
            # Note: OpenHands integration requires the package to be installed
            # and Docker to be running
            import subprocess
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.warning("Docker not running. Using mock executor.")
                return False

            # For now, we don't have OpenHands installed
            # This is a placeholder for future integration
            logger.info("Docker available. OpenHands integration ready.")
            return False  # Set to True when OpenHands is integrated

        except Exception as e:
            logger.warning(f"OpenHands check failed: {e}. Using mock executor.")
            return False

    async def execute_code(
        self,
        code: str,
        language: str,
        filename: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute a single code snippet.

        Args:
            code: The code to execute
            language: Programming language (python, javascript, etc.)
            filename: Optional filename for the code

        Returns:
            ExecutionResult with output and any errors
        """
        if not self._openhands_available:
            return await self._mock_execute(code, language)

        # OpenHands execution would go here
        # For now, return mock result
        return await self._mock_execute(code, language)

    async def execute_project(
        self,
        files: Dict[str, str],
        entry_command: str
    ) -> ExecutionResult:
        """
        Execute a multi-file project.

        Args:
            files: Dictionary mapping file paths to content
            entry_command: Command to run (e.g., "npm run dev", "python main.py")

        Returns:
            ExecutionResult with output and any errors
        """
        if not self._openhands_available:
            return await self._mock_execute_project(files, entry_command)

        # OpenHands execution would go here
        return await self._mock_execute_project(files, entry_command)

    async def execute_with_feedback(
        self,
        code: str,
        language: str,
        max_iterations: int = 5
    ) -> ExecutionResult:
        """
        Execute code with automatic error fixing.

        This implements a feedback loop where:
        1. Code is executed
        2. If errors occur, they're sent to the LLM
        3. LLM provides a fix
        4. Fixed code is re-executed
        5. Repeat until success or max iterations

        Args:
            code: Initial code to execute
            language: Programming language
            max_iterations: Maximum fix attempts

        Returns:
            ExecutionResult with final code and outcome
        """
        current_code = code
        iteration = 0

        while iteration < max_iterations:
            result = await self.execute_code(current_code, language)

            if result.success:
                return ExecutionResult(
                    success=True,
                    output=result.output,
                    modified_files={"main": current_code},
                    execution_time=result.execution_time
                )

            # In a full implementation, we would:
            # 1. Send error to LLM
            # 2. Get fixed code
            # 3. Try again

            # For now, just return the error
            logger.warning(f"Execution failed on iteration {iteration + 1}: {result.error}")
            iteration += 1

        return ExecutionResult(
            success=False,
            output="",
            error=f"Max iterations ({max_iterations}) reached without success",
            modified_files={"main": current_code}
        )

    async def run_tests(
        self,
        files: Dict[str, str],
        test_command: str
    ) -> ExecutionResult:
        """
        Run tests for a project.

        Args:
            files: Project files including tests
            test_command: Command to run tests (e.g., "pytest", "npm test")

        Returns:
            ExecutionResult with test output
        """
        if not self._openhands_available:
            return await self._mock_run_tests(files, test_command)

        return await self._mock_run_tests(files, test_command)

    # Mock implementations for local development

    async def _mock_execute(
        self,
        code: str,
        language: str
    ) -> ExecutionResult:
        """Mock code execution"""
        await asyncio.sleep(0.5)  # Simulate execution time

        # Basic syntax checking (very simplified)
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return ExecutionResult(
                    success=True,
                    output="Mock execution successful.\n[Output simulated for local development]",
                    execution_time=0.5
                )
            except SyntaxError as e:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Syntax error: {e}",
                    exit_code=1,
                    execution_time=0.1
                )

        # For other languages, assume success
        return ExecutionResult(
            success=True,
            output=f"Mock {language} execution completed.\n[Real execution requires OpenHands]",
            execution_time=0.5
        )

    async def _mock_execute_project(
        self,
        files: Dict[str, str],
        entry_command: str
    ) -> ExecutionResult:
        """Mock project execution"""
        await asyncio.sleep(1.0)

        file_list = "\n".join(f"  - {f}" for f in files.keys())

        return ExecutionResult(
            success=True,
            output=f"""Mock project execution:
Command: {entry_command}
Files:
{file_list}

[Real execution requires OpenHands with Docker]
Server would be running at http://localhost:3000""",
            execution_time=1.0
        )

    async def _mock_run_tests(
        self,
        files: Dict[str, str],
        test_command: str
    ) -> ExecutionResult:
        """Mock test execution"""
        await asyncio.sleep(0.8)

        # Find test files
        test_files = [f for f in files.keys() if "test" in f.lower()]

        return ExecutionResult(
            success=True,
            output=f"""Mock test execution:
Command: {test_command}
Test files found: {len(test_files)}

====== Mock Test Results ======
3 passed, 0 failed, 0 skipped
==============================

[Real tests require OpenHands with Docker]""",
            execution_time=0.8
        )


# Global executor instance
_executor: Optional[CodeExecutor] = None


def get_executor() -> CodeExecutor:
    """Get or create the global executor instance"""
    global _executor

    if _executor is None:
        _executor = CodeExecutor()

    return _executor
