from dataclasses import dataclass

from dataclass_wizard import JSONWizard

from trader.client.agent import Agent
from trader.client.ship import Ship
from trader.client.shipyard import ShipTransaction


@dataclass
class ShipPurchase(JSONWizard):
    agent: Agent
    ship: Ship
    transaction: ShipTransaction
