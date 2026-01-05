import pytest

from spo import create_app
from spo.extensions import db


@pytest.fixture(scope="function")
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        yield db.session


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
