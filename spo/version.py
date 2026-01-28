"""Version information for Shopping Points Optimiser.

Version is read from pyproject.toml (single source of truth).
Update version only in pyproject.toml [project] section.
"""

try:
    from importlib.metadata import version

    __version__ = version("shopping-points-optimiser")
except Exception:
    # Fallback for development (package not installed yet)
    __version__ = "0.3.1-dev"
