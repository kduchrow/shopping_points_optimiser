"""Tests for scheduler functionality."""


from spo.models import ScheduledJob
from spo.services.scheduler import JOB_REGISTRY, register_job_type


def test_create_scheduled_job(app, session):
    """Test creating a scheduled job."""
    with app.app_context():
        job = ScheduledJob(
            job_name="test_job",
            job_type="deduplication",
            cron_expression="0 2 * * *",
            enabled=True,
        )
        session.add(job)
        session.commit()

        retrieved = ScheduledJob.query.filter_by(job_name="test_job").first()
        assert retrieved is not None
        assert retrieved.job_type == "deduplication"
        assert retrieved.cron_expression == "0 2 * * *"
        assert retrieved.enabled is True


def test_scheduled_job_defaults(app, session):
    """Test scheduled job default values."""
    with app.app_context():
        job = ScheduledJob(
            job_name="test_job_2",
            job_type="cleanup",
            cron_expression="0 3 * * *",
        )
        session.add(job)
        session.commit()

        retrieved = ScheduledJob.query.filter_by(job_name="test_job_2").first()
        assert retrieved.enabled is False  # default
        assert retrieved.last_run_at is None
        assert retrieved.last_run_status is None


def test_register_job_type():
    """Test registering a job type."""

    def dummy_job():
        pass

    register_job_type("test_type", dummy_job)
    assert "test_type" in JOB_REGISTRY
    assert JOB_REGISTRY["test_type"] == dummy_job


def test_admin_create_scheduled_job_route(app, client, session):
    """Test creating scheduled job via admin route."""
    with app.app_context():
        # Create admin user
        from spo.models import User

        admin = User()
        admin.username = "admin_test"
        admin.email = "admin@test.com"
        admin.role = "admin"
        admin.set_password("password")
        session.add(admin)
        session.commit()

        # Login as admin
        client.post("/login", data={"username": "admin_test", "password": "password"})

        # Create scheduled job
        response = client.post(
            "/admin/scheduled_jobs/create",
            data={
                "job_name": "test_scheduled_job",
                "job_type": "deduplication",
                "cron_expression": "0 2 * * *",
                "enabled": "on",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        job = ScheduledJob.query.filter_by(job_name="test_scheduled_job").first()
        assert job is not None
        assert job.enabled is True


def test_admin_toggle_scheduled_job(app, client, session):
    """Test toggling scheduled job enabled status."""
    with app.app_context():
        # Create admin user
        from spo.models import User

        admin = User()
        admin.username = "admin_test2"
        admin.email = "admin2@test.com"
        admin.role = "admin"
        admin.set_password("password")
        session.add(admin)
        session.commit()

        # Create scheduled job
        job = ScheduledJob(
            job_name="toggle_test",
            job_type="deduplication",
            cron_expression="0 2 * * *",
            enabled=True,
        )
        session.add(job)
        session.commit()
        job_id = job.id

        # Login as admin
        client.post("/login", data={"username": "admin_test2", "password": "password"})

        # Toggle job
        response = client.post(f"/admin/scheduled_jobs/{job_id}/toggle", follow_redirects=True)

        assert response.status_code == 200
        job = ScheduledJob.query.get(job_id)
        assert job.enabled is False

        # Toggle again
        client.post(f"/admin/scheduled_jobs/{job_id}/toggle", follow_redirects=True)
        job = ScheduledJob.query.get(job_id)
        assert job.enabled is True
