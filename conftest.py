import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration-tests", action="store_true", default=False, help="run integration tests with hardware I/O"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration_test: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration-tests"):
        # --run-integration-tests given in cli: do not skip integration tests
        return
    skip_integration_test = pytest.mark.skip(reason="need --run-integration-tests option to run")
    for item in items:
        if "integration_test" in item.keywords:
            item.add_marker(skip_integration_test)
