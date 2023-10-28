from dataclasses import dataclass
from typing import Annotated, List, Optional

from dataclass_wizard import JSONWizard, json_key


@dataclass
class Faction(JSONWizard):
    symbol: str


@dataclass
class Traits(JSONWizard):
    symbol: str
    name: str
    description: str


@dataclass
class Orbital(JSONWizard):
    symbol: str


@dataclass
class Chart(JSONWizard):
    submitted_by: str
    submitted_on: str
    waypoint_symbol: Optional[str] = None


@dataclass
class Waypoint(JSONWizard):
    symbol: str
    waypoint_system_type: Annotated[str, json_key("type")]
    system_symbol: str
    x: int
    y: int
    orbitals: List[Orbital]
    faction: Faction
    traits: List[Traits]
    chart: Chart
    orbits: Optional[str] = None
