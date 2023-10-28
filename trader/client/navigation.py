from dataclasses import dataclass
from typing import Annotated

from dataclass_wizard import JSONWizard, json_key

from trader.client.fuel import Fuel


@dataclass
class NavigationRouteWayPoint(JSONWizard):
    symbol: str
    nav_route_waypoint_type: Annotated[str, json_key("type")]
    system_symbol: str
    x: int
    y: int


@dataclass
class Route(JSONWizard):
    departure_time: str
    arrival: str
    destination: NavigationRouteWayPoint
    departure: NavigationRouteWayPoint
    origin: NavigationRouteWayPoint


@dataclass
class Navigation(JSONWizard):
    system_symbol: str
    waypoint_symbol: str
    route: Route
    status: str
    flight_mode: str


@dataclass
class Orbit(JSONWizard):
    nav: Navigation


@dataclass
class Dock(JSONWizard):
    nav: Navigation


@dataclass
class NavigationAndFuel(JSONWizard):
    fuel: Fuel
    nav: Navigation


@dataclass
class NavigationRequestData(JSONWizard):
    waypoint_symbol: str
