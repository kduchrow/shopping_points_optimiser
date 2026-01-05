"""
Background job queue for async scraper execution
"""
import threading
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Callable, Optional


class JobStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    def __init__(self, job_id: str, func: Callable, args=None, kwargs=None):
        self.id = job_id
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
        self.status = JobStatus.QUEUED
        self.progress = 0
        self.total_steps = 100
        self.messages: list[dict] = []
        self.result = None
        self.error: Optional[str] = None
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.thread: Optional[threading.Thread] = None
    
    def add_message(self, message: str):
        """Add a progress message"""
        self.messages.append({
            'timestamp': datetime.utcnow().isoformat(),
            'message': message
        })
    
    def set_progress(self, progress: int, total: Optional[int] = None):
        """Update progress"""
        self.progress = progress
        if total:
            self.total_steps = total
    
    def get_progress_percent(self) -> int:
        """Get progress as percentage"""
        if self.total_steps == 0:
            return 0
        return int((self.progress / self.total_steps) * 100)
    
    def to_dict(self):
        """Convert job to dictionary"""
        return {
            'id': self.id,
            'status': self.status.value,
            'progress': self.progress,
            'progress_percent': self.get_progress_percent(),
            'total_steps': self.total_steps,
            'messages': self.messages,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class JobQueue:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.queue: list = []
        self.lock = threading.Lock()
        self.worker_thread = None
        self.running = False
    
    def start(self):
        """Start the job queue worker"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
    
    def stop(self):
        """Stop the job queue worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _worker(self):
        """Worker thread that processes jobs"""
        while self.running:
            with self.lock:
                if self.queue:
                    job = self.queue.pop(0)
                else:
                    job = None
            
            if job:
                self._execute_job(job)
            else:
                # Sleep briefly to avoid busy waiting
                threading.Event().wait(0.1)
    
    def _execute_job(self, job: Job):
        """Execute a job in a separate thread"""
        job.thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        job.thread.start()
    
    def _run_job(self, job: Job):
        """Run a job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.add_message(f"Job started: {job.func.__name__}")
            
            # Execute the function with progress callback
            result = job.func(job, *job.args, **job.kwargs)
            
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = job.total_steps
            job.add_message("Job completed successfully")
        
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.add_message(f"Job failed: {str(e)}")
    
    def enqueue(self, func: Callable, args=None, kwargs=None) -> str:
        """Enqueue a job"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, func, args, kwargs)
        
        with self.lock:
            self.jobs[job_id] = job
            self.queue.append(job)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> list:
        """Get all jobs"""
        with self.lock:
            return list(self.jobs.values())
    
    def clear_old_jobs(self, max_age_hours: int = 24):
        """Clear completed jobs older than max_age_hours"""
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        with self.lock:
            to_remove = [
                job_id for job_id, job in self.jobs.items()
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                and job.completed_at is not None
                and job.completed_at.timestamp() < cutoff
            ]
            for job_id in to_remove:
                del self.jobs[job_id]


# Global job queue instance
job_queue = JobQueue()
