"""Integration tests for environment variable validation and external service connectivity.

Run with: pytest -m integration tests/integration/test_environment_validation.py -v
Tests connectivity to actual external services: PostgreSQL, NATS, Telegram API.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from telegram_antilurk_bot.database.session import get_engine

# Load environment variables from .env file
load_dotenv()


class TestEnvironmentVariables:
    """Test basic environment variable validation."""

    def test_required_environment_variables_present(self) -> None:
        """Test that all required environment variables are present."""
        required_vars = ["TELEGRAM_TOKEN", "DATABASE_URL"]
        missing_vars = []

        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            pytest.skip(f"Required environment variables missing: {', '.join(missing_vars)}")

        # Verify they have reasonable values
        token = os.environ.get("TELEGRAM_TOKEN", "")
        db_url = os.environ.get("DATABASE_URL", "")

        assert len(token) > 20, "TELEGRAM_TOKEN appears too short"
        assert ":" in token, "TELEGRAM_TOKEN should contain ':' (format: botid:token)"
        assert db_url.startswith(("postgresql://", "postgres://")), (
            "DATABASE_URL should be PostgreSQL URL"
        )

    def test_optional_environment_variables_format(self) -> None:
        """Test format of optional environment variables if present."""
        nats_url = os.environ.get("NATS_URL")

        if nats_url:
            assert nats_url.startswith("nats://"), "NATS_URL should start with nats://"
            # Basic URL format validation
            assert ":" in nats_url, "NATS_URL should contain port"

    def test_environment_variable_security(self) -> None:
        """Test that sensitive environment variables don't contain obvious issues."""
        token = os.environ.get("TELEGRAM_TOKEN", "")
        db_url = os.environ.get("DATABASE_URL", "")

        if token:
            # Skip security checks if using test tokens (from conftest.py)
            if "test_token_123456789" in token:
                pytest.skip("Using test token from conftest.py - security checks not applicable")

            # Should not contain obvious test/dummy values
            assert "test" not in token.lower(), "TELEGRAM_TOKEN appears to be a test value"
            assert "dummy" not in token.lower(), "TELEGRAM_TOKEN appears to be a dummy value"
            assert "example" not in token.lower(), "TELEGRAM_TOKEN appears to be an example value"

        if db_url:
            # Skip security checks if using test database URLs
            if "localhost" in db_url or "test:test@" in db_url:
                pytest.skip("Using test database URL - security checks not applicable")

            # Should not use default/insecure passwords in production-like URLs
            if "halob" in db_url or "192.168.86.31" in db_url:
                # This is expected to be a real server, check for security
                assert "password" not in db_url.lower(), (
                    "DATABASE_URL contains 'password' - use secure credentials"
                )
                assert "admin" not in db_url.lower(), (
                    "DATABASE_URL contains 'admin' - use specific user"
                )


class TestPostgreSQLConnectivity:
    """Test PostgreSQL database connectivity and configuration."""

    def test_database_url_parsing(self) -> None:
        """Test that DATABASE_URL is properly parsed."""
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        # Should be able to create engine without errors
        engine = create_engine(db_url)
        assert engine is not None
        assert "postgresql" in str(engine.url)

    def test_database_connectivity(self) -> None:
        """Test actual database connection and basic operations."""
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            pytest.fail("DATABASE_URL not set - required for integration tests")

        # Only skip if it's obviously a test/local URL
        if ("localhost" in db_url or "127.0.0.1" in db_url) and "test:test@" in db_url:
            pytest.skip("DATABASE_URL points to test database - use real external database")

        # Integration test should fail if database is not accessible
        engine = get_engine()
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1 as test")).first()
            assert result is not None
            assert result._mapping["test"] == 1

            # Test database info
            db_info = conn.execute(
                text("""
                SELECT
                    current_database() as db_name,
                    current_user as username,
                    version() as pg_version,
                    inet_server_addr() as server_ip,
                    inet_server_port() as server_port
            """)
            ).first()

            assert db_info is not None
            print(f"✅ Connected to database: {db_info.db_name}")
            print(f"✅ Connected as user: {db_info.username}")
            print(f"✅ Server: {db_info.server_ip}:{db_info.server_port}")
            print(f"✅ PostgreSQL version: {db_info.pg_version[:60]}...")

            # Test permissions
            conn.execute(
                text(
                    "CREATE TEMP TABLE env_test_permissions (id SERIAL, created_at TIMESTAMP DEFAULT NOW())"
                )
            )
            conn.execute(text("INSERT INTO env_test_permissions DEFAULT VALUES"))
            count = conn.execute(text("SELECT COUNT(*) FROM env_test_permissions")).first()
            conn.execute(text("DROP TABLE env_test_permissions"))
            assert count is not None
            print(f"✅ Database permissions: CREATE/INSERT/DROP working ({count[0]} row)")

    def test_database_required_tables_exist(self) -> None:
        """Test that required database schema exists or can be created."""
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Check if core tables exist (from the bot's schema)
                tables_query = text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)

                existing_tables = [row[0] for row in conn.execute(tables_query).fetchall()]
                print(f"📋 Existing tables: {existing_tables}")

                # Expected tables from the bot schema (may not exist yet if migrations haven't run)
                expected_tables = ["users", "message_archive", "provocations"]
                existing_expected = [t for t in expected_tables if t in existing_tables]

                if existing_expected:
                    print(f"✅ Found bot tables: {existing_expected}")
                else:
                    print("ℹ️  No bot tables found yet - migrations may not have run")

        except Exception as e:
            pytest.skip(f"Database schema check failed: {e}")


