from dataclasses import dataclass
from typing import Annotated, List, Optional

from dataclass_wizard import JSONWizard, json_key

from trader.client.agent import Agent
from trader.client.cargo import Cargo


@dataclass
class Export(JSONWizard):
    symbol: str
    name: str
    description: str


@dataclass
class Import(JSONWizard):
    symbol: str
    name: str
    description: str


@dataclass
class Exchange(JSONWizard):
    symbol: str
    name: str
    description: str


@dataclass
class Transaction(JSONWizard):
    waypoint_symbol: str
    ship_symbol: str
    trade_symbol: str
    transaction_type: Annotated[str, json_key("type")]
    units: int
    price_per_unit: int
    total_price: int
    timestamp: str


@dataclass
class TradeGood(JSONWizard):
    symbol: str
    trade_volume: int
    supply: str
    purchase_price: int
    sell_price: int


@dataclass
class Market(JSONWizard):
    symbol: str
    exports: List[Export]
    imports: List[Import]
    exchange: List[Exchange]
    transactions: Optional[List[Transaction]] = None
    trade_goods: Optional[List[TradeGood]] = None


@dataclass
class Sale(JSONWizard):
    agent: Agent
    cargo: Cargo
    transaction: Transaction
