#!/usr/bin/env python
"""Check version consistency across all files."""

import json
import re
import sys
from pathlib import Path

# Read version from spo/version.py
version_file = Path(__file__).parent.parent / "spo" / "version.py"
version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_file.read_text())
if not version_match:
    print("❌ Could not find version in spo/version.py")
    sys.exit(1)

app_version = version_match.group(1)
print(f"✅ App Version (spo/version.py): {app_version}")

# Check package.json
package_json_file = Path(__file__).parent.parent / "package.json"
package_json = json.loads(package_json_file.read_text())
package_version = package_json.get("version")

if package_version == app_version:
    print(f"✅ package.json version: {package_version} (matches)")
else:
    print(f"❌ package.json version: {package_version} (MISMATCH! Expected: {app_version})")
    sys.exit(1)

# Check migration files
migrations_dir = Path(__file__).parent.parent / "migrations" / "versions"
migration_files = list(migrations_dir.glob("v*.py"))

if migration_files:
    latest_migration = sorted(migration_files)[-1]
    migration_content = latest_migration.read_text()

    # Extract revision from file
    revision_match = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', migration_content)
    if revision_match:
        migration_revision = revision_match.group(1)
        expected_revision = f"v{app_version.replace('.', '_')}"

        if migration_revision == expected_revision:
            print(f"✅ Latest migration revision: {migration_revision} (matches)")
        else:
            print(
                f"⚠️  Latest migration revision: {migration_revision} (Expected: {expected_revision})"
            )
    else:
        print(f"⚠️  Could not find revision in {latest_migration.name}")
else:
    print("⚠️  No migration files found")

print(f"\n🎉 All version checks passed! App is at version {app_version}")
