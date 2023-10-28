from dataclasses import dataclass
from typing import List, Optional

from dataclass_wizard import JSONWizard


@dataclass
class DeliverContractTerms(JSONWizard):
    destination_symbol: str
    trade_symbol: str
    units_fulfilled: int
    units_required: int


@dataclass
class ContractPayment(JSONWizard):
    on_accepted: int
    on_fulfilled: int


@dataclass
class ContractTerms(JSONWizard):
    deadline: str
    deliver: Optional[List[DeliverContractTerms]] = None
    payment: Optional[ContractPayment] = None


@dataclass
class Contract(JSONWizard):
    accepted: bool
    deadline_to_accept: str
    expiration: str
    faction_symbol: str
    fulfilled: bool
    id: str
    terms: Optional[ContractTerms] = None
