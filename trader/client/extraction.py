from dataclasses import dataclass
from typing import Annotated, Optional

from dataclass_wizard import JSONWizard, json_key


@dataclass
class Yield(JSONWizard):
    symbol: str
    units: int


@dataclass
class Extraction(JSONWizard):
    shipSymbol: Optional[str] = None
    extraction_yield: Optional[Annotated[Yield, json_key("yield")]] = None
