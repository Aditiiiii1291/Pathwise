import pytest
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable
from app.core.database import normalize_database_url, get_engine_kwargs, Base
import app.models  # Ensure all models are registered with Base.metadata


def test_normalize_database_url():
    """Verify URL normalization handles Render postgres:// prefix and default fallbacks."""
    # SQLite
    assert normalize_database_url("sqlite:///./pathwise.db") == "sqlite:///./pathwise.db"
    assert normalize_database_url("") == "sqlite:///./pathwise.db"
    assert normalize_database_url(None) == "sqlite:///./pathwise.db"

    # Render legacy postgres:// format
    render_url = "postgres://pathwise_user:SecretPass123@dpg-host.oregon-postgres.render.com/pathwise_db"
    expected = "postgresql://pathwise_user:SecretPass123@dpg-host.oregon-postgres.render.com/pathwise_db"
    assert normalize_database_url(render_url) == expected

    # Standard PostgreSQL URL
    pg_url = "postgresql://user:pass@localhost:5432/mydb"
    assert normalize_database_url(pg_url) == pg_url

    # Leading/trailing whitespace
    assert normalize_database_url("  postgres://user:pass@host/db  ") == "postgresql://user:pass@host/db"


def test_get_engine_kwargs_isolation():
    """Verify that SQLite-specific connect_args are NEVER applied to PostgreSQL."""
    # SQLite kwargs
    sqlite_kwargs = get_engine_kwargs("sqlite:///./pathwise.db")
    assert "connect_args" in sqlite_kwargs
    assert sqlite_kwargs["connect_args"].get("check_same_thread") is False

    # PostgreSQL kwargs
    pg_kwargs = get_engine_kwargs("postgresql://user:pass@host:5432/db")
    assert "connect_args" not in pg_kwargs
    assert pg_kwargs.get("pool_pre_ping") is True

    # Render-style normalized URL kwargs
    render_kwargs = get_engine_kwargs("postgresql://user:pass@dpg-host.render.com/db")
    assert "connect_args" not in render_kwargs
    assert render_kwargs.get("pool_pre_ping") is True


def test_model_metadata_ddl_compilation_postgresql():
    """
    Verify all SQLAlchemy models in Base.metadata can compile to valid CREATE TABLE DDL
    under both PostgreSQL and SQLite dialects without dialect compilation errors.
    """
    pg_dialect = postgresql.dialect()
    sqlite_dialect = sqlite.dialect()

    tables = Base.metadata.sorted_tables
    assert len(tables) >= 11  # All models registered

    for table in tables:
        # Check SQLite DDL compilation
        sqlite_ddl = str(CreateTable(table).compile(dialect=sqlite_dialect))
        assert f"CREATE TABLE {table.name}" in sqlite_ddl

        # Check PostgreSQL DDL compilation
        pg_ddl = str(CreateTable(table).compile(dialect=pg_dialect))
        assert f"CREATE TABLE {table.name}" in pg_ddl
