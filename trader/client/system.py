from dataclasses import dataclass
from typing import Annotated, List

from dataclass_wizard import JSONWizard, json_key


@dataclass
class Orbital(JSONWizard):
    symbol: str


@dataclass
class Waypoint(JSONWizard):
    symbol: str
    waypoint_type: Annotated[str, json_key("type")]
    x: int
    y: int
    orbitals: List[Orbital]


@dataclass
class Faction(JSONWizard):
    symbol: str


@dataclass
class System(JSONWizard):
    symbol: str
    sector_symbol: str
    system_type: Annotated[str, json_key("type")]
    x: int
    y: int
    waypoints: List[Waypoint]
    factions: List[Faction]
