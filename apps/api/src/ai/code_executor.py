"""
Code Execution Sandbox Module

Provides safe, isolated execution of generated code with feedback loops.
This is the critical missing piece that turns "code that looks right"
into "code that actually works".

Features:
- Docker-based sandboxed execution
- Multi-language support (Python, Node.js, Go, Rust)
- Timeout and resource limits
- Output capture (stdout, stderr, return values)
- Error feedback for iterative fixing
- File system isolation
"""

from typing import Optional, List, Dict, Any, Union, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import tempfile
import asyncio
import shutil
import json
import os
import logging
import time
import hashlib

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution result status"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    IMPORT_ERROR = "import_error"
    RESOURCE_LIMIT = "resource_limit"


class Language(str, Enum):
    """Supported execution languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    BASH = "bash"


@dataclass
class ExecutionResult:
    """Result of code execution"""
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    return_value: Optional[Any] = None
    exit_code: int = 0
    execution_time_ms: float = 0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_line: Optional[int] = None
    error_traceback: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_value": self.return_value,
            "exit_code": self.exit_code,
            "execution_time_ms": self.execution_time_ms,
            "error": {
                "type": self.error_type,
                "message": self.error_message,
                "line": self.error_line,
                "traceback": self.error_traceback
            } if self.error_type else None
        }

    def get_feedback(self) -> str:
        """Get human-readable feedback for the LLM to fix issues"""
        if self.is_success:
            return f"Code executed successfully.\nOutput: {self.stdout[:1000]}"

        feedback = f"Execution failed with {self.status.value}.\n"

        if self.error_type:
            feedback += f"Error type: {self.error_type}\n"
        if self.error_message:
            feedback += f"Error message: {self.error_message}\n"
        if self.error_line:
            feedback += f"Error on line: {self.error_line}\n"
        if self.error_traceback:
            feedback += f"Traceback:\n{self.error_traceback[-2000:]}\n"
        if self.stderr:
            feedback += f"Stderr:\n{self.stderr[-1000:]}\n"

        return feedback


@dataclass
class ExecutionConfig:
    """Configuration for code execution"""
    timeout_seconds: int = 30
    max_memory_mb: int = 512
    max_output_size: int = 100000  # 100KB
    allow_network: bool = False
    allow_file_write: bool = True
    working_dir: Optional[str] = None
    environment: Dict[str, str] = field(default_factory=dict)
    install_dependencies: bool = True


class CodeExecutor:
    """
    Safe code execution sandbox.

    Example:
        executor = CodeExecutor()

        # Execute Python code
        result = await executor.execute('''
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)

        print(fibonacci(10))
        ''', Language.PYTHON)

        if result.is_success:
            print(f"Output: {result.stdout}")
        else:
            print(f"Error: {result.get_feedback()}")

        # Execute with feedback loop
        fixed_code = await executor.execute_with_retry(
            code=buggy_code,
            language=Language.PYTHON,
            fix_callback=llm_fix_function
        )
    """

    # Docker images for each language
    DOCKER_IMAGES = {
        Language.PYTHON: "python:3.11-slim",
        Language.JAVASCRIPT: "node:20-slim",
        Language.TYPESCRIPT: "node:20-slim",
        Language.GO: "golang:1.22-alpine",
        Language.RUST: "rust:1.77-slim",
        Language.BASH: "alpine:3.19",
    }

    # File extensions for each language
    EXTENSIONS = {
        Language.PYTHON: ".py",
        Language.JAVASCRIPT: ".js",
        Language.TYPESCRIPT: ".ts",
        Language.GO: ".go",
        Language.RUST: ".rs",
        Language.BASH: ".sh",
    }

    def __init__(self, use_docker: bool = True):
        self.use_docker = use_docker and self._check_docker()
        if not self.use_docker:
            logger.warning("Docker not available, using local execution (less safe)")

    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    async def execute(
        self,
        code: str,
        language: Language,
        config: Optional[ExecutionConfig] = None,
        files: Optional[Dict[str, str]] = None
    ) -> ExecutionResult:
        """
        Execute code in a sandbox.

        Args:
            code: Code to execute
            language: Programming language
            config: Execution configuration
            files: Additional files to include {filename: content}

        Returns:
            ExecutionResult with output and any errors
        """
        config = config or ExecutionConfig()
        start_time = time.time()

        try:
            if self.use_docker:
                result = await self._execute_docker(code, language, config, files)
            else:
                result = await self._execute_local(code, language, config, files)

            result.execution_time_ms = (time.time() - start_time) * 1000
            return result

        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error_type="TimeoutError",
                error_message=f"Execution exceeded {config.timeout_seconds} seconds",
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    async def execute_with_retry(
        self,
        code: str,
        language: Language,
        fix_callback: Callable[[str, ExecutionResult], Awaitable[str]],
        max_retries: int = 5,
        config: Optional[ExecutionConfig] = None
    ) -> tuple:
        """
        Execute code with automatic retry and fixing.

        Args:
            code: Initial code to execute
            language: Programming language
            fix_callback: Async function that takes (code, error_result) and returns fixed code
            max_retries: Maximum fix attempts
            config: Execution configuration

        Returns:
            Tuple of (final_code, final_result, iterations)
        """
        current_code = code
        iterations = []

        for i in range(max_retries):
            result = await self.execute(current_code, language, config)
            iterations.append({
                "attempt": i + 1,
                "code_hash": hashlib.md5(current_code.encode()).hexdigest()[:8],
                "status": result.status.value,
                "error": result.error_message
            })

            if result.is_success:
                return current_code, result, iterations

            # Try to fix the code
            try:
                fixed_code = await fix_callback(current_code, result)
                if fixed_code == current_code:
                    # No changes made, stop retrying
                    break
                current_code = fixed_code
            except Exception as e:
                logger.error(f"Fix callback failed: {e}")
                break

        # Return last result even if failed
        return current_code, result, iterations

    async def _execute_docker(
        self,
        code: str,
        language: Language,
        config: ExecutionConfig,
        files: Optional[Dict[str, str]]
    ) -> ExecutionResult:
        """Execute code in Docker container"""
        image = self.DOCKER_IMAGES[language]
        ext = self.EXTENSIONS[language]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write main code file
            main_file = os.path.join(tmpdir, f"main{ext}")
            with open(main_file, 'w') as f:
                f.write(code)

            # Write additional files
            if files:
                for filename, content in files.items():
                    filepath = os.path.join(tmpdir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'w') as f:
                        f.write(content)

            # Build Docker command
            cmd = self._build_docker_command(language, config, tmpdir)

            # Run container
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.timeout_seconds
                )

                stdout_str = stdout.decode('utf-8', errors='replace')[:config.max_output_size]
                stderr_str = stderr.decode('utf-8', errors='replace')[:config.max_output_size]

                return self._parse_result(
                    proc.returncode or 0,
                    stdout_str,
                    stderr_str,
                    language
                )

            except asyncio.TimeoutError:
                # Kill the container
                proc.kill()
                raise

    def _build_docker_command(
        self,
        language: Language,
        config: ExecutionConfig,
        tmpdir: str
    ) -> List[str]:
        """Build Docker run command"""
        cmd = [
            "docker", "run",
            "--rm",  # Remove container after execution
            f"--memory={config.max_memory_mb}m",
            f"--cpus=1",
            "-v", f"{tmpdir}:/app",
            "-w", "/app",
        ]

        # Network isolation
        if not config.allow_network:
            cmd.append("--network=none")

        # Read-only filesystem (except /app and /tmp)
        if not config.allow_file_write:
            cmd.extend(["--read-only", "--tmpfs=/tmp"])

        # Add environment variables
        for key, value in config.environment.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add image
        cmd.append(self.DOCKER_IMAGES[language])

        # Add execution command based on language
        if language == Language.PYTHON:
            cmd.extend(["python", "main.py"])
        elif language == Language.JAVASCRIPT:
            cmd.extend(["node", "main.js"])
        elif language == Language.TYPESCRIPT:
            # Install ts-node if needed, then run
            cmd.extend(["sh", "-c", "npx -y ts-node main.ts"])
        elif language == Language.GO:
            cmd.extend(["go", "run", "main.go"])
        elif language == Language.RUST:
            cmd.extend(["sh", "-c", "rustc main.rs -o main && ./main"])
        elif language == Language.BASH:
            cmd.extend(["sh", "main.sh"])

        return cmd

    async def _execute_local(
        self,
        code: str,
        language: Language,
        config: ExecutionConfig,
        files: Optional[Dict[str, str]]
    ) -> ExecutionResult:
        """Execute code locally (fallback when Docker unavailable)"""
        ext = self.EXTENSIONS[language]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write main code file
            main_file = os.path.join(tmpdir, f"main{ext}")
            with open(main_file, 'w') as f:
                f.write(code)

            # Write additional files
            if files:
                for filename, content in files.items():
                    filepath = os.path.join(tmpdir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'w') as f:
                        f.write(content)

            # Build command based on language
            cmd = self._build_local_command(language, main_file)

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=tmpdir
                )

                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.timeout_seconds
                )

                stdout_str = stdout.decode('utf-8', errors='replace')[:config.max_output_size]
                stderr_str = stderr.decode('utf-8', errors='replace')[:config.max_output_size]

                return self._parse_result(
                    proc.returncode or 0,
                    stdout_str,
                    stderr_str,
                    language
                )

            except asyncio.TimeoutError:
                proc.kill()
                raise

    def _build_local_command(self, language: Language, main_file: str) -> List[str]:
        """Build local execution command"""
        if language == Language.PYTHON:
            return ["python", main_file]
        elif language == Language.JAVASCRIPT:
            return ["node", main_file]
        elif language == Language.TYPESCRIPT:
            return ["npx", "ts-node", main_file]
        elif language == Language.GO:
            return ["go", "run", main_file]
        elif language == Language.BASH:
            return ["bash", main_file]
        else:
            raise ValueError(f"Unsupported language for local execution: {language}")

    def _parse_result(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        language: Language
    ) -> ExecutionResult:
        """Parse execution output into structured result"""
        if exit_code == 0 and not stderr:
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code
            )

        # Parse error details based on language
        error_info = self._parse_error(stderr, language)

        # Determine status based on error type
        status = ExecutionStatus.RUNTIME_ERROR
        if error_info.get("type") == "SyntaxError":
            status = ExecutionStatus.SYNTAX_ERROR
        elif error_info.get("type") in ("ImportError", "ModuleNotFoundError"):
            status = ExecutionStatus.IMPORT_ERROR

        return ExecutionResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            error_type=error_info.get("type"),
            error_message=error_info.get("message"),
            error_line=error_info.get("line"),
            error_traceback=error_info.get("traceback")
        )

    def _parse_error(self, stderr: str, language: Language) -> Dict[str, Any]:
        """Parse error output for specific language"""
        import re

        error_info = {
            "type": None,
            "message": None,
            "line": None,
            "traceback": stderr
        }

        if language == Language.PYTHON:
            # Python error format: "ErrorType: message"
            # Line format: "  File "...", line X"
            error_match = re.search(r'(\w+Error|\w+Exception): (.+)$', stderr, re.MULTILINE)
            if error_match:
                error_info["type"] = error_match.group(1)
                error_info["message"] = error_match.group(2)

            line_match = re.search(r'File "[^"]+", line (\d+)', stderr)
            if line_match:
                error_info["line"] = int(line_match.group(1))

        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            # Node.js error format varies
            error_match = re.search(r'(\w+Error): (.+)$', stderr, re.MULTILINE)
            if error_match:
                error_info["type"] = error_match.group(1)
                error_info["message"] = error_match.group(2)

            line_match = re.search(r':(\d+):\d+', stderr)
            if line_match:
                error_info["line"] = int(line_match.group(1))

        elif language == Language.GO:
            # Go error format: "./main.go:X:Y: error message"
            error_match = re.search(r'\.go:(\d+):\d+: (.+)$', stderr, re.MULTILINE)
            if error_match:
                error_info["line"] = int(error_match.group(1))
                error_info["message"] = error_match.group(2)
                error_info["type"] = "CompileError"

        return error_info


class MultiFileExecutor:
    """
    Execute multi-file projects.

    Example:
        executor = MultiFileExecutor()

        result = await executor.execute_project({
            "main.py": "from utils import helper\\nprint(helper())",
            "utils.py": "def helper(): return 'Hello!'",
            "requirements.txt": "requests>=2.0.0"
        }, Language.PYTHON)
    """

    def __init__(self):
        self.executor = CodeExecutor()

    async def execute_project(
        self,
        files: Dict[str, str],
        language: Language,
        entry_point: str = "main",
        config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Execute a multi-file project.

        Args:
            files: Dict of {filename: content}
            language: Programming language
            entry_point: Main file name (without extension)
            config: Execution configuration

        Returns:
            ExecutionResult
        """
        config = config or ExecutionConfig()
        ext = CodeExecutor.EXTENSIONS[language]
        entry_file = f"{entry_point}{ext}"

        if entry_file not in files:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_type="FileNotFoundError",
                error_message=f"Entry point '{entry_file}' not found in project files"
            )

        # Extract main code and other files
        main_code = files[entry_file]
        other_files = {k: v for k, v in files.items() if k != entry_file}

        # Handle dependencies
        if config.install_dependencies:
            await self._install_dependencies(files, language, config)

        return await self.executor.execute(
            main_code,
            language,
            config,
            other_files
        )

    async def _install_dependencies(
        self,
        files: Dict[str, str],
        language: Language,
        config: ExecutionConfig
    ):
        """Install project dependencies"""
        # This would handle requirements.txt, package.json, go.mod, etc.
        # For now, we rely on Docker images having common packages
        pass


