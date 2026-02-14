import os
import uuid

from rq import Queue
from rq.job import Job

from spo.services.scrape_queue_config import get_redis_connection

DEFAULT_QUEUE_NAME = "scraper"


def enqueue_scrape_job(program: str, *, requested_by: str | None = None) -> str:
    """Enqueue a scrape job in Redis and return the job id."""
    queue_name = os.environ.get("SCRAPER_QUEUE_NAME", DEFAULT_QUEUE_NAME)
    redis_conn = get_redis_connection()

    run_id = str(uuid.uuid4())
    job: Job = Queue(queue_name, connection=redis_conn).enqueue(
        "spo.worker_tasks.run_scrape_job",
        program=program,
        run_id=run_id,
        requested_by=requested_by,
        job_timeout=int(os.environ.get("SCRAPER_JOB_TIMEOUT", "3600")),
    )
    return job.id


def enqueue_import_job(payload: dict, *, requested_by: str | None = None) -> str:
    """Enqueue a consolidated import job in Redis and return the job id."""
    queue_name = os.environ.get("SCRAPER_QUEUE_NAME", DEFAULT_QUEUE_NAME)
    redis_conn = get_redis_connection()

    run_id = str(uuid.uuid4())
    job: Job = Queue(queue_name, connection=redis_conn).enqueue(
        "spo.worker_tasks.run_import_job",
        import_payload=payload,
        run_id=run_id,
        requested_by=requested_by,
        job_timeout=int(os.environ.get("SCRAPER_JOB_TIMEOUT", "3600")),
    )
    return job.id


def enqueue_coupon_import_job(payload: dict, *, requested_by: str | None = None) -> str:
    """Enqueue a consolidated coupon import job in Redis and return the job id."""
    queue_name = os.environ.get("SCRAPER_QUEUE_NAME", DEFAULT_QUEUE_NAME)
    redis_conn = get_redis_connection()

    run_id = str(uuid.uuid4())
    job: Job = Queue(queue_name, connection=redis_conn).enqueue(
        "spo.worker_tasks.run_coupon_import_job",
        import_payload=payload,
        run_id=run_id,
        requested_by=requested_by,
        job_timeout=int(os.environ.get("SCRAPER_JOB_TIMEOUT", "3600")),
    )
    return job.id


def get_rq_job_status(job_id: str) -> dict | None:
    """Fetch basic status information for an RQ job by id.

    Returns a dict compatible with `job_queue.Job.to_dict()` shape where possible,
    or None if the job cannot be found.
    """
    redis_conn = get_redis_connection()
    try:
        rq_job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return None

    # Map RQ statuses to our simpler statuses
    status_map = {
        "queued": "queued",
        "started": "running",
        "finished": "completed",
        "failed": "failed",
    }
    raw_status = rq_job.get_status()
    status = status_map.get(raw_status, raw_status)

    # Try to read progress and messages from job.meta if set by the worker
    meta = getattr(rq_job, "meta", {}) or {}
    progress_percent = int(meta.get("progress_percent", meta.get("progress", 0))) if meta else 0
    messages = meta.get("messages", []) if meta else []

    info = {
        "id": rq_job.id,
        "status": status,
        "progress_percent": progress_percent,
        "messages": messages,
        "created_at": (
            getattr(rq_job, "created_at", None).isoformat()
            if getattr(rq_job, "created_at", None)
            else None
        ),
        "started_at": (
            getattr(rq_job, "started_at", None).isoformat()
            if getattr(rq_job, "started_at", None)
            else None
        ),
        "ended_at": (
            getattr(rq_job, "ended_at", None).isoformat()
            if getattr(rq_job, "ended_at", None)
            else None
        ),
        "kwargs": getattr(rq_job, "kwargs", {}) or {},
    }

    return info
