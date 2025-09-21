"""Integration test: verify DB connectivity and a trivial query.

Run with: pytest -m integration -q
Requires DATABASE_URL to point to a reachable PostgreSQL instance.
"""

import os

import pytest
from _pytest.monkeypatch import MonkeyPatch
from dotenv import load_dotenv
from sqlalchemy import text

from telegram_antilurk_bot.database.session import get_engine

# Load environment variables from .env file
load_dotenv()


@pytest.mark.integration
def test_database_connect_and_simple_query() -> None:
    """Connect to the database and execute a trivial SELECT."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        pytest.fail("DATABASE_URL not set - required for integration tests")

    # Skip if this is a localhost/test URL (not an actual external server)
    if "localhost" in db_url or "127.0.0.1" in db_url or "test:test@" in db_url:
        pytest.skip("DATABASE_URL points to localhost/test - use real external database")

    # Integration test should fail if database is not accessible
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("select 1 as a")).first()
        assert result is not None
        # Access by column name via mapping for portability
        assert result._mapping["a"] == 1

        print("✅ Database connectivity test passed - simple query successful")


def test_database_engine_creation(monkeypatch: MonkeyPatch) -> None:
    """Test that database engine can be created without connection."""
    # Set a dummy DATABASE_URL for testing
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")

    engine = get_engine()
    assert engine is not None
    assert "postgresql" in str(engine.url)


def test_external_database_connection() -> None:
    """Test connection to external database using environment configuration."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        pytest.fail("DATABASE_URL not set - required for integration tests")

    # Skip if this is a localhost/test URL (not an actual external server)
    if "localhost" in db_url or "127.0.0.1" in db_url or "test:test@" in db_url:
        pytest.skip("DATABASE_URL points to localhost/test - use real external database")

    # Integration test should fail if database is not accessible
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("select version()")).first()
        assert result is not None
        version_info = result[0]
        print(f"✅ Connected successfully to: {version_info}")

        # Test basic database operations
        calc_result = conn.execute(text("select 1 + 1 as result")).first()
        assert calc_result is not None
        assert calc_result._mapping["result"] == 2

        # Test server info
        server_info = conn.execute(text("""
            SELECT
                current_database() as db_name,
                current_user as username,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port
        """)).first()

        assert server_info is not None
        print(f"✅ Database: {server_info.db_name}")
        print(f"✅ User: {server_info.username}")
        print(f"✅ Server: {server_info.server_ip}:{server_info.server_port}")


def test_database_connection_resilience(monkeypatch: MonkeyPatch) -> None:
    """Test database connection with IP fallback if hostname fails."""
    original_db_url = os.environ.get("DATABASE_URL")
    if not original_db_url:
        pytest.fail("DATABASE_URL not set - required for integration tests")

    # Skip if this is a localhost/test URL
    if "localhost" in original_db_url or "127.0.0.1" in original_db_url or "test:test@" in original_db_url:
        pytest.skip("DATABASE_URL points to localhost/test - use real external database")

    # Test original URL first
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("select version()")).first()
            print(f"✅ Original DATABASE_URL works: {result[0][:50]}...")
            return  # Success with original URL
    except Exception as e:
        if "could not translate host name" not in str(e).lower():
            # If it's not a DNS issue, don't try IP fallback
            raise

    # If hostname resolution failed, try IP fallback (only for known hosts)
    if "halob" in original_db_url:
        ip_url = original_db_url.replace("halob", "192.168.86.31")
        monkeypatch.setenv("DATABASE_URL", ip_url)

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("select version()")).first()
            print(f"✅ IP fallback works: {result[0][:50]}...")
            print("ℹ️  Consider updating DNS or using IP in DATABASE_URL")
    else:
        pytest.fail("Hostname resolution failed and no known IP fallback available")


def test_connection_with_custom_database_url(monkeypatch: MonkeyPatch) -> None:
    """Test connection using environment variable if provided."""
    db_url = os.environ.get("TEST_DATABASE_URL")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL not set - provide a connection string to test external database")

    monkeypatch.setenv("DATABASE_URL", db_url)

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("select version()")).first()
        assert result is not None
        print(f"✅ Connected with custom URL to: {result[0]}")

        # Test basic operations
        conn.execute(text("select 1"))
        print("✅ Basic query execution works")
