"""
Session-scoped pytest fixtures that cache Checkov results.

Helper functions are in helpers.py; import from there in test modules.
"""
from __future__ import annotations

import pytest

from tests.helpers import (
    COMPLIANT_DIR,
    VIOLATIONS_DIR,
    VIOLATION_FILES,
    run_checkov,
)


@pytest.fixture(scope="session")
def checkov_open_firewall():
    return run_checkov(VIOLATION_FILES["open_firewall"])


@pytest.fixture(scope="session")
def checkov_unencrypted_storage():
    return run_checkov(VIOLATION_FILES["unencrypted_storage"])


@pytest.fixture(scope="session")
def checkov_public_storage():
    return run_checkov(VIOLATION_FILES["public_storage"])


@pytest.fixture(scope="session")
def checkov_compliant():
    return run_checkov(COMPLIANT_DIR)


@pytest.fixture(scope="session")
def checkov_all_violations():
    return run_checkov(VIOLATIONS_DIR)
