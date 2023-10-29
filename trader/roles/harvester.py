from loguru import logger

from trader.client.waypoint import Waypoint
from trader.exceptions import TraderException
from trader.roles.common import Common
from trader.util.algebra import compute_distance

DISALLOWED_WAYPOINT_TYPE = ["ASTEROID_BASE"]

DISALLOWED_LOCATION_TYPES = [
    "CORROSIVE_ATMOSPHERE",
    "EXPLOSIVE_GASES",
    "EXTREME_PRESSURE",
    "EXTREME_TEMPERATURES",
    "RADIOACTIVE",
    "STRIPPED",
    "STRONG_GRAVITY",
    "THIN_ATMOSPHERE",
    "TOXIC_ATMOSPHERE",
]


class Harvester(Common):
    def find_best_location_to_mine(self) -> Waypoint:
        locations = {}
        raw_locations = self.client.waypoints(self.ship.nav.system_symbol)
        if not raw_locations.data:
            raise TraderException("No waypoints found to find locations to mine!")
        for location in raw_locations.data:
            disallowed_location = False
            for trait in location.traits:
                if trait in DISALLOWED_LOCATION_TYPES:
                    disallowed_location = True
                    break
            if location.waypoint_system_type in DISALLOWED_WAYPOINT_TYPE:
                disallowed_location = True

            if not disallowed_location:
                x1, y1 = (
                    self.ship.nav.route.destination.x,
                    self.ship.nav.route.destination.y,
                )
                x2, y2 = location.x, location.y
                distance_from_current_location = compute_distance(
                    x1=x1, x2=x2, y1=y1, y2=y2
                )
                locations[distance_from_current_location] = location
        return locations[min(locations.keys())]

    def mine(self):
        logger.info(f"Ship {self.ship.symbol} starting to mine, then waiting")
        best_location = self.find_best_location_to_mine()
        self.refuel_ship()
        self.navigate_to_waypoint(waypoint_symbol=best_location.symbol)

        while True:
            if self.ship.cargo.units == self.ship.cargo.capacity:
                logger.info(f"Ship {self.ship.symbol} completed mining")
                break
            self.client.extract(call_sign=self.ship.symbol)
            self.wait()

    def survey(self):
        pass
