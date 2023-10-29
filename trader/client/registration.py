from dataclasses import dataclass
from typing import Any

from dataclass_wizard import JSONWizard, json_field


@dataclass
class RegistrationRequestData(JSONWizard):
    faction: str
    call_sign: Any = json_field("symbol", all=True)
