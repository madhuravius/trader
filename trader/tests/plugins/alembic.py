"""
Derived partially from this suggestion: https://stackoverflow.com/a/35394239

Will basically run migrations/teardown on test to ensure forward func. This will
do a teardown at the end, so use some degree of caution/sense with this file.
"""
from pathlib import Path

import alembic.config
from alembic import command

ROOT_PATH = Path(__file__).parent.parent.parent.parent
ALEMBIC_CFG = alembic.config.Config(ROOT_PATH / "alembic.ini")


def pytest_configure(config):
    command.upgrade(ALEMBIC_CFG, "head")


def pytest_unconfigure(config):
    command.downgrade(ALEMBIC_CFG, "base")
