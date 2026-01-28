#!/usr/bin/env python3
"""Sync version from pyproject.toml to .env for local development.

This ensures .env always has the correct version from the single source of truth
(pyproject.toml). Run this before 'docker compose up'.

Usage:
    python scripts/sync_version.py
    # or from project root:
    python -m scripts.sync_version
"""

import re
import sys
from pathlib import Path


def get_version_from_pyproject():
    """Extract version from pyproject.toml."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject}")

    with open(pyproject) as f:
        content = f.read()

    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def sync_env_version(version):
    """Update or create APP_VERSION in .env file."""
    env_file = Path(__file__).parent.parent / ".env"

    if env_file.exists():
        with open(env_file) as f:
            lines = f.readlines()

        # Find and replace existing APP_VERSION line
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("APP_VERSION="):
                new_lines.append(f"APP_VERSION={version}\n")
                updated = True
            else:
                new_lines.append(line)

        # If APP_VERSION wasn't found, add it at the top
        if not updated:
            new_lines.insert(0, f"APP_VERSION={version}\n")

        with open(env_file, "w") as f:
            f.writelines(new_lines)

        print(f"✅ Updated {env_file} with version {version}")
    else:
        # Create .env with APP_VERSION
        with open(env_file, "w") as f:
            f.write(f"APP_VERSION={version}\n")
        print(f"✅ Created {env_file} with version {version}")


if __name__ == "__main__":
    try:
        version = get_version_from_pyproject()
        print(f"📖 Found version in pyproject.toml: {version}")
        sync_env_version(version)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
