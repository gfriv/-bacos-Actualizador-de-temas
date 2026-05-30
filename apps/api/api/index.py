import os
from pathlib import Path

from alembic.config import Config

from alembic import command


def run_migrations_once() -> None:
    if os.getenv("RUN_MIGRATIONS_ON_STARTUP", "false").lower() != "true":
        return
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    command.upgrade(config, "head")


run_migrations_once()

from app.main import app as app  # noqa: E402,F401
