#!/usr/bin/env python3
"""Test external PostgreSQL connectivity for Telegram Anti-Lurk Bot."""

import os
import sys

from sqlalchemy import create_engine, text


def test_connection(db_url: str) -> bool:
    """Test database connection with detailed error reporting."""
    try:
        print(f"Testing connection to: {db_url.split('@')[1] if '@' in db_url else db_url}")

        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()")).first()
            print("✅ Connection successful!")
            print(f"   PostgreSQL version: {result[0]}")

            # Test basic operations
            conn.execute(text("SELECT 1 + 1 as test")).first()
            print("   ✅ Basic queries working")

            # Test database permissions
            try:
                conn.execute(text("CREATE TEMP TABLE test_permissions (id int)"))
                conn.execute(text("DROP TABLE test_permissions"))
                print("   ✅ Table creation/deletion permissions working")
            except Exception as e:
                print(f"   ⚠️  Limited permissions: {e}")

            return True

    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ Connection failed: {e}")

        if "connection refused" in error_msg:
            print("   💡 Possible causes:")
            print("      - PostgreSQL not running")
            print("      - Firewall blocking port 5432")
            print("      - PostgreSQL not configured to accept external connections")

        elif "authentication failed" in error_msg or "password authentication failed" in error_msg:
            print("   💡 Possible causes:")
            print("      - Wrong username/password")
            print("      - User doesn't have permission to connect from this host")
            print("      - pg_hba.conf doesn't allow connections from external hosts")

        elif "could not translate host name" in error_msg or "name resolution failed" in error_msg:
            print("   💡 Possible causes:")
            print("      - Hostname not resolvable (try IP address instead)")
            print("      - DNS issues")

        elif "timeout" in error_msg:
            print("   💡 Possible causes:")
            print("      - Network connectivity issues")
            print("      - Firewall dropping packets")

        return False


def main():
    """Test various connection scenarios."""
    test_scenarios = [
        {
            "name": "Halob with hostname (postgres superuser)",
            "url": "postgresql://postgres:postgres@halob:5432/postgres",
        },
        {
            "name": "Halob with IP (postgres superuser)",
            "url": "postgresql://postgres:postgres@192.168.86.31:5432/postgres",
        },
        {
            "name": "Bot user (if created)",
            "url": "postgresql://antilurk_bot:AntiLurk2024!SecurePass@halob:5432/antilurk",
        },
        {
            "name": "Custom DATABASE_URL (from environment)",
            "url": os.environ.get("DATABASE_URL", ""),
        },
    ]

    print("🔍 Testing PostgreSQL External Connectivity")
    print("=" * 50)

    success_count = 0
    for i, scenario in enumerate(test_scenarios, 1):
        if not scenario["url"]:
            print(f"{i}. {scenario['name']}: SKIPPED (no URL provided)")
            continue

        print(f"\n{i}. Testing: {scenario['name']}")
        print("-" * 30)

        if test_connection(scenario["url"]):
            success_count += 1

    print(f"\n{'=' * 50}")
    print(
        f"Summary: {success_count}/{len([s for s in test_scenarios if s['url']])} connections successful"
    )

    if success_count == 0:
        print("\n🚨 No successful connections!")
        print("📋 Next steps:")
        print("   1. Review deploy/setup_external_postgres.md")
        print("   2. Configure PostgreSQL for external connections")
        print("   3. Create antilurk_bot user and database")
        print("   4. Restart PostgreSQL service")
        sys.exit(1)
    else:
        print("\n✅ External connectivity verified!")


if __name__ == "__main__":
    main()
