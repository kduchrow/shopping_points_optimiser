#!/usr/bin/env python3
"""Pre-deployment checks for database migration.

This script verifies that the server is safe to deploy the v0.2.0 migration.
It checks for potential issues that could cause deployment failures.

Usage:
    python scripts/pre_deployment_check.py
"""

import os
import sys

import sqlalchemy as sa
from sqlalchemy import inspect


def check_database_state():
    """Check if database is in a safe state for migration."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False

    try:
        engine = sa.create_engine(database_url)
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        print("=" * 70)
        print("DATABASE MIGRATION SAFETY CHECK")
        print("=" * 70)

        # Scenario 1: Fresh database (no tables except alembic_version)
        if len(existing_tables) <= 1 and "alembic_version" not in existing_tables:
            print("✅ Database appears to be fresh")
            print("   - Safe to deploy: v0.2.0 migration will create all tables")
            print("   - Risk level: LOW")
            return True

        # Scenario 2: Only alembic_version exists (migration marked but no tables)
        if existing_tables == ["alembic_version"]:
            print("⚠️  Database has alembic_version table but no app tables")
            print("   - This suggests a previous incomplete migration")
            print("   - Safe to deploy: Migration will create missing tables")
            print("   - Recommended: Review migration history")
            print("   - Risk level: MEDIUM")
            return True

        # Scenario 3: App tables exist (assume they're from previous version)
        app_tables = {
            "bonus_programs",
            "users",
            "shops",
            "shop_main",
            "shop_variants",
            "coupons",
            "proposals",
            "notifications",
        }
        existing_app_tables = app_tables & set(existing_tables)

        if existing_app_tables:
            print("⚠️  WARNING: Application tables already exist!")
            print(f"   - Found {len(existing_app_tables)} app tables:")
            for table in sorted(existing_app_tables):
                print(f"     • {table}")

            print()
            print("   ⚠️  IMPORTANT: v0.2.0 migration uses CREATE TABLE (not ALTER)")
            print("   - It WILL FAIL if tables already exist")
            print("   - This is a FRESH SCHEMA migration")
            print()
            print("   OPTIONS:")
            print("   1. If this is a v0.1.0 → v0.2.0 upgrade:")
            print("      - You need an INCREMENTAL migration (v0.1.0_to_v0.2.0)")
            print("      - NOT a fresh schema migration")
            print("   2. If this is a fresh deployment:")
            print("      - Drop all tables and alembic_version")
            print("      - Then deploy with docker-compose up (will create fresh)")
            print()
            print("   Risk level: CRITICAL - DO NOT DEPLOY WITHOUT ACTION")
            return False

        print("✅ Database is in unknown but safe state")
        print("   - Found tables:", ", ".join(sorted(existing_tables)))
        print("   - Risk level: LOW")
        return True

    except Exception as e:
        print("❌ ERROR: Failed to check database")
        print(f"   {e}")
        return False


def check_migration_file():
    """Verify migration file is properly configured."""
    print("\n" + "=" * 70)
    print("MIGRATION FILE CHECK")
    print("=" * 70)

    migration_file = "migrations/versions/v0_2_0_initial_schema.py"

    if not os.path.exists(migration_file):
        print(f"❌ ERROR: Migration file not found: {migration_file}")
        return False

    with open(migration_file) as f:
        content = f.read()

    checks = {
        "Has upgrade() function": "def upgrade()" in content,
        "Has downgrade() function": "def downgrade()" in content,
        "Creates bonus_programs table": "op.create_table(" in content,
        "Has proper revision ID": 'revision = "v0_2_0"' in content,
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        all_passed = all_passed and result

    if all_passed:
        print("\n✅ Migration file is properly configured")
    else:
        print("\n❌ Migration file has issues")

    return all_passed


def main():
    """Run all pre-deployment checks."""
    print("\n🔍 Running pre-deployment checks for v0.2.0 migration\n")

    checks = [
        ("Database State", check_database_state),
        ("Migration File", check_migration_file),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            results.append((check_name, False))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n✅ All checks passed - Safe to deploy")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed - Review above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
