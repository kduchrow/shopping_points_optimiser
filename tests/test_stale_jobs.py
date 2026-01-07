"""
Test for cleaning up stale job runs on app startup.
"""

from flask import Flask

from spo import create_app
from spo.extensions import db
from spo.models import ScheduledJob, ScheduledJobRun


def test_stale_jobs_cleaned_on_startup(app: Flask):
    """Test that running/queued jobs are marked as failed when app starts."""
    with app.app_context():
        # Create a test scheduled job
        job = ScheduledJob(
            job_name="Test Job",
            job_type="test_job",
            cron_expression="0 * * * *",
            enabled=True,
        )
        db.session.add(job)
        db.session.commit()

        # Create job runs with different statuses
        runs = [
            ScheduledJobRun(scheduled_job_id=job.id, status="running", message="Was running"),
            ScheduledJobRun(scheduled_job_id=job.id, status="queued", message="Was queued"),
            ScheduledJobRun(
                scheduled_job_id=job.id, status="success", message="Completed successfully"
            ),
            ScheduledJobRun(scheduled_job_id=job.id, status="failed", message="Already failed"),
        ]
        for run in runs:
            db.session.add(run)
        db.session.commit()

        # Store the IDs
        running_id = runs[0].id
        queued_id = runs[1].id
        success_id = runs[2].id
        failed_id = runs[3].id

        # Simulate app restart by creating a new app instance
        # This will trigger the cleanup logic in create_app
        new_app = create_app(start_jobs=False, run_seed=False)

        with new_app.app_context():
            # Check that running and queued jobs are now failed
            running_run = db.session.get(ScheduledJobRun, running_id)
            assert running_run is not None and running_run.status == "failed"
            assert "Container restarted" in running_run.message

            queued_run = db.session.get(ScheduledJobRun, queued_id)
            assert queued_run is not None and queued_run.status == "failed"
            assert "Container restarted" in queued_run.message

            # Check that success and failed jobs are unchanged
            success_run = db.session.get(ScheduledJobRun, success_id)
            assert success_run is not None and success_run.status == "success"
            assert success_run.message == "Completed successfully"

            failed_run = db.session.get(ScheduledJobRun, failed_id)
            assert failed_run is not None and failed_run.status == "failed"
            assert failed_run.message == "Already failed"

        # Cleanup
        with app.app_context():
            ScheduledJobRun.query.filter_by(scheduled_job_id=job.id).delete()
            ScheduledJob.query.filter_by(id=job.id).delete()
            db.session.commit()
