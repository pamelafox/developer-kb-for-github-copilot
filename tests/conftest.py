import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live-smoke",
        action="store_true",
        default=False,
        help="Run browser tests against the selected provisioned azd environment without API mocks.",
    )
    parser.addoption(
        "--smoke-base-url",
        default=None,
        help="Run unmocked browser smoke tests against an already deployed application URL.",
    )


@pytest.fixture(scope="session")
def live_smoke(pytestconfig: pytest.Config) -> bool:
    return bool(pytestconfig.getoption("--live-smoke") or pytestconfig.getoption("--smoke-base-url"))


@pytest.fixture(scope="session")
def smoke_base_url(pytestconfig: pytest.Config) -> str | None:
    return pytestconfig.getoption("--smoke-base-url")
