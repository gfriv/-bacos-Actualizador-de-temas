def normalize_database_url(database_url: str) -> str:
    """Return a SQLAlchemy URL compatible with the installed PostgreSQL driver."""
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return database_url
