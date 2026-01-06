"""Setup configuration for Shopping Points Optimiser."""

from pathlib import Path

from setuptools import find_packages, setup

# Read version from spo/version.py
version_file = Path(__file__).parent / "spo" / "version.py"
version_dict = {}
with open(version_file) as f:
    exec(f.read(), version_dict)
__version__ = version_dict["__version__"]

setup(
    name="shopping-points-optimiser",
    version=__version__,
    description="Shopping Points Optimizer - maximize cashback and bonus points",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "Flask>=3.0",
        "Flask-SQLAlchemy>=3.1",
        "Flask-Login>=0.6",
        "requests>=2.30",
        "beautifulsoup4>=4.12",
        "playwright>=1.40",
        "alembic>=1.12",
        "psycopg2-binary>=2.9",
        "gunicorn>=20.0",
    ],
)
