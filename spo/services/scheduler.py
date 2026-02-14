"""Job scheduler service for running periodic tasks."""

import logging
import threading
from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.exc import ObjectDeletedError

from spo.extensions import db
from spo.models import ScheduledJob, ScheduledJobRun, utcnow

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler = None

# Registry of available job types and their execution functions
JOB_REGISTRY = {}

# Track running jobs: {run_id: {'thread': Thread, 'start_time': float, 'cancel_requested': bool}}
RUNNING_JOBS = {}


def register_job_type(job_type: str, func):
    """Register a job type with its execution function.

    Args:
        job_type: Unique identifier for the job type (e.g., 'deduplication')
        func: Function to execute. Will be called with (job_id: int, **kwargs)
    """
    JOB_REGISTRY[job_type] = func
    logger.info(f"Registered job type: {job_type}")


class SimpleJob:
    """Simple job wrapper for inline execution (replaces RQ job object)."""

    def __init__(self, run_id: int):
        """Initialize job wrapper.

        Args:
            run_id: ID of the ScheduledJobRun record to update with messages
        """
        self.run_id = run_id
        self.messages = []

    def add_message(self, message: str):
        """Add a message to the job run log.

        Args:
            message: Message to add
        """
        # Check if cancellation was requested
        if self.run_id in RUNNING_JOBS and RUNNING_JOBS[self.run_id].get("cancel_requested"):
            raise InterruptedError("Job cancellation requested")

        self.messages.append(message)
        logger.info(f"Job {self.run_id}: {message}")
        # Update the run's message field with accumulated messages
        run = db.session.get(ScheduledJobRun, self.run_id)
        if run:
            run.message = " | ".join(self.messages)
            db.session.commit()

    def set_progress(self, current: int, total: int):
        """Set job progress (no-op for inline execution).

        Args:
            current: Current progress
            total: Total progress
        """
        # Check if cancellation was requested
        if self.run_id in RUNNING_JOBS and RUNNING_JOBS[self.run_id].get("cancel_requested"):
            raise InterruptedError("Job cancellation requested")

        pct = int((current / total) * 100) if total > 0 else 0
        logger.info(f"Job {self.run_id}: Progress {pct}%")


