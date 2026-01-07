"""Job scheduler service for running periodic tasks."""

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from job_queue import job_queue
from spo.extensions import db
from spo.models import ScheduledJob

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None

# Registry of available job types and their execution functions
JOB_REGISTRY = {}


def register_job_type(job_type: str, func):
    """Register a job type with its execution function.

    Args:
        job_type: Unique identifier for the job type (e.g., 'deduplication')
        func: Function to execute. Will be called with (job_id: int, **kwargs)
    """
    JOB_REGISTRY[job_type] = func
    logger.info(f"Registered job type: {job_type}")


def _execute_scheduled_job(scheduled_job_id: int):
    """Execute a scheduled job and update its status.

    Args:
        scheduled_job_id: ID of the ScheduledJob database record
    """
    from spo import create_app

    app = create_app(start_jobs=False)

    with app.app_context():
        scheduled_job = ScheduledJob.query.get(scheduled_job_id)
        if not scheduled_job or not scheduled_job.enabled:
            logger.warning(f"Scheduled job {scheduled_job_id} not found or disabled")
            return

        job_func = JOB_REGISTRY.get(scheduled_job.job_type)
        if not job_func:
            logger.error(f"No handler registered for job type: {scheduled_job.job_type}")
            scheduled_job.last_run_at = datetime.now(UTC)
            scheduled_job.last_run_status = "failed"
            scheduled_job.last_run_message = f"Unknown job type: {scheduled_job.job_type}"
            db.session.commit()
            return

        try:
            logger.info(f"Executing scheduled job: {scheduled_job.job_name}")

            # Enqueue the job in the job queue for async execution
            job_id = job_queue.enqueue(job_func)

            scheduled_job.last_run_at = datetime.now(UTC)
            scheduled_job.last_run_status = "queued"
            scheduled_job.last_run_message = f"Enqueued as job {job_id[:8]}"
            db.session.commit()

            logger.info(f"Scheduled job {scheduled_job.job_name} enqueued as {job_id}")

        except Exception as e:
            logger.exception(f"Error executing scheduled job {scheduled_job.job_name}")
            scheduled_job.last_run_at = datetime.now(UTC)
            scheduled_job.last_run_status = "failed"
            scheduled_job.last_run_message = str(e)[:500]
            db.session.commit()


def init_scheduler(app):
    """Initialize the scheduler and load scheduled jobs from database.

    Args:
        app: Flask application instance
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already initialized")
        return _scheduler

    _scheduler = BackgroundScheduler(daemon=True)

    with app.app_context():
        # Load all enabled scheduled jobs from database
        scheduled_jobs = ScheduledJob.query.filter_by(enabled=True).all()

        for scheduled_job in scheduled_jobs:
            try:
                trigger = CronTrigger.from_crontab(scheduled_job.cron_expression)
                _scheduler.add_job(
                    func=_execute_scheduled_job,
                    trigger=trigger,
                    args=[scheduled_job.id],
                    id=f"scheduled_job_{scheduled_job.id}",
                    name=scheduled_job.job_name,
                    replace_existing=True,
                )
                logger.info(
                    f"Scheduled job '{scheduled_job.job_name}' "
                    f"with cron '{scheduled_job.cron_expression}'"
                )
            except Exception as e:
                logger.error(
                    f"Failed to schedule job '{scheduled_job.job_name}': {e}", exc_info=True
                )

    _scheduler.start()
    logger.info(f"Scheduler started with {len(_scheduler.get_jobs())} jobs")

    return _scheduler


def reload_scheduled_job(scheduled_job_id: int, app=None):
    """Reload a single scheduled job from database.

    Args:
        scheduled_job_id: ID of the ScheduledJob to reload
        app: Flask application instance (optional, will create if needed)
    """
    global _scheduler

    if _scheduler is None:
        logger.error("Scheduler not initialized")
        return False

    if app is None:
        from spo import create_app

        app = create_app(start_jobs=False)

    with app.app_context():
        scheduled_job = ScheduledJob.query.get(scheduled_job_id)
        if not scheduled_job:
            logger.error(f"Scheduled job {scheduled_job_id} not found")
            return False

        job_id = f"scheduled_job_{scheduled_job.id}"

        # Remove existing job if present
        if _scheduler.get_job(job_id):
            _scheduler.remove_job(job_id)
            logger.info(f"Removed existing schedule for '{scheduled_job.job_name}'")

        # Add job if enabled
        if scheduled_job.enabled:
            try:
                trigger = CronTrigger.from_crontab(scheduled_job.cron_expression)
                _scheduler.add_job(
                    func=_execute_scheduled_job,
                    trigger=trigger,
                    args=[scheduled_job.id],
                    id=job_id,
                    name=scheduled_job.job_name,
                    replace_existing=True,
                )
                logger.info(
                    f"Scheduled job '{scheduled_job.job_name}' "
                    f"with cron '{scheduled_job.cron_expression}'"
                )
                return True
            except Exception as e:
                logger.error(
                    f"Failed to schedule job '{scheduled_job.job_name}': {e}", exc_info=True
                )
                return False
        else:
            logger.info(f"Job '{scheduled_job.job_name}' is disabled, not scheduling")
            return True


def get_scheduler():
    """Get the global scheduler instance."""
    return _scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("Scheduler shutdown complete")
