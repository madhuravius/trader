from dataclasses import dataclass
from typing import Annotated, Literal, Optional

from dataclass_wizard import JSONWizard, json_key

from trader.client.fuel import Fuel

FlightStatuses = Literal["IN_TRANSIT", "IN_ORBIT", "DOCKED"]
FlightModes = Literal["DRIFT", "STEALTH", "CRUISE", "BURN"]


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
    status: FlightStatuses
    flight_mode: FlightModes


@dataclass
class Orbit(JSONWizard):
    nav: Navigation


@dataclass
class Dock(JSONWizard):
    nav: Navigation


@dataclass
class NavigationAndFuel(JSONWizard):
    fuel: Optional[Fuel] = None
    nav: Optional[Navigation] = None


@dataclass
class NavigationRequestData(JSONWizard):
    waypoint_symbol: str


@dataclass
class NavigationRequestPatch(JSONWizard):
    flight_mode: FlightModes
