from pytest_socket import disable_socket

from trader.tests.mocks.common import default_read_api_key_from_disk as _
from trader.tests.mocks.common import default_write_api_key_to_disk as _

pytest_plugins = [
    "trader.tests.plugins.alembic",
]


def pytest_runtest_setup():
    disable_socket()
