"""Job monitor that watches database changes and publishes events"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.domain.models.import_job import ImportJobStatus
from app.infrastructure.repositories.import_job_repository import ImportJobRepository
from app.infrastructure.repositories.job_log_repository import JobLogRepository
from app.infrastructure.events.job_events import get_event_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class JobMonitor:
    """Monitors job changes in the database and publishes events"""

    def __init__(self):
        self.event_manager = get_event_manager()
        self.running = False
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._all_jobs_monitor_task: Optional[asyncio.Task] = None
        self._last_all_jobs_states: Dict[str, Dict[str, Any]] = {}

    async def start_monitoring_all_jobs(self, interval: float = 2.0) -> None:
        """
        Start monitoring all jobs.

        Args:
            interval: Polling interval in seconds
        """
        if not self.running:
            self.running = True
            self._all_jobs_monitor_task = asyncio.create_task(
                self._monitor_all_jobs(interval)
            )
            logger.info("started_monitoring_all_jobs")

    async def stop_monitoring_all_jobs(self) -> None:
        """Stop monitoring all jobs."""
        if self.running:
            self.running = False
            if self._all_jobs_monitor_task:
                self._all_jobs_monitor_task.cancel()
                try:
                    await self._all_jobs_monitor_task
                except asyncio.CancelledError:
                    pass
            logger.info("stopped_monitoring_all_jobs")

    async def _monitor_all_jobs(self, interval: float) -> None:
        """Monitor all jobs and publish events on changes."""
        last_job_states: Dict[str, Dict[str, Any]] = {}

        while self.running:
            try:
                db: Session = SessionLocal()
                try:
                    repository = ImportJobRepository(db)
                    active_jobs = repository.list(
                        skip=0,
                        limit=1000,
                        status=None,
                    )

                    # Filter active jobs
                    active_jobs = [
                        job
                        for job in active_jobs
                        if job.status in [
                            ImportJobStatus.PENDING,
                            ImportJobStatus.PROCESSING,
                            ImportJobStatus.COMPLETED,
                            ImportJobStatus.FAILED,
                        ]
                    ]

                    current_job_ids = {str(job.id) for job in active_jobs}

                    # Check for changes
                    for job in active_jobs:
                        job_id = str(job.id)
                        current_state = {
                            "status": job.status,
                            "processed_rows": job.processed_rows,
                            "error_rows": job.error_rows,
                            "total_rows": job.total_rows,
                        }

                        last_state = last_job_states.get(job_id)

                        if last_state != current_state:
                            # Determine event type
                            event_type = "progress_update"
                            if last_state is None:
                                event_type = "status_update"
                            elif last_state.get("status") != current_state["status"]:
                                event_type = "status_update"

                            # Publish event
                            await self.event_manager.publish(
                                job_id,
                                event_type,
                                {
                                    "id": job_id,
                                    "job_id": job_id,
                                    "filename": job.filename,
                                    "status": job.status,
                                    "total_rows": job.total_rows,
                                    "processed_rows": job.processed_rows,
                                    "error_rows": job.error_rows,
                                    "started_at": job.started_at.isoformat() if job.started_at else None,
                                    "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                                    "created_at": job.created_at.isoformat(),
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )
                            last_job_states[job_id] = current_state

                    # Remove jobs that are no longer active
                    for job_id in list(last_job_states.keys()):
                        if job_id not in current_job_ids:
                            del last_job_states[job_id]

                finally:
                    db.close()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("job_monitoring_cancelled_all_jobs")
                break
            except Exception as e:
                logger.error("job_monitoring_error_all_jobs", error=str(e))
                await asyncio.sleep(interval)


# Singleton instance
_monitor: Optional[JobMonitor] = None


def get_monitor() -> JobMonitor:
    """
    Get the global monitor instance.

    Returns:
        JobMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = JobMonitor()
    return _monitor
