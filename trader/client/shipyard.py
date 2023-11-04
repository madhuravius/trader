from dataclasses import dataclass
from typing import Annotated, List, Optional

from dataclass_wizard import JSONWizard, json_key

from trader.client.ship import (
    ShipCrew,
    ShipEngine,
    ShipFrame,
    ShipModule,
    ShipMount,
    ShipReactor,
)


@dataclass
class ShipTransaction(JSONWizard):
    waypoint_symbol: str
    ship_symbol: str
    price: int
    agent_symbol: str
    timestamp: str


@dataclass
class ShipType(JSONWizard):
    ship_type: Annotated[str, json_key("type")]


@dataclass
class ShipyardShip(JSONWizard):
    ship_type: Annotated[str, json_key("type")]
    name: str
    description: str
    supply: str
    activity: str
    purchase_price: int
    crew: ShipCrew
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    modules: List[ShipModule]
    mounts: List[ShipMount]


@dataclass
class Shipyard(JSONWizard):
    symbol: str
    ship_types: List[ShipType]
    modifications_fee: int
    transactions: Optional[List[ShipTransaction]] = None
    ships: Optional[List[ShipyardShip]] = None


@dataclass
class ShipPurchaseRequestData(JSONWizard):
    ship_type: str
    waypoint_symbol: str
