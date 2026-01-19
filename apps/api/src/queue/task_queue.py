"""
Task Queue for Code Weaver Pro

Implements a Redis-backed task queue for:
- Long-running agent executions
- Background code generation
- Async file processing

Features:
- Priority queues (high, normal, low)
- Task retry with exponential backoff
- Task status tracking
- Graceful shutdown handling
- In-memory fallback for local development
"""

import asyncio
import json
import os
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskStatus(str, Enum):
    """Status of a task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(int, Enum):
    """Priority levels for tasks"""
    HIGH = 0
    NORMAL = 5
    LOW = 10


@dataclass
class Task:
    """Represents a task in the queue"""
    id: str
    name: str
    args: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "args": self.args,
            "priority": self.priority.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "project_id": self.project_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            args=data["args"],
            priority=TaskPriority(data.get("priority", 5)),
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            project_id=data.get("project_id"),
            metadata=data.get("metadata", {})
        )


class BaseTaskQueue(ABC):
    """Abstract base class for task queues"""

    @abstractmethod
    async def enqueue(self, task: Task) -> str:
        """Add a task to the queue"""
        pass

    @abstractmethod
    async def dequeue(self, timeout: Optional[int] = None) -> Optional[Task]:
        """Get the next task from the queue"""
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> None:
        """Update a task"""
        pass

    @abstractmethod
    async def get_tasks_by_project(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        pass


class InMemoryTaskQueue(BaseTaskQueue):
    """In-memory task queue for local development"""

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def enqueue(self, task: Task) -> str:
        """Add task to queue"""
        async with self._lock:
            self._tasks[task.id] = task
            # Priority queue uses (priority, timestamp, task_id) for ordering
            await self._queue.put((
                task.priority.value,
                task.created_at,
                task.id
            ))
            logger.debug(f"Enqueued task {task.id}: {task.name}")
        return task.id

    async def dequeue(self, timeout: Optional[int] = None) -> Optional[Task]:
        """Get next task from queue"""
        try:
            if timeout:
                _, _, task_id = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=timeout
                )
            else:
                _, _, task_id = self._queue.get_nowait()

            async with self._lock:
                task = self._tasks.get(task_id)
                if task and task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now().isoformat()
                    return task
                return None

        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self._tasks.get(task_id)

    async def update_task(self, task: Task) -> None:
        """Update task"""
        async with self._lock:
            self._tasks[task.id] = task

    async def get_tasks_by_project(self, project_id: str) -> List[Task]:
        """Get tasks for a project"""
        return [
            task for task in self._tasks.values()
            if task.project_id == project_id
        ]


class RedisTaskQueue(BaseTaskQueue):
    """Redis-backed task queue for distributed processing"""

    def __init__(self, redis_url: str, queue_name: str = "codeweaver:tasks"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        self._redis = None

    async def _get_redis(self):
        """Get Redis connection"""
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = await redis.from_url(self.redis_url)
        return self._redis

    async def enqueue(self, task: Task) -> str:
        """Add task to Redis queue"""
        redis_client = await self._get_redis()

        # Store task data
        task_key = f"{self.queue_name}:task:{task.id}"
        await redis_client.set(task_key, json.dumps(task.to_dict()))

        # Add to sorted set (priority queue)
        score = task.priority.value * 1e10 + datetime.now().timestamp()
        await redis_client.zadd(f"{self.queue_name}:pending", {task.id: score})

        # Index by project if applicable
        if task.project_id:
            await redis_client.sadd(
                f"{self.queue_name}:project:{task.project_id}",
                task.id
            )

        logger.debug(f"Enqueued task {task.id}: {task.name} to Redis")
        return task.id

    async def dequeue(self, timeout: Optional[int] = None) -> Optional[Task]:
        """Get next task from Redis queue"""
        redis_client = await self._get_redis()

        # Get highest priority task (lowest score)
        if timeout:
            result = await redis_client.bzpopmin(
                f"{self.queue_name}:pending",
                timeout=timeout
            )
            if not result:
                return None
            _, task_id, _ = result
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
        else:
            result = await redis_client.zpopmin(f"{self.queue_name}:pending", 1)
            if not result:
                return None
            task_id, _ = result[0]
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id

        # Get task data
        task = await self.get_task(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now().isoformat()
            await self.update_task(task)

            # Move to processing set
            await redis_client.sadd(f"{self.queue_name}:processing", task_id)

        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task from Redis"""
        redis_client = await self._get_redis()
        task_key = f"{self.queue_name}:task:{task_id}"

        data = await redis_client.get(task_key)
        if data:
            return Task.from_dict(json.loads(data))
        return None

    async def update_task(self, task: Task) -> None:
        """Update task in Redis"""
        redis_client = await self._get_redis()
        task_key = f"{self.queue_name}:task:{task.id}"
        await redis_client.set(task_key, json.dumps(task.to_dict()))

        # Handle completion
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task.completed_at = datetime.now().isoformat()
            await redis_client.srem(f"{self.queue_name}:processing", task.id)

            # Store in completed set with expiry
            await redis_client.sadd(f"{self.queue_name}:completed", task.id)
            await redis_client.expire(task_key, 86400)  # 24 hour TTL

    async def get_tasks_by_project(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        redis_client = await self._get_redis()
        task_ids = await redis_client.smembers(
            f"{self.queue_name}:project:{project_id}"
        )

        tasks = []
        for task_id in task_ids:
            task_id = task_id.decode() if isinstance(task_id, bytes) else task_id
            task = await self.get_task(task_id)
            if task:
                tasks.append(task)

        return tasks


class TaskWorker:
    """Worker that processes tasks from the queue"""

    def __init__(
        self,
        queue: BaseTaskQueue,
        handlers: Dict[str, Callable] = None
    ):
        self.queue = queue
        self.handlers: Dict[str, Callable] = handlers or {}
        self._running = False
        self._current_task: Optional[Task] = None

    def register_handler(self, task_name: str, handler: Callable):
        """Register a handler for a task type"""
        self.handlers[task_name] = handler

    async def process_task(self, task: Task) -> None:
        """Process a single task"""
        handler = self.handlers.get(task.name)

        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"No handler registered for task: {task.name}"
            await self.queue.update_task(task)
            return

        try:
            # Execute handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**task.args)
            else:
                result = handler(**task.args)

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")

            if task.retry_count < task.max_retries:
                # Schedule retry
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.error = str(e)

                # Exponential backoff
                delay = 2 ** task.retry_count
                await asyncio.sleep(delay)

                task.status = TaskStatus.PENDING
                await self.queue.enqueue(task)
            else:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now().isoformat()

        await self.queue.update_task(task)

    async def run(self, poll_interval: int = 1):
        """Run the worker loop"""
        self._running = True
        logger.info("Task worker started")

        while self._running:
            try:
                task = await self.queue.dequeue(timeout=poll_interval)

                if task:
                    self._current_task = task
                    logger.info(f"Processing task {task.id}: {task.name}")
                    await self.process_task(task)
                    self._current_task = None

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(poll_interval)

    def stop(self):
        """Stop the worker"""
        self._running = False
        logger.info("Task worker stopping...")


# Factory function to create appropriate queue
def create_task_queue() -> BaseTaskQueue:
    """Create task queue based on environment"""
    redis_url = os.environ.get("REDIS_URL")

    if redis_url:
        logger.info("Using Redis task queue")
        return RedisTaskQueue(redis_url)
    else:
        logger.info("Using in-memory task queue (local development)")
        return InMemoryTaskQueue()


# Global queue instance
_task_queue: Optional[BaseTaskQueue] = None


def get_task_queue() -> BaseTaskQueue:
    """Get the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = create_task_queue()
    return _task_queue


# Decorator for registering task handlers
def task(name: str, priority: TaskPriority = TaskPriority.NORMAL):
    """Decorator to register a function as a task handler"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

        # Store task metadata
        wrapper._task_name = name
        wrapper._task_priority = priority

        return wrapper
    return decorator
