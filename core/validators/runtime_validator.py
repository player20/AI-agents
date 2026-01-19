"""
Runtime Validation Module

Validates that a project can start and run successfully.
"""

import shutil
import subprocess
import sys
import signal
import time
import requests
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import threading

from .project_detector import ProjectType, ProjectInfo


def _get_executable(name: str) -> str:
    """Get full path to executable, handling Windows .cmd wrappers."""
    executable = shutil.which(name)
    return executable if executable else name


def _safe_popen(args: List[str], cwd: str = None, **kwargs) -> subprocess.Popen:
    """Safely create Popen without shell=True."""
    resolved_args = [_get_executable(args[0])] + args[1:]
    kwargs.pop('shell', None)
    return subprocess.Popen(resolved_args, cwd=cwd, **kwargs)


@dataclass
class RuntimeResult:
    """Result of runtime validation."""
    status: str  # pass, fail, skip
    message: str
    startup_time_ms: Optional[int] = None
    url: Optional[str] = None
    response_code: Optional[int] = None
    process_output: Optional[str] = None
    errors: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "startup_time_ms": self.startup_time_ms,
            "url": self.url,
            "response_code": self.response_code,
            "process_output": self.process_output[:500] if self.process_output else None,
            "errors": self.errors[:500] if self.errors else None,
        }


