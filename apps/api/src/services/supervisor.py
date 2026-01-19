"""
Agent Supervisor Service

Provides error handling, retry logic, and circuit breaker patterns
for reliable agent execution.
"""

from typing import Dict, Optional, Callable, Awaitable, TypeVar, Generic, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ===========================================
# Circuit Breaker States
# ===========================================

class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovery is possible


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker"""
    failure_threshold: int = Field(default=5, description="Failures before opening")
    success_threshold: int = Field(default=2, description="Successes to close from half-open")
    timeout_seconds: float = Field(default=60.0, description="Time before testing recovery")
    half_open_max_calls: int = Field(default=3, description="Max calls in half-open state")


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by stopping requests to failing services.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def is_allowed(self) -> bool:
        """Check if a request should be allowed"""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                # Check if timeout has passed
                if self.last_failure_time:
                    elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout_seconds:
                        logger.info(f"Circuit {self.name} transitioning to half-open")
                        self.state = CircuitState.HALF_OPEN
                        self.half_open_calls = 0
                        return True
                return False

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls < self.config.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                return False

            return False

    async def record_success(self) -> None:
        """Record a successful call"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    logger.info(f"Circuit {self.name} closing after recovery")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0

            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def record_failure(self) -> None:
        """Record a failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit {self.name} opening after half-open failure")
                self.state = CircuitState.OPEN
                self.success_count = 0

            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    logger.warning(f"Circuit {self.name} opening after {self.failure_count} failures")
                    self.state = CircuitState.OPEN

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


# ===========================================
# Retry Configuration
# ===========================================

class RetryConfig(BaseModel):
    """Configuration for retry behavior"""
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    initial_delay: float = Field(default=1.0, description="Initial delay in seconds")
    max_delay: float = Field(default=30.0, description="Maximum delay in seconds")
    exponential_base: float = Field(default=2.0, description="Exponential backoff base")
    jitter: bool = Field(default=True, description="Add random jitter to delays")


class RetryResult(BaseModel, Generic[T]):
    """Result of a retry operation"""
    success: bool
    result: Optional[Any] = None
    attempts: int = 0
    total_delay_seconds: float = 0.0
    errors: list = Field(default_factory=list)


# ===========================================
# Agent Supervisor
# ===========================================

class AgentSupervisor:
    """
    Supervises agent execution with retry and circuit breaker patterns.

    Features:
    - Exponential backoff retries
    - Circuit breaker per agent
    - Fallback to simpler agents
    - Execution statistics
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
    ):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "successes": 0, "failures": 0}
        )

    def _get_circuit(self, agent_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for an agent"""
        if agent_id not in self._circuits:
            self._circuits[agent_id] = CircuitBreaker(
                name=f"agent:{agent_id}",
                config=self.circuit_config,
            )
        return self._circuits[agent_id]

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt with exponential backoff"""
        delay = self.retry_config.initial_delay * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(delay, self.retry_config.max_delay)

        if self.retry_config.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    async def execute_with_supervision(
        self,
        agent_id: str,
        execute_fn: Callable[[], Awaitable[T]],
        fallback_fn: Optional[Callable[[], Awaitable[T]]] = None,
        on_retry: Optional[Callable[[int, Exception], Awaitable[None]]] = None,
    ) -> RetryResult[T]:
        """
        Execute a function with retry and circuit breaker.

        Args:
            agent_id: Identifier for the agent (for circuit breaker)
            execute_fn: The async function to execute
            fallback_fn: Optional fallback function if all retries fail
            on_retry: Optional callback on each retry attempt

        Returns:
            RetryResult with the outcome
        """
        circuit = self._get_circuit(agent_id)
        attempts = 0
        total_delay = 0.0
        errors = []

        # Check circuit breaker
        if not await circuit.is_allowed():
            logger.warning(f"Circuit open for {agent_id}, skipping execution")
            if fallback_fn:
                try:
                    result = await fallback_fn()
                    return RetryResult(
                        success=True,
                        result=result,
                        attempts=0,
                        errors=["Circuit open, used fallback"],
                    )
                except Exception as e:
                    return RetryResult(
                        success=False,
                        attempts=0,
                        errors=[f"Circuit open, fallback failed: {str(e)}"],
                    )

            return RetryResult(
                success=False,
                attempts=0,
                errors=["Circuit breaker open"],
            )

        # Attempt execution with retries
        for attempt in range(self.retry_config.max_retries + 1):
            attempts += 1
            self._stats[agent_id]["attempts"] += 1

            try:
                result = await execute_fn()

                # Success!
                await circuit.record_success()
                self._stats[agent_id]["successes"] += 1

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay_seconds=total_delay,
                    errors=errors,
                )

            except Exception as e:
                error_msg = f"Attempt {attempts}: {type(e).__name__}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Agent {agent_id} failed: {error_msg}")

                # Record failure for circuit breaker
                await circuit.record_failure()

                # Check if we should retry
                if attempt < self.retry_config.max_retries:
                    delay = self._calculate_delay(attempt)
                    total_delay += delay

                    if on_retry:
                        await on_retry(attempt + 1, e)

                    logger.info(f"Retrying {agent_id} in {delay:.2f}s (attempt {attempt + 2})")
                    await asyncio.sleep(delay)

        # All retries exhausted
        self._stats[agent_id]["failures"] += 1

        # Try fallback
        if fallback_fn:
            logger.info(f"Using fallback for {agent_id}")
            try:
                result = await fallback_fn()
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay_seconds=total_delay,
                    errors=errors + ["Used fallback"],
                )
            except Exception as e:
                errors.append(f"Fallback failed: {str(e)}")

        return RetryResult(
            success=False,
            attempts=attempts,
            total_delay_seconds=total_delay,
            errors=errors,
        )

    async def execute_with_timeout(
        self,
        agent_id: str,
        execute_fn: Callable[[], Awaitable[T]],
        timeout_seconds: float = 60.0,
        fallback_fn: Optional[Callable[[], Awaitable[T]]] = None,
    ) -> RetryResult[T]:
        """
        Execute with both timeout and retry/circuit breaker.

        Args:
            agent_id: Agent identifier
            execute_fn: Function to execute
            timeout_seconds: Timeout per attempt
            fallback_fn: Optional fallback

        Returns:
            RetryResult with outcome
        """
        async def wrapped_execute():
            return await asyncio.wait_for(execute_fn(), timeout=timeout_seconds)

        return await self.execute_with_supervision(
            agent_id=agent_id,
            execute_fn=wrapped_execute,
            fallback_fn=fallback_fn,
        )

    def get_circuit_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get circuit breaker status for an agent"""
        circuit = self._circuits.get(agent_id)
        if circuit:
            return circuit.get_status()
        return None

    def get_all_circuit_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get all circuit breaker statuses"""
        return {
            agent_id: circuit.get_status()
            for agent_id, circuit in self._circuits.items()
        }

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get execution statistics for all agents"""
        return dict(self._stats)

    def get_agent_stats(self, agent_id: str) -> Dict[str, int]:
        """Get execution statistics for a specific agent"""
        return dict(self._stats.get(agent_id, {}))

    def reset_circuit(self, agent_id: str) -> bool:
        """Manually reset a circuit breaker"""
        if agent_id in self._circuits:
            circuit = self._circuits[agent_id]
            circuit.state = CircuitState.CLOSED
            circuit.failure_count = 0
            circuit.success_count = 0
            logger.info(f"Circuit {agent_id} manually reset")
            return True
        return False

    def reset_all_circuits(self) -> None:
        """Reset all circuit breakers"""
        for agent_id in self._circuits:
            self.reset_circuit(agent_id)


# ===========================================
# Agent Fallback Registry
# ===========================================

# Map of agent -> fallback agent
# If an agent fails, try these simpler alternatives
AGENT_FALLBACKS: Dict[str, str] = {
    # Complex agents fall back to simpler ones
    "Senior": "FullStackEngineer",
    "BackendEngineer": "FullStackEngineer",
    "FrontendEngineer": "FullStackEngineer",
    "iOS": "FullStackEngineer",
    "Android": "FullStackEngineer",

    # QA falls back to basic verification
    "SecurityEngineer": "QA",

    # Research agents
    "Research": "Ideas",

    # DevOps
    "DevOps": "Verifier",
}


def get_fallback_agent(agent_id: str) -> Optional[str]:
    """Get the fallback agent for a given agent"""
    return AGENT_FALLBACKS.get(agent_id)


# ===========================================
# Singleton and Convenience Functions
# ===========================================

_supervisor: Optional[AgentSupervisor] = None


def get_supervisor() -> AgentSupervisor:
    """Get or create the global supervisor instance"""
    global _supervisor
    if _supervisor is None:
        _supervisor = AgentSupervisor()
    return _supervisor


async def supervised_execute(
    agent_id: str,
    execute_fn: Callable[[], Awaitable[T]],
    fallback_fn: Optional[Callable[[], Awaitable[T]]] = None,
) -> RetryResult[T]:
    """
    Execute a function with supervision.

    Convenience function using global supervisor.
    """
    supervisor = get_supervisor()
    return await supervisor.execute_with_supervision(
        agent_id=agent_id,
        execute_fn=execute_fn,
        fallback_fn=fallback_fn,
    )