class TestRunner:
    """
    Run tests on generated code.

    Example:
        runner = TestRunner()

        result = await runner.run_tests(
            code="def add(a, b): return a + b",
            tests="def test_add(): assert add(1, 2) == 3",
            language=Language.PYTHON
        )
    """

    def __init__(self):
        self.executor = CodeExecutor()

    async def run_tests(
        self,
        code: str,
        tests: str,
        language: Language,
        config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Run tests against code.

        Args:
            code: Source code to test
            tests: Test code
            language: Programming language
            config: Execution configuration

        Returns:
            ExecutionResult with test results
        """
        config = config or ExecutionConfig()

        # Combine code and tests based on language
        combined = self._combine_code_and_tests(code, tests, language)

        result = await self.executor.execute(combined, language, config)

        # Parse test results
        if language == Language.PYTHON:
            result = self._parse_pytest_output(result)

        return result

    def _combine_code_and_tests(
        self,
        code: str,
        tests: str,
        language: Language
    ) -> str:
        """Combine source code and tests into single executable"""
        if language == Language.PYTHON:
            return f'''{code}

# Tests
import sys

{tests}

if __name__ == "__main__":
    # Run tests
    import traceback
    test_functions = [name for name in dir() if name.startswith('test_')]
    passed = 0
    failed = 0

    for test_name in test_functions:
        try:
            globals()[test_name]()
            print(f"✓ {{test_name}}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {{test_name}}: {{e}}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"✗ {{test_name}}: {{e}}")
            traceback.print_exc()
            failed += 1

    print(f"\\n{{passed}} passed, {{failed}} failed")
    sys.exit(0 if failed == 0 else 1)
'''
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            return f'''{code}

// Tests
{tests}

// Run tests
const testFunctions = Object.entries(global)
    .filter(([name]) => name.startsWith('test_'));

let passed = 0;
let failed = 0;

for (const [name, fn] of testFunctions) {{
    try {{
        fn();
        console.log(`✓ ${{name}}`);
        passed++;
    }} catch (e) {{
        console.log(`✗ ${{name}}: ${{e.message}}`);
        failed++;
    }}
}}

console.log(`\\n${{passed}} passed, ${{failed}} failed`);
process.exit(failed === 0 ? 0 : 1);
'''
        else:
            # Generic combination
            return f"{code}\n\n{tests}"

    def _parse_pytest_output(self, result: ExecutionResult) -> ExecutionResult:
        """Parse pytest-style output"""
        import re

        # Count passes and failures
        pass_match = re.search(r'(\d+) passed', result.stdout)
        fail_match = re.search(r'(\d+) failed', result.stdout)

        passed = int(pass_match.group(1)) if pass_match else 0
        failed = int(fail_match.group(1)) if fail_match else 0

        result.return_value = {
            "passed": passed,
            "failed": failed,
            "total": passed + failed
        }

        return result


# ===========================================
# Convenience Functions
# ===========================================

_default_executor: Optional[CodeExecutor] = None
_default_test_runner: Optional[TestRunner] = None


def get_executor() -> CodeExecutor:
    """Get the default code executor"""
    global _default_executor
    if _default_executor is None:
        _default_executor = CodeExecutor()
    return _default_executor


def get_test_runner() -> TestRunner:
    """Get the default test runner"""
    global _default_test_runner
    if _default_test_runner is None:
        _default_test_runner = TestRunner()
    return _default_test_runner


async def execute_code(
    code: str,
    language: str,
    timeout: int = 30
) -> ExecutionResult:
    """Execute code in sandbox"""
    lang = Language(language.lower())
    config = ExecutionConfig(timeout_seconds=timeout)
    return await get_executor().execute(code, lang, config)


async def execute_python(code: str, timeout: int = 30) -> ExecutionResult:
    """Execute Python code"""
    return await execute_code(code, "python", timeout)


async def execute_javascript(code: str, timeout: int = 30) -> ExecutionResult:
    """Execute JavaScript code"""
    return await execute_code(code, "javascript", timeout)


async def run_tests(
    code: str,
    tests: str,
    language: str
) -> ExecutionResult:
    """Run tests against code"""
    lang = Language(language.lower())
    return await get_test_runner().run_tests(code, tests, lang)
