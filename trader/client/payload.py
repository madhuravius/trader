from dataclasses import dataclass
from typing import List, Optional

from dataclass_wizard import JSONWizard

from trader.client.agent import Agent
from trader.client.cargo import Cargo
from trader.client.contract import Contract
from trader.client.cooldown import Cooldown
from trader.client.extraction import Extraction
from trader.client.faction import Faction
from trader.client.fuel import Refuel
from trader.client.market import Market, Sale
from trader.client.navigation import Dock, NavigationAndFuel, Orbit
from trader.client.ship import Ship
from trader.client.system import System
from trader.client.waypoint import Waypoint


@dataclass
class MetaPayloadFields(JSONWizard):
    total: int
    page: int
    limit: int


@dataclass
class ErrorPayload(JSONWizard):
    message: Optional[str]
    code: Optional[int]


@dataclass
class CommonPayloadFields(JSONWizard):
    error: Optional[ErrorPayload] = None
    meta: Optional[MetaPayloadFields] = None


@dataclass
class AgentPayload(CommonPayloadFields):
    data: Optional[Agent] = None


@dataclass
class AgentsPayload(CommonPayloadFields):
    data: Optional[List[Agent]] = None


@dataclass
class ContractsPayload(CommonPayloadFields):
    data: Optional[List[Contract]] = None


@dataclass
class ShipPayload(CommonPayloadFields):
    data: Optional[Ship] = None


@dataclass
class ShipsPayload(CommonPayloadFields):
    data: Optional[List[Ship]] = None


@dataclass
class SystemsPayload(CommonPayloadFields):
    data: Optional[List[System]] = None


@dataclass
class SystemPayload(CommonPayloadFields):
    data: Optional[System] = None


@dataclass
class WaypointsPayload(CommonPayloadFields):
    data: Optional[List[Waypoint]] = None


@dataclass
class RegistrationResponse(JSONWizard):
    token: str
    agent: Agent
    contract: Contract
    faction: Faction
    ship: Ship


@dataclass
class RegistrationResponsePayload(CommonPayloadFields):
    data: Optional[RegistrationResponse] = None


@dataclass
class OrbitPayload(CommonPayloadFields):
    data: Optional[Orbit] = None


@dataclass
class DockPayload(CommonPayloadFields):
    data: Optional[Dock] = None


@dataclass
class ExtractPayload(CommonPayloadFields):
    data: Optional[Extraction] = None


@dataclass
class RefuelPayload(CommonPayloadFields):
    data: Optional[Refuel] = None


@dataclass
class CargoPayload(CommonPayloadFields):
    data: Optional[Cargo] = None


@dataclass
class NavigationPayload(CommonPayloadFields):
    data: Optional[NavigationAndFuel] = None


@dataclass
class CooldownPayload(CommonPayloadFields):
    data: Optional[Cooldown] = None


@dataclass
class MarketPayload(CommonPayloadFields):
    data: Optional[Market] = None


@dataclass
class SalePayload(CommonPayloadFields):
    data: Optional[Sale] = None


PayloadTypes = (
    RegistrationResponsePayload
    | AgentPayload
    | AgentsPayload
    | CargoPayload
    | CooldownPayload
    | ContractsPayload
    | DockPayload
    | ExtractPayload
    | MarketPayload
    | NavigationPayload
    | OrbitPayload
    | RefuelPayload
    | SalePayload
    | ShipsPayload
    | ShipPayload
    | SystemsPayload
    | SystemPayload
    | WaypointsPayload
)
