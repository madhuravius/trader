from dataclasses import dataclass
from typing import List

from dataclass_wizard import JSONWizard


@dataclass
class FactionTrait(JSONWizard):
    symbol: str
    name: str
    description: str


@dataclass
class Faction(JSONWizard):
    symbol: str
    name: str
    description: str
    headquarters: str
    traits: List[FactionTrait]
    is_recruiting: bool
