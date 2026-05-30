from app.core.database_url import normalize_database_url


def test_normalize_render_postgres_url() -> None:
    assert (
        normalize_database_url("postgres://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )


def test_normalize_plain_postgresql_url() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@example.com:5432/db")
        == "postgresql+psycopg://user:pass@example.com:5432/db"
    )


def test_keep_driver_specific_and_sqlite_urls() -> None:
    assert normalize_database_url("postgresql+psycopg://user:pass@example.com/db") == (
        "postgresql+psycopg://user:pass@example.com/db"
    )
    assert normalize_database_url("sqlite:///./abacos.db") == "sqlite:///./abacos.db"
