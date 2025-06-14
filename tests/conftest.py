"""Global test configuration and shared fixtures."""

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection for CI environment."""
    # Skip slow tests in CI unless explicitly requested
    if os.environ.get("CI") and not os.environ.get("RUN_SLOW_TESTS"):
        skip_slow = pytest.mark.skip(reason="Skipping slow tests in CI")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)