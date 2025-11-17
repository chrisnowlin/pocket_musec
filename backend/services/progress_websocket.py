"""WebSocket service for real-time progress updates."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .presentation_jobs_persistent import get_job_manager
from .presentation_errors import PresentationError, PresentationErrorCode
from ..models.progress_tracking import ProgressUpdate

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates."""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store which jobs each user is subscribed to
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # Store progress update history for reconnection scenarios
        self.progress_history: Dict[str, List[ProgressUpdate]] = {}
        self.max_history_size = 50

    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """Connect a WebSocket and add to active connections."""
        try:
            await websocket.accept()

            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
                self.user_subscriptions[user_id] = set()

            self.active_connections[user_id].append(websocket)
            logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect WebSocket for user {user_id}: {e}")
            return False

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """Remove a WebSocket connection."""
        try:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)

                # Clean up if no more connections for this user
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    if user_id in self.user_subscriptions:
                        del self.user_subscriptions[user_id]

                logger.info(f"WebSocket disconnected for user {user_id}. Remaining: {len(self.active_connections.get(user_id, []))}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect for user {user_id}: {e}")

    def subscribe_to_job(self, user_id: str, job_id: str) -> bool:
        """Subscribe a user to job progress updates."""
        if user_id not in self.user_subscriptions:
            return False

        self.user_subscriptions[user_id].add(job_id)

        # Send recent history if available
        if job_id in self.progress_history:
            asyncio.create_task(self._send_history_to_user(user_id, job_id))

        logger.info(f"User {user_id} subscribed to job {job_id}")
        return True

    def unsubscribe_from_job(self, user_id: str, job_id: str) -> None:
        """Unsubscribe a user from job progress updates."""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(job_id)
            logger.info(f"User {user_id} unsubscribed from job {job_id}")

    async def send_progress_update(self, job_id: str, progress_update: ProgressUpdate) -> int:
        """Send progress update to all subscribed users."""
        sent_count = 0

        try:
            # Store in history
            self._store_progress_update(job_id, progress_update)

            # Find all users subscribed to this job
            subscribed_users = [
                user_id for user_id, job_ids in self.user_subscriptions.items()
                if job_id in job_ids
            ]

            # Send to each subscribed user
            for user_id in subscribed_users:
                user_sent = await self._send_to_user(user_id, progress_update.to_dict())
                if user_sent:
                    sent_count += 1

            logger.debug(f"Progress update for job {job_id} sent to {sent_count} users")
            return sent_count

        except Exception as e:
            logger.error(f"Failed to send progress update for job {job_id}: {e}")
            return 0

    async def send_job_status_update(self, job_id: str, job_status: dict) -> int:
        """Send job status update to all subscribed users."""
        try:
            # Convert job status to progress update
            progress_update = ProgressUpdate(
                job_id=job_id,
                progress=None,  # Will be enhanced later
                update_type="job_status"
            )

            # Include job status in the update
            update_data = progress_update.to_dict()
            update_data["job_status"] = job_status

            return await self._send_to_subscribers(job_id, update_data)

        except Exception as e:
            logger.error(f"Failed to send job status update for job {job_id}: {e}")
            return 0

    async def send_job_completion(self, job_id: str, result_data: dict) -> int:
        """Send job completion notification."""
        try:
            completion_update = {
                "job_id": job_id,
                "update_type": "job_complete",
                "timestamp": datetime.utcnow().isoformat(),
                "result": result_data
            }

            return await self._send_to_subscribers(job_id, completion_update)

        except Exception as e:
            logger.error(f"Failed to send job completion for job {job_id}: {e}")
            return 0

    async def send_job_error(self, job_id: str, error_data: dict) -> int:
        """Send job error notification."""
        try:
            error_update = {
                "job_id": job_id,
                "update_type": "job_error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": error_data
            }

            return await self._send_to_subscribers(job_id, error_update)

        except Exception as e:
            logger.error(f"Failed to send job error for job {job_id}: {e}")
            return 0

    async def broadcast_to_user(self, user_id: str, message: dict) -> int:
        """Send a message to all of a user's connections."""
        sent_count = 0

        if user_id not in self.active_connections:
            return 0

        # Filter out closed connections
        active_websockets = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
                sent_count += 1
                active_websockets.append(websocket)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket for user {user_id}: {e}")
                # Connection is likely closed, don't add back to active list

        # Update active connections list
        self.active_connections[user_id] = active_websockets

        # Clean up if no active connections remain
        if not active_websockets:
            del self.active_connections[user_id]
            if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]

        return sent_count

    async def _send_to_subscribers(self, job_id: str, message: dict) -> int:
        """Send a message to all users subscribed to a specific job."""
        sent_count = 0

        subscribed_users = [
            user_id for user_id, job_ids in self.user_subscriptions.items()
            if job_id in job_ids
        ]

        for user_id in subscribed_users:
            sent_count += await self._send_to_user(user_id, message)

        return sent_count

    async def _send_to_user(self, user_id: str, message: dict) -> bool:
        """Send a message to a specific user."""
        if user_id not in self.active_connections:
            return False

        sent_to_any = False
        active_websockets = []

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(json.dumps(message))
                sent_to_any = True
                active_websockets.append(websocket)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket for user {user_id}: {e}")

        # Update active connections list
        self.active_connections[user_id] = active_websockets

        # Clean up if no active connections remain
        if not active_websockets:
            del self.active_connections[user_id]
            if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]

        return sent_to_any

    async def _send_history_to_user(self, user_id: str, job_id: str) -> None:
        """Send recent progress history to a newly connected user."""
        if job_id not in self.progress_history:
            return

        # Send the last few progress updates to catch up
        recent_updates = self.progress_history[j_id][-5:]  # Last 5 updates

        for update in recent_updates:
            await self._send_to_user(user_id, update.to_dict())

    def _store_progress_update(self, job_id: str, progress_update: ProgressUpdate) -> None:
        """Store progress update in history."""
        if job_id not in self.progress_history:
            self.progress_history[job_id] = []

        self.progress_history[job_id].append(progress_update)

        # Limit history size
        if len(self.progress_history[job_id]) > self.max_history_size:
            self.progress_history[job_id] = self.progress_history[job_id][-self.max_history_size:]

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections."""
        stats = {
            "total_users": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "total_subscriptions": sum(len(jobs) for jobs in self.user_subscriptions.values()),
            "active_jobs": set()
        }

        # Collect all active job subscriptions
        for job_ids in self.user_subscriptions.values():
            stats["active_jobs"].update(job_ids)

        stats["active_jobs"] = len(stats["active_jobs"])
        return stats

    async def cleanup_inactive_connections(self) -> int:
        """Clean up inactive WebSocket connections."""
        cleaned_count = 0

        for user_id, connections in list(self.active_connections.items()):
            active_connections = []

            for websocket in connections:
                try:
                    # Test connection with ping (or just try to send empty message)
                    await websocket.ping()
                    active_connections.append(websocket)
                except Exception:
                    # Connection is dead
                    cleaned_count += 1

            if active_connections:
                self.active_connections[user_id] = active_connections
            else:
                # No active connections for this user
                del self.active_connections[user_id]
                if user_id in self.user_subscriptions:
                    del self.user_subscriptions[user_id]

        logger.info(f"Cleaned up {cleaned_count} inactive WebSocket connections")
        return cleaned_count


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager


class WebSocketProgressService:
    """Service for managing WebSocket progress updates."""

    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.job_manager = get_job_manager()

    async def send_step_progress(
        self,
        job_id: str,
        step: str,
        progress: float,
        message: str = "",
        details: dict = None
    ) -> int:
        """Send step progress update."""
        try:
            # Get the job and its detailed progress
            job = self.job_manager.get_job(job_id)
            if not job:
                logger.warning(f"Attempted to send progress for non-existent job {job_id}")
                return 0

            detailed_progress = job.get_detailed_progress()
            if not detailed_progress:
                return 0

            # Update the detailed progress
            from ..models.progress_tracking import ProgressStep
            if step in [s.value for s in ProgressStep]:
                progress_step = ProgressStep(step)
                detailed_progress.update_step_progress(progress_step, progress, message, details)

            # Create progress update
            progress_update = ProgressUpdate(
                job_id=job_id,
                progress=detailed_progress,
                update_type="progress"
            )

            # Send to subscribers
            return await self.websocket_manager.send_progress_update(job_id, progress_update)

        except Exception as e:
            logger.error(f"Failed to send step progress for job {job_id}: {e}")
            return 0

    async def send_step_complete(
        self,
        job_id: str,
        step: str,
        result_data: dict = None,
        skip_step: bool = False
    ) -> int:
        """Send step completion update."""
        try:
            job = self.job_manager.get_job(job_id)
            if not job:
                return 0

            detailed_progress = job.get_detailed_progress()
            if not detailed_progress:
                return 0

            # Complete the step
            from ..models.progress_tracking import ProgressStep
            if step in [s.value for s in ProgressStep]:
                progress_step = ProgressStep(step)
                detailed_progress.complete_step(progress_step, result_data, skip_step)

            # Create progress update
            progress_update = ProgressUpdate(
                job_id=job_id,
                progress=detailed_progress,
                update_type="step_complete"
            )

            return await self.websocket_manager.send_progress_update(job_id, progress_update)

        except Exception as e:
            logger.error(f"Failed to send step completion for job {job_id}: {e}")
            return 0

    async def send_step_error(
        self,
        job_id: str,
        step: str,
        error_message: str,
        error_details: dict = None
    ) -> int:
        """Send step error update."""
        try:
            job = self.job_manager.get_job(job_id)
            if not job:
                return 0

            detailed_progress = job.get_detailed_progress()
            if not detailed_progress:
                return 0

            # Mark step as failed
            from ..models.progress_tracking import ProgressStep
            if step in [s.value for s in ProgressStep]:
                progress_step = ProgressStep(step)
                detailed_progress.fail_step(progress_step, error_message, error_details)

            # Create progress update
            progress_update = ProgressUpdate(
                job_id=job_id,
                progress=detailed_progress,
                update_type="step_error"
            )

            return await self.websocket_manager.send_progress_update(job_id, progress_update)

        except Exception as e:
            logger.error(f"Failed to send step error for job {job_id}: {e}")
            return 0


# Global progress service instance
progress_service = WebSocketProgressService()


def get_progress_service() -> WebSocketProgressService:
    """Get the global progress service instance."""
    return progress_service