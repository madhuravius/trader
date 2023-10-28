from dataclasses import dataclass
from datetime import datetime

from dataclass_wizard import JSONWizard


@dataclass
class Cooldown(JSONWizard):
    ship_symbol: str
    total_seconds: int
    remaining_seconds: int
    expiration: datetime
