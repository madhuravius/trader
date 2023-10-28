from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class ClientRequest:
    function: Callable
    arguments: Dict[str, Any]
