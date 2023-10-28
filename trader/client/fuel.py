from dataclasses import dataclass

from dataclass_wizard import JSONWizard

from trader.client.agent import Agent
from trader.client.market import Transaction


@dataclass
class FuelConsumed(JSONWizard):
    amount: int
    timestamp: str


@dataclass
class Fuel(JSONWizard):
    current: int
    capacity: int
    consumed: FuelConsumed


@dataclass
class Refuel(JSONWizard):
    agent: Agent
    fuel: Fuel
    transaction: Transaction