class RuntimeValidator:
    """
    Validates that a project can start and respond to requests.

    Starts the server, waits for it to be ready, and makes a health check request.
    """

    # Start configurations per project type
    START_CONFIGS = {
        ProjectType.STREAMLIT: {
            "command": [sys.executable, "-m", "streamlit", "run", "{entry_point}",
                        "--server.headless=true", "--server.port={port}"],
            "port": 8501,
            "health_endpoint": "/",
            "startup_timeout": 30,
        },
        ProjectType.FLASK: {
            "command": [sys.executable, "-m", "flask", "run", "--port={port}"],
            "port": 5000,
            "health_endpoint": "/",
            "startup_timeout": 15,
            "env": {"FLASK_APP": "{entry_point}"},
        },
        ProjectType.DJANGO: {
            "command": [sys.executable, "manage.py", "runserver", "{port}"],
            "port": 8000,
            "health_endpoint": "/",
            "startup_timeout": 20,
        },
        ProjectType.FASTAPI: {
            "command": [sys.executable, "-m", "uvicorn", "{entry_point}:app",
                        "--host=0.0.0.0", "--port={port}"],
            "port": 8000,
            "health_endpoint": "/",
            "startup_timeout": 15,
        },
        ProjectType.REACT: {
            "command": ["npm", "start"],
            "port": 3000,
            "health_endpoint": "/",
            "startup_timeout": 60,
            "env": {"PORT": "{port}", "BROWSER": "none"},
        },
        ProjectType.VUE: {
            "command": ["npm", "run", "serve"],
            "port": 8080,
            "health_endpoint": "/",
            "startup_timeout": 60,
        },
        ProjectType.NEXTJS: {
            "command": ["npm", "run", "dev"],
            "port": 3000,
            "health_endpoint": "/",
            "startup_timeout": 60,
            "env": {"PORT": "{port}"},
        },
        ProjectType.NODEJS: {
            "command": ["npm", "start"],
            "port": 3000,
            "health_endpoint": "/",
            "startup_timeout": 30,
        },
        ProjectType.STATIC_HTML: {
            "command": [sys.executable, "-m", "http.server", "{port}"],
            "port": 8000,
            "health_endpoint": "/",
            "startup_timeout": 5,
        },
    }

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.output_buffer = []

    def validate(self, project: ProjectInfo, auto_stop: bool = True) -> RuntimeResult:
        """
        Validate that a project starts and responds to requests.

        Args:
            project: ProjectInfo with project details
            auto_stop: Whether to stop the server after validation

        Returns:
            RuntimeResult with startup status
        """
        config = self.START_CONFIGS.get(project.project_type)

        if not config:
            return RuntimeResult(
                status="skip",
                message=f"Runtime validation not configured for {project.project_type.value}"
            )

        # Find an available port
        port = self._find_available_port(config["port"])
        if not port:
            return RuntimeResult(
                status="fail",
                message=f"Could not find available port near {config['port']}"
            )

        # Build the command
        entry_point = project.entry_point or "app.py"
        command = self._build_command(config["command"], entry_point, port)

        # Build environment
        env = self._build_env(config.get("env", {}), entry_point, port)

        try:
            # Start the server
            start_time = time.time()
            result = self._start_server(project.path, command, env, config["startup_timeout"])

            if result.status == "fail":
                return result

            # Wait for server to be ready
            url = f"http://localhost:{port}{config['health_endpoint']}"
            ready_result = self._wait_for_ready(url, config["startup_timeout"])

            startup_time = int((time.time() - start_time) * 1000)

            if ready_result.status == "fail":
                ready_result.startup_time_ms = startup_time
                ready_result.process_output = "\n".join(self.output_buffer[-20:])
                return ready_result

            return RuntimeResult(
                status="pass",
                message=f"Server started successfully on port {port}",
                startup_time_ms=startup_time,
                url=url,
                response_code=ready_result.response_code,
            )

        finally:
            if auto_stop:
                self.stop()

    def _find_available_port(self, preferred: int) -> Optional[int]:
        """Find an available port near the preferred port."""
        for port in range(preferred, preferred + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue
        return None

    def _build_command(self, template: list, entry_point: str, port: int) -> list:
        """Build the command with substitutions."""
        command = []
        for part in template:
            part = part.replace("{entry_point}", entry_point)
            part = part.replace("{port}", str(port))
            command.append(part)
        return command

    def _build_env(self, template: dict, entry_point: str, port: int) -> dict:
        """Build environment variables with substitutions."""
        import os
        env = os.environ.copy()
        for key, value in template.items():
            value = value.replace("{entry_point}", entry_point)
            value = value.replace("{port}", str(port))
            env[key] = value
        return env

    def _start_server(self, path: Path, command: list, env: dict, timeout: int) -> RuntimeResult:
        """Start the server process."""
        try:
            # Use safe popen that resolves executable paths cross-platform
            self.process = _safe_popen(
                command,
                cwd=path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Start output reader thread
            def read_output():
                for line in self.process.stdout:
                    self.output_buffer.append(line.strip())
                    if len(self.output_buffer) > 100:
                        self.output_buffer.pop(0)

            thread = threading.Thread(target=read_output, daemon=True)
            thread.start()

            # Wait a moment for the process to start
            time.sleep(1)

            # Check if process is still running
            if self.process.poll() is not None:
                return RuntimeResult(
                    status="fail",
                    message=f"Server process exited with code {self.process.returncode}",
                    errors="\n".join(self.output_buffer),
                )

            return RuntimeResult(
                status="pass",
                message="Server process started"
            )

        except FileNotFoundError:
            return RuntimeResult(
                status="fail",
                message=f"Command not found: {command[0]}"
            )
        except Exception as e:
            return RuntimeResult(
                status="fail",
                message=f"Failed to start server: {str(e)}"
            )

    def _wait_for_ready(self, url: str, timeout: int) -> RuntimeResult:
        """Wait for the server to respond to requests."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=2, allow_redirects=True)
                # Accept any 2xx or 3xx response as success
                if 200 <= response.status_code < 400:
                    return RuntimeResult(
                        status="pass",
                        message="Server is ready",
                        response_code=response.status_code,
                    )
                elif response.status_code >= 500:
                    return RuntimeResult(
                        status="fail",
                        message=f"Server returned error: {response.status_code}",
                        response_code=response.status_code,
                    )
            except requests.exceptions.ConnectionError:
                # Server not ready yet
                pass
            except requests.exceptions.Timeout:
                # Server responding slowly
                pass
            except Exception as e:
                return RuntimeResult(
                    status="fail",
                    message=f"Error checking server: {str(e)}"
                )

            # Check if process died
            if self.process and self.process.poll() is not None:
                return RuntimeResult(
                    status="fail",
                    message=f"Server process died with code {self.process.returncode}",
                    errors="\n".join(self.output_buffer[-10:]),
                )

            time.sleep(1)

        return RuntimeResult(
            status="fail",
            message=f"Server did not respond within {timeout} seconds",
            url=url,
        )

    def stop(self) -> None:
        """Stop the running server."""
        if self.process:
            try:
                # Try graceful shutdown first
                if sys.platform == "win32":
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)

                # Wait for process to end
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill
                    self.process.kill()
                    self.process.wait(timeout=5)

            except Exception:
                pass
            finally:
                self.process = None

    def get_running_url(self) -> Optional[str]:
        """Get the URL of the currently running server."""
        if self.process and self.process.poll() is None:
            # Server is running
            return getattr(self, '_last_url', None)
        return None


# Convenience function
def validate_runtime(project: ProjectInfo, auto_stop: bool = True) -> RuntimeResult:
    """
    Validate that a project starts and responds to requests.

    Args:
        project: ProjectInfo with project details
        auto_stop: Whether to stop the server after validation

    Returns:
        RuntimeResult with startup status
    """
    validator = RuntimeValidator()
    return validator.validate(project, auto_stop)
