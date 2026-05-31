from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text

from alembic import context
from app.core.config import settings
from app.core.database_url import normalize_database_url
from app.db import models  # noqa: F401
from app.db.base import Base

config = context.config
database_url = normalize_database_url(settings.database_url)
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _normalize_legacy_revision_ids(connection) -> None:
    legacy_pairs = {
        "0003_merge_report_types_and_file_blobs": "0003_merge_reports_files",
        "0004_evidence_quality_document_versions": "0004_evidence_quality_docs",
    }
    try:
        connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
    except Exception:
        connection.rollback()
        return
    for old_revision, new_revision in legacy_pairs.items():
        connection.execute(
            text("UPDATE alembic_version SET version_num = :new WHERE version_num = :old"),
            {"old": old_revision, "new": new_revision},
        )
    connection.commit()


def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _normalize_legacy_revision_ids(connection)
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
