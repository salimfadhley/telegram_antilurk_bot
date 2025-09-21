import os
import pytest


@pytest.fixture
def db_url() -> str:
    """Database URL for external connectivity check.

    If not set, skip the test to avoid false negatives in CI.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set; skipping external DB connectivity test")
    return url
