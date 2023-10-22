from dataclasses import dataclass

from dataclass_wizard import JSONWizard

@dataclass
class Agent(JSONWizard):
    symbol: str
    headquarters: str
    credits: int
    ship_count: int
    starting_faction: str
    account_id: str

@dataclass
class Contract(JSONWizard):
    id: str

@dataclass
class Faction(JSONWizard):
    symbol: str

@dataclass
class Ship(JSONWizard):
    symbol: str

@dataclass
class AgentPayload(JSONWizard):
    data: Agent

@dataclass
class RegistrationResponse(JSONWizard):
    token: str
    agent: Agent
    contract: Contract
    faction: Faction
    ship: Ship


@dataclass
class RegistrationResponsePayload:
    data: RegistrationResponse
