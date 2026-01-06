"""
Test-Accounts erstellen für Shopping Points Optimiser
"""

from app import app
from spo.extensions import db
from spo.models import User


def create_test_accounts():
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(username="admin").first()
        if existing_admin:
            print("Admin-Account existiert bereits.")
        else:
            admin = User(username="admin", email="admin@example.com", role="admin", status="active")
            admin.set_password("admin123")
            db.session.add(admin)
            print("OK Admin-Account erstellt (admin / admin123)")

        # Contributor
        existing_contrib = User.query.filter_by(username="contributor").first()
        if existing_contrib:
            print("Contributor-Account existiert bereits.")
        else:
            contributor = User(
                username="contributor",
                email="contributor@example.com",
                role="contributor",
                status="active",
            )
            contributor.set_password("contrib123")
            db.session.add(contributor)
            print("OK Contributor-Account erstellt (contributor / contrib123)")

        # Regular user
        existing_user = User.query.filter_by(username="testuser").first()
        if existing_user:
            print("Testuser-Account existiert bereits.")
        else:
            user = User(
                username="testuser", email="testuser@example.com", role="user", status="active"
            )
            user.set_password("user123")
            db.session.add(user)
            print("OK User-Account erstellt (testuser / user123)")

        # Viewer (unregistered)
        existing_viewer = User.query.filter_by(username="viewer").first()
        if existing_viewer:
            print("Viewer-Account existiert bereits.")
        else:
            viewer = User(
                username="viewer", email="viewer@example.com", role="viewer", status="active"
            )
            viewer.set_password("viewer123")
            db.session.add(viewer)
            print("OK Viewer-Account erstellt (viewer / viewer123)")

        db.session.commit()
        print("OK Test-Accounts erfolgreich erstellt!")
        print("\nZugangs-Informationen:")
        print("-" * 50)
        print("Admin:       admin / admin123")
        print("Contributor: contributor / contrib123")
        print("User:        testuser / user123")
        print("Viewer:      viewer / viewer123")
        print("-" * 50)


if __name__ == "__main__":
    create_test_accounts()