def _execute_scheduled_job(scheduled_job_id: int):
    """Execute a scheduled job and update its status.

    Args:
        scheduled_job_id: ID of the ScheduledJob database record
    """
    from spo import create_app

    app = create_app(start_jobs=False)

    with app.app_context():
        scheduled_job = db.session.get(ScheduledJob, scheduled_job_id)
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

        msg = "Enqueued from scheduler"
        run = ScheduledJobRun(
            scheduled_job_id=scheduled_job.id,
            status="queued",
            message=msg,
        )
        db.session.add(run)
        scheduled_job.last_run_at = utcnow()
        scheduled_job.last_run_status = "queued"
        scheduled_job.last_run_message = msg
        db.session.commit()

        try:
            # Execute in background thread to avoid blocking
            _run_scheduled_job_in_thread(scheduled_job.id, run.id, job_func)
        except Exception as e:
            logger.exception(f"Error executing scheduled job {scheduled_job.job_name}")
            run.status = "failed"
            run.message = str(e)[:500]
            scheduled_job.last_run_at = utcnow()
            scheduled_job.last_run_status = "failed"
            scheduled_job.last_run_message = run.message
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
        try:
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
        except Exception as e:
            logger.warning(
                f"Could not load scheduled jobs from database (tables may not exist yet): {e}"
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
        scheduled_job = db.session.get(ScheduledJob, scheduled_job_id)
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


def _run_scheduled_job(job, scheduled_job_id: int, run_id: int, job_func):
    """Wrapper to run the actual job and record status."""
    from spo import create_app

    app = create_app(start_jobs=False, run_seed=False)

    with app.app_context():
        scheduled_job = db.session.get(ScheduledJob, scheduled_job_id)
        run = db.session.get(ScheduledJobRun, run_id)

        if not run:
            logger.error(f"Scheduled run missing (run_id={run_id})")
            return

        # Capture job name early in case the DB row is deleted while running
        job_name = scheduled_job.job_name if scheduled_job else f"scheduled_job_{scheduled_job_id}"
        logger.info(f"Starting scheduled job run {run_id} for job '{job_name}'")

        status = "success"
        message = "Completed successfully"

        # Mark running
        run.status = "running"
        run.message = "Job started"
        db.session.commit()
        logger.info(f"Marked run {run_id} as running")

        try:
            # Create a simple job wrapper for inline execution
            job_wrapper = SimpleJob(run_id)
            # Call job function with job wrapper
            result = job_func(job_wrapper)
            logger.info(f"Job function completed with result: {result}")
        except Exception as e:  # noqa: BLE001
            status = "failed"
            message = str(e)[:500]
            logger.exception(f"Scheduled job {job_name} failed")
            # Update run state
            try:
                run.status = status
                run.message = message
                db.session.commit()
            except (ObjectDeletedError, NoResultFound):
                logger.warning(
                    f"Run {run_id} row deleted while handling failure; skipping run update"
                )

            # Try to update scheduled_job summary fields if it still exists
            try:
                sj = db.session.get(ScheduledJob, scheduled_job_id)
                if sj:
                    sj.last_run_at = utcnow()
                    sj.last_run_status = status
                    sj.last_run_message = message
                    db.session.commit()
            except (ObjectDeletedError, NoResultFound):
                logger.warning(
                    f"Scheduled job {scheduled_job_id} row missing when marking failure; skipping job summary update"
                )
            logger.error(f"Marked run {run_id} as failed (if record still present)")
        else:
            # Success path: update run and job summary but tolerate missing rows
            try:
                run.status = status
                run.message = message
                db.session.commit()
            except (ObjectDeletedError, NoResultFound):
                logger.warning(
                    f"Run {run_id} row deleted while marking success; skipping run update"
                )

            try:
                sj = db.session.get(ScheduledJob, scheduled_job_id)
                if sj:
                    sj.last_run_at = utcnow()
                    sj.last_run_status = status
                    sj.last_run_message = message
                    db.session.commit()
            except (ObjectDeletedError, NoResultFound):
                logger.warning(
                    f"Scheduled job {scheduled_job_id} row missing when marking success; skipping job summary update"
                )
            logger.info(f"Marked run {run_id} as success (if records still present)")


def _run_scheduled_job_in_thread(scheduled_job_id: int, run_id: int, job_func):
    """Start a scheduled job in a background thread.

    Args:
        scheduled_job_id: ID of the ScheduledJob
        run_id: ID of the ScheduledJobRun
        job_func: Job function to execute
    """

    def wrapper():
        try:
            _run_scheduled_job(None, scheduled_job_id, run_id, job_func)
        finally:
            # Clean up the job registry
            RUNNING_JOBS.pop(run_id, None)

    thread = threading.Thread(target=wrapper, daemon=True)
    RUNNING_JOBS[run_id] = {"thread": thread, "cancel_requested": False}
    thread.start()
    logger.info(f"Started job thread for run {run_id}")


def trigger_job_now(scheduled_job_id: int, ignore_enabled: bool = True, app=None):
    """Manually trigger a scheduled job immediately.

    Enqueues the job function via job_queue and records a run log entry.

    Args:
        scheduled_job_id: ID of the ScheduledJob to trigger
        ignore_enabled: If True, run even when job is disabled
        app: Optional Flask app to reuse; will create one if not provided
    Returns:
        Tuple (ok: bool, message: str)
    """
    if app is None:
        from spo import create_app

        app = create_app(start_jobs=False)

    with app.app_context():
        job = db.session.get(ScheduledJob, scheduled_job_id)
        if not job:
            return False, f"Job {scheduled_job_id} not found"

        if not ignore_enabled and not job.enabled:
            return False, f"Job '{job.job_name}' is disabled"

        job_func = JOB_REGISTRY.get(job.job_type)
        if not job_func:
            # record failed run
            run = ScheduledJobRun(
                scheduled_job_id=job.id,
                status="failed",
                message=f"Unknown job type: {job.job_type}",
            )
            db.session.add(run)
            job.last_run_at = datetime.now(UTC)
            job.last_run_status = "failed"
            job.last_run_message = run.message
            db.session.commit()
            return False, run.message

        try:
            run = ScheduledJobRun(
                scheduled_job_id=job.id,
                status="queued",
                message="Enqueued manually",
            )
            db.session.add(run)
            job.last_run_at = utcnow()
            job.last_run_status = "queued"
            job.last_run_message = run.message
            db.session.commit()

            # Execute in background thread to avoid blocking web server
            _run_scheduled_job_in_thread(job.id, run.id, job_func)
            return True, job.last_run_message
        except Exception as e:
            msg = str(e)[:500]
            run = ScheduledJobRun(
                scheduled_job_id=job.id,
                status="failed",
                message=msg,
            )
            db.session.add(run)
            job.last_run_at = datetime.now(UTC)
            job.last_run_status = "failed"
            job.last_run_message = msg
            db.session.commit()
            logger.exception(f"Error when manually triggering job '{job.job_name}'")
            return False, msg


def cancel_job_run(run_id: int) -> bool:
    """Cancel a running job.

    Args:
        run_id: ID of the ScheduledJobRun to cancel

    Returns:
        True if cancellation was requested, False if job not running
    """
    if run_id in RUNNING_JOBS:
        RUNNING_JOBS[run_id]["cancel_requested"] = True
        logger.info(f"Cancellation requested for run {run_id}")
        return True
    return False
