"""
WebSocket Connection Manager for real-time communication
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


# Heartbeat configuration
HEARTBEAT_INTERVAL_SECONDS = 30
HEARTBEAT_TIMEOUT_SECONDS = 10


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports:
    - Multiple connections per project
    - Broadcasting to all connections for a project
    - Individual message sending
    - Connection lifecycle management
    - Automatic heartbeat to keep connections alive
    """

    def __init__(self, heartbeat_interval: int = HEARTBEAT_INTERVAL_SECONDS):
        # project_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> project_id mapping for cleanup
        self.connection_projects: Dict[WebSocket, str] = {}
        # WebSocket -> heartbeat task mapping
        self._heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        # Heartbeat interval
        self.heartbeat_interval = heartbeat_interval

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        """Accept a new WebSocket connection and register it for a project"""
        await websocket.accept()

        async with self._lock:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()

            self.active_connections[project_id].add(websocket)
            self.connection_projects[websocket] = project_id

        # Start heartbeat for this connection
        heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(websocket, project_id)
        )
        self._heartbeat_tasks[websocket] = heartbeat_task

        logger.info(f"WebSocket connected for project {project_id}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        # Stop heartbeat task
        if websocket in self._heartbeat_tasks:
            task = self._heartbeat_tasks.pop(websocket)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            project_id = self.connection_projects.pop(websocket, None)

            if project_id and project_id in self.active_connections:
                self.active_connections[project_id].discard(websocket)

                # Clean up empty project sets
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]

        logger.info(f"WebSocket disconnected for project {project_id}")

    async def _heartbeat_loop(self, websocket: WebSocket, project_id: str) -> None:
        """
        Send periodic heartbeat messages to keep the connection alive.

        This prevents proxies and load balancers from closing idle connections.
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                # Send heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "project_id": project_id,
                }

                try:
                    await asyncio.wait_for(
                        websocket.send_json(heartbeat),
                        timeout=HEARTBEAT_TIMEOUT_SECONDS
                    )
                    logger.debug(f"Heartbeat sent for project {project_id}")
                except asyncio.TimeoutError:
                    logger.warning(f"Heartbeat timeout for project {project_id}")
                    break
                except Exception as e:
                    logger.warning(f"Heartbeat failed for project {project_id}: {e}")
                    break

        except asyncio.CancelledError:
            # Normal cancellation during disconnect
            pass
        except Exception as e:
            logger.error(f"Heartbeat loop error for project {project_id}: {e}")

        # Clean up if heartbeat failed
        if websocket in self.connection_projects:
            await self.disconnect(websocket)

    async def send_json(self, websocket: WebSocket, data: dict) -> bool:
        """Send JSON data to a specific WebSocket connection"""
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            return False

    async def broadcast_to_project(self, project_id: str, data: dict) -> int:
        """
        Broadcast a message to all connections for a project.

        Returns the number of successful sends.
        """
        sent_count = 0

        async with self._lock:
            connections = self.active_connections.get(project_id, set()).copy()

        failed_connections = []

        for websocket in connections:
            try:
                await websocket.send_json(data)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                failed_connections.append(websocket)

        # Clean up failed connections
        for websocket in failed_connections:
            await self.disconnect(websocket)

        return sent_count

    async def send_event(
        self,
        project_id: str,
        event_type: str,
        **kwargs
    ) -> int:
        """
        Send a typed event to all connections for a project.

        Convenience method for sending GenerationEvent-like messages.
        """
        event = {"type": event_type, **kwargs}
        return await self.broadcast_to_project(project_id, event)

    def get_connection_count(self, project_id: Optional[str] = None) -> int:
        """Get the number of active connections, optionally for a specific project"""
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())

    def get_active_projects(self) -> Set[str]:
        """Get all project IDs with active connections"""
        return set(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
