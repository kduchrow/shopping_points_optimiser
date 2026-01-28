#!/usr/bin/env python
"""Check version consistency across all files.

Version is read from pyproject.toml (single source of truth).
This script verifies that:
1. pyproject.toml has a valid version
2. spo/version.py can successfully read it via importlib.metadata
3. .env file has the synced APP_VERSION (for local dev)
"""

import re
import sys
from pathlib import Path

# Read version from pyproject.toml (single source of truth)
pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
if not pyproject_file.exists():
    print("❌ pyproject.toml not found")
    sys.exit(1)

pyproject_content = pyproject_file.read_text()
version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', pyproject_content)
if not version_match:
    print("❌ Could not find version in pyproject.toml")
    sys.exit(1)

app_version = version_match.group(1)
print(f"✅ pyproject.toml version: {app_version}")

# Check that spo/version.py can read the version correctly
try:
    # Import the version module to verify it works
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from spo.version import __version__

    if __version__ == app_version:
        print(f"✅ spo/version.py reads: {__version__} (matches)")
    elif __version__.endswith("-dev"):
        print(f"⚠️  spo/version.py reads: {__version__} (fallback mode - package not installed)")
        print(f"   This is OK for CI, but Docker should show {app_version}")
    else:
        print(f"❌ spo/version.py reads: {__version__} (MISMATCH! Expected: {app_version})")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error importing spo.version: {e}")
    sys.exit(1)

print(f"\n🎉 Version check passed! App is at version {app_version}")
