"""Setup configuration for Shopping Points Optimiser."""

from setuptools import find_packages, setup

setup(
    name="shopping-points-optimiser",
    version="1.0.0",
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
