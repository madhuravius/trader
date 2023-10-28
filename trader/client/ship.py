from dataclasses import dataclass
from typing import List, Optional

from dataclass_wizard import JSONWizard

from trader.client.cargo import Cargo
from trader.client.fuel import Fuel
from trader.client.navigation import Navigation


@dataclass
class ShipCrew(JSONWizard):
    current: int
    required: int
    capacity: int
    rotation: str
    morale: int
    wages: int


@dataclass
class ShipRequirements(JSONWizard):
    power: Optional[int] = None
    crew: Optional[int] = None
    slots: Optional[int] = None


@dataclass
class ShipModule(JSONWizard):
    symbol: str
    name: str
    description: str
    requirements: ShipRequirements
    capacity: Optional[int] = None
    ship_module_range: Optional[int] = None


@dataclass
class ShipWaypoint(JSONWizard):
    symbol: str
    name: str
    description: str
    strength: int
    requirements: ShipRequirements
    deposits: List[str]


@dataclass
class ShipReactor(JSONWizard):
    symbol: str
    name: str
    description: str
    condition: int
    power_output: int
    requirements: ShipRequirements


@dataclass
class ShipEngine(JSONWizard):
    symbol: str
    name: str
    description: str
    condition: int
    speed: int
    requirements: ShipRequirements


@dataclass
class ShipCooldown(JSONWizard):
    ship_symbol: str
    total_seconds: int
    remaining_seconds: int
    expiration: Optional[str] = None


@dataclass
class ShipMount(JSONWizard):
    symbol: str
    name: str
    description: str
    strength: int
    requirements: ShipRequirements


@dataclass
class ShipRegistration(JSONWizard):
    name: str
    faction_symbol: str
    role: str


@dataclass
class ShipFrame(JSONWizard):
    symbol: str
    name: str
    description: str
    condition: int
    module_slots: int
    mounting_points: int
    fuel_capacity: int
    requirements: ShipRequirements


@dataclass
class Ship(JSONWizard):
    symbol: str
    registration: ShipRegistration
    nav: Navigation
    crew: ShipCrew
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    cooldown: ShipCooldown
    modules: List[ShipModule]
    mounts: List[ShipMount]
    cargo: Cargo
    fuel: Fuel
