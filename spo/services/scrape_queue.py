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
