# conftest.py

import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--create_resources", action="store_true", default=False, help="run resources_creation tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "resources_creation: mark test as slow to run")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--create_resources"):
        skip_not_resources_creation = pytest.mark.skip(reason="remove --create_resources option to run")
        for item in items:
            if not "resources_creation" in item.keywords:
                item.add_marker(skip_not_resources_creation)
    else:
        skip_resources_creation = pytest.mark.skip(reason="need --create_resources option to run")
        for item in items:
            if "resources_creation" in item.keywords:
                item.add_marker(skip_resources_creation)
