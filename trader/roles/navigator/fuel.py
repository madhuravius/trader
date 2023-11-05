from typing import Callable, Dict

from trader.client.navigation import FlightModes

"""
fuel is computed based on the following matrix:

CRUISE  = d
DRIFT   = 1
BURN    = 2d
STEALTH = d

source: https://github.com/SpaceTradersAPI/api-docs/wiki/Travel-Fuel-and-Time
"""
FUEL_COST_MULTIPLIER: Dict[FlightModes, Callable[[int], int]] = {
    "CRUISE": lambda distance: distance,
    "DRIFT": lambda _: 1,
    "BURN": lambda distance: 2 * distance,
    "STEALTH": lambda distance: distance,
}
