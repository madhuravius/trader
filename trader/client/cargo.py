from dataclasses import dataclass
from typing import List

from dataclass_wizard import JSONWizard


@dataclass
class Inventory(JSONWizard):
    symbol: str
    name: str
    description: str
    units: int


@dataclass
class Cargo(JSONWizard):
    capacity: int
    units: int
    inventory: List[Inventory]


@dataclass
class CargoRequest(JSONWizard):
    symbol: str
    units: int
