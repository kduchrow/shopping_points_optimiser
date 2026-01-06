"""
Reset the SQLite database: drop all tables, recreate schema, and seed test accounts.
Usage:
  python reset_db.py
"""

import create_test_accounts

from app import app, db


def reset_db():
    with app.app_context():
        print("Dropping all tables ...", flush=True)
        db.drop_all()
        print("Creating tables ...", flush=True)
        db.create_all()
        print("Seeding test accounts ...", flush=True)
        create_test_accounts.create_test_accounts()
        print("Done. You can now start the server.")


if __name__ == "__main__":
    reset_db()
