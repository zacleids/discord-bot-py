import os
import sys

import pytest

from shared.db.db import create_dbs
from shared.models import orm_db

# Ensure the environment is set to TEST
if os.environ.get("ENV") != "TEST":
    sys.exit("ERROR: Tests can only be run when ENV=TEST")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    print("Setting up test database...")
    # Ensure the test DB and all tables exist before any tests run
    create_dbs()
    print("Test database setup complete.")
    orm_db.connect(reuse_if_open=True)
    print("Connected to test database.")
    yield
    print("Tearing down test database...")
    orm_db.close()
    print("Test database teardown complete.")
