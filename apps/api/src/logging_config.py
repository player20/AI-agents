"""
Structured Logging Configuration for Code Weaver Pro

Uses structlog for structured, context-rich logging with:
- JSON output for production
- Colored console output for development
- Request ID tracking
- Agent execution context
- Performance metrics
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional
from contextvars import ContextVar
from functools import wraps
import uuid

# Context variables for request-scoped data
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
project_id_var: ContextVar[Optional[str]] = ContextVar('project_id', default=None)
agent_name_var: ContextVar[Optional[str]] = ContextVar('agent_name', default=None)


def configure_logging(
    level: str = None,
    json_output: bool = None,
    log_file: Optional[str] = None
):
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_output: If True, output JSON logs. If None, auto-detect from environment.
        log_file: Optional file path to write logs to
    """
    level = level or os.environ.get("LOG_LEVEL", "INFO")
    is_development = os.environ.get("API_DEBUG", "false").lower() == "true"

    # Auto-detect JSON output based on environment
    if json_output is None:
        json_output = not is_development

    try:
        import structlog

        # Shared processors for all outputs
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_context_processor,
        ]

        if json_output:
            # Production: JSON output
            processors = shared_processors + [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ]
        else:
            # Development: Colored console output
            processors = shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ]

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Also configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, level.upper()),
        )

        # Add file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logging.getLogger().addHandler(file_handler)

        logger = get_logger("logging_config")
        logger.info("Logging configured", level=level, json_output=json_output)

    except ImportError:
        # Fallback to standard logging if structlog not installed
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=getattr(logging, level.upper()),
        )
        logging.info("Using standard logging (structlog not installed)")


def add_context_processor(logger, method_name, event_dict):
    """Add context variables to log entries"""
    # Add request ID if available
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id

    # Add project ID if available
    project_id = project_id_var.get()
    if project_id:
        event_dict["project_id"] = project_id

    # Add agent name if available
    agent_name = agent_name_var.get()
    if agent_name:
        event_dict["agent"] = agent_name

    return event_dict


def get_logger(name: str = None):
    """Get a structured logger instance"""
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        return logging.getLogger(name)


def set_request_context(request_id: str = None, project_id: str = None, agent_name: str = None):
    """Set context variables for the current request/task"""
    if request_id:
        request_id_var.set(request_id)
    if project_id:
        project_id_var.set(project_id)
    if agent_name:
        agent_name_var.set(agent_name)


def clear_request_context():
    """Clear all context variables"""
    request_id_var.set(None)
    project_id_var.set(None)
    agent_name_var.set(None)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return str(uuid.uuid4())[:8]


# ===========================================
# Logging decorators
# ===========================================

def log_execution_time(logger_name: str = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()

            logger.debug(f"Starting {func.__name__}", function=func.__name__)

            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2)
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()

            logger.debug(f"Starting {func.__name__}", function=func.__name__)

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2)
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(e)
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_agent_execution(agent_name: str):
    """Decorator to log agent execution with context"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger("agents")

            # Set agent context
            previous_agent = agent_name_var.get()
            agent_name_var.set(agent_name)

            start_time = time.time()
            logger.info(f"Agent started", agent=agent_name, status="running")

            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                logger.info(
                    f"Agent completed",
                    agent=agent_name,
                    status="completed",
                    duration_ms=round(elapsed * 1000, 2)
                )
                return result

            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Agent failed",
                    agent=agent_name,
                    status="failed",
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(e)
                )
                raise

            finally:
                # Restore previous agent context
                agent_name_var.set(previous_agent)

        return wrapper
    return decorator


# ===========================================
# FastAPI middleware for request logging
# ===========================================

async def logging_middleware(request, call_next):
    """FastAPI middleware for request/response logging"""
    from fastapi import Request

    logger = get_logger("http")

    # Generate and set request ID
    request_id = request.headers.get("X-Request-ID") or generate_request_id()
    set_request_context(request_id=request_id)

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown"
    )

    start_time = time.time()

    try:
        response = await call_next(request)
        elapsed = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2)
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            path=request.url.path,
            duration_ms=round(elapsed * 1000, 2),
            error=str(e)
        )
        raise

    finally:
        clear_request_context()
