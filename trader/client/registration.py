from dataclasses import dataclass
from typing import Annotated

from dataclass_wizard import JSONWizard, json_key


@dataclass
class RegistrationRequestData(JSONWizard):
    call_sign: Annotated[str, json_key("symbol")]
    faction: str
