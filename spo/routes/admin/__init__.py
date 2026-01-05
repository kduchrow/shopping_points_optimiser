"""Admin route registration aggregator."""

from .core import register_admin_core
from .jobs import register_admin_jobs
from .shops import register_admin_shops
from .users import register_admin_users


def register_admin(app):
    register_admin_core(app)
    register_admin_jobs(app)
    register_admin_shops(app)
    register_admin_users(app)
    return app
