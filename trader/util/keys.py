import os
from typing import Optional

TOKEN_PATH = ".token"


def write_api_key_to_disk(token: str):
    with open(TOKEN_PATH, "w") as file:
        file.write(token)


def read_api_key_from_disk() -> Optional[str]:
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as file:
            return file.read()
    return None