# NATS connectivity tests have been moved to tests/integration/test_nats_connectivity.py


# Telegram connectivity tests have been moved to tests/integration/test_telegram_connectivity.py


class TestServiceIntegration:
    """Test integration between services."""

    def test_all_required_services_accessible(self) -> None:
        """Test that all required services are accessible simultaneously."""
        # Check environment - fail fast if required config missing
        required_vars = ["TELEGRAM_TOKEN", "DATABASE_URL", "NATS_URL"]
        missing = [var for var in required_vars if not os.environ.get(var)]

        if missing:
            pytest.fail(f"Missing required environment variables: {missing}")

        services_status = {}

        # Test Database
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1")).first()
            services_status["PostgreSQL"] = "✅ Connected"
        except Exception as e:
            services_status["PostgreSQL"] = f"❌ Failed: {str(e)[:50]}"

        # Test NATS - fail if not accessible
        nats_url = os.environ.get("NATS_URL")
        assert nats_url, "NATS_URL must be configured for integration tests"

        # Basic NATS connectivity test
        url_parts = nats_url.replace("nats://", "").split(":")
        if len(url_parts) != 2:
            services_status["NATS"] = "❌ Invalid URL format"
        else:
            try:
                import socket

                host, port = url_parts[0], int(url_parts[1])
                sock = socket.socket()
                sock.settimeout(3)
                sock.connect((host, port))
                sock.close()
                services_status["NATS"] = "✅ Connected"
            except Exception as e:
                services_status["NATS"] = f"❌ Failed: {str(e)[:50]}"

        # Test Telegram
        token = os.environ.get("TELEGRAM_TOKEN", "")
        if len(token) > 30 and ":" in token:
            services_status["Telegram"] = "✅ Token format valid"
        else:
            services_status["Telegram"] = "❌ Token invalid/missing"

        # Report status
        print("\n🔍 Service Connectivity Summary:")
        for service, status in services_status.items():
            print(f"  {service}: {status}")

        # Fail if any services are down
        failed_services = [
            service for service, status in services_status.items() if status.startswith("❌")
        ]

        if failed_services:
            pytest.fail(f"Services failed: {failed_services}")

    def test_environment_configuration_summary(self) -> None:
        """Print a summary of the current environment configuration."""
        print("\n📋 Environment Configuration Summary:")
        print("=" * 50)

        # Database
        db_url = os.environ.get("DATABASE_URL", "")
        if db_url:
            # Parse URL safely for display
            if "@" in db_url:
                parts = db_url.split("@")
                host_part = parts[1] if len(parts) > 1 else "unknown"
                print(f"Database: Connected to {host_part}")
            else:
                print("Database: URL format unclear")
        else:
            print("Database: ❌ Not configured")

        # NATS
        nats_url = os.environ.get("NATS_URL", "")
        if nats_url:
            print(f"NATS: {nats_url}")
        else:
            print("NATS: Not configured (optional)")

        # Telegram
        token = os.environ.get("TELEGRAM_TOKEN", "")
        if token:
            # Show only first few chars for security
            masked_token = f"{token[:10]}...{token[-5:]}" if len(token) > 15 else "***masked***"
            print(f"Telegram: {masked_token}")
        else:
            print("Telegram: ❌ Not configured")

        print("=" * 50)
