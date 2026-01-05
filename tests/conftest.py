import pytest
from flask import Flask

from spo.extensions import db


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="test-secret",
    )
    db.init_app(app)

    with app.app_context():
        from spo import models  # noqa: F401  Ensure models are registered
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        yield db.session
