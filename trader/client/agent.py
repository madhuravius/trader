from dataclasses import dataclass
from typing import Optional

from dataclass_wizard import JSONWizard


@dataclass
class Agent(JSONWizard):
    symbol: str
    headquarters: str
    credits: int
    ship_count: int
    starting_faction: str
    account_id: Optional[str] = None
