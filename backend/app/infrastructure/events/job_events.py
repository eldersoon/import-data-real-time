"""Job event manager for SSE pub/sub"""

import asyncio
from typing import Dict, List, Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobEventManager:
    """Manages job-related events for SSE pub/sub"""

    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {"__all__": []}
        self._lock = asyncio.Lock()

    async def subscribe(self, job_id: Optional[str]) -> asyncio.Queue:
        """
        Subscribe to job events.

        Args:
            job_id: Optional job ID to subscribe to specific job, None for all jobs

        Returns:
            Queue to receive events
        """
        async with self._lock:
            queue = asyncio.Queue()
            key = job_id or "__all__"
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(queue)
            logger.info(
                "subscriber_added",
                job_id=job_id,
                total_subscribers=len(self._subscribers[key])
            )
            return queue

    async def unsubscribe(self, job_id: Optional[str], queue: asyncio.Queue) -> None:
        """
        Unsubscribe from job events.

        Args:
            job_id: Optional job ID
            queue: Queue to unsubscribe
        """
        async with self._lock:
            key = job_id or "__all__"
            if key in self._subscribers and queue in self._subscribers[key]:
                self._subscribers[key].remove(queue)
                logger.info(
                    "subscriber_removed",
                    job_id=job_id,
                    remaining_subscribers=len(self._subscribers[key])
                )

    async def publish(self, job_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish an event.

        Args:
            job_id: Job ID
            event_type: Event type (status_update, progress_update, log_update)
            data: Event data
        """
        event = {
            "job_id": job_id,
            "event_type": event_type,
            "data": data,
        }

        async with self._lock:
            # Send to job-specific subscribers
            if job_id in self._subscribers:
                for queue in self._subscribers[job_id]:
                    try:
                        await queue.put(event)
                    except Exception as e:
                        logger.warning(
                            "failed_to_send_event_to_job_subscriber",
                            job_id=job_id,
                            error=str(e)
                        )

            # Send to all-jobs subscribers
            if "__all__" in self._subscribers:
                for queue in self._subscribers["__all__"]:
                    try:
                        await queue.put(event)
                    except Exception as e:
                        logger.warning(
                            "failed_to_send_event_to_all_subscriber",
                            job_id=job_id,
                            error=str(e)
                        )

        logger.debug(
            "event_published",
            job_id=job_id,
            event_type=event_type,
            data=data
        )


# Singleton instance
_event_manager: Optional[JobEventManager] = None


def get_event_manager() -> JobEventManager:
    """
    Get the global event manager instance.

    Returns:
        JobEventManager instance
    """
    global _event_manager
    if _event_manager is None:
        _event_manager = JobEventManager()
    return _event_manager
