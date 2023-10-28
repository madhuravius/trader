from dataclasses import dataclass
from typing import Annotated, List

from dataclass_wizard import JSONWizard, json_key


@dataclass
class ConnectedSystem(JSONWizard):
    symbol: str
    sector_symbol: str
    connected_system_type: Annotated[str, json_key("type")]
    faction_symbol: str
    x: int
    y: int
    distance: int


@dataclass
class JumpGate(JSONWizard):
    jump_range: int
    faction_symbol: str
    connected_systems: List[ConnectedSystem]
