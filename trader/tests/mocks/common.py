from typing import Iterator
from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def default_write_api_key_to_disk() -> Iterator[None]:
    with patch("trader.util.keys.write_api_key_to_disk"):
        yield


@pytest.fixture(scope="session", autouse=True)
def default_read_api_key_from_disk() -> Iterator[None]:
    with patch("trader.util.keys.write_api_key_to_disk"):
        yield
