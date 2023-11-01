from math import dist

from loguru import logger

from trader.client.waypoint import Waypoint
from trader.exceptions import TraderException
from trader.roles.common import Common

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # highest base priority as this is harvesting-related
        # and directly income generated
        self.base_priority = 3
        self.client.set_base_priority(base_priority=self.base_priority)

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
                distance_from_current_location = dist(
                    [
                        self.ship.nav.route.destination.x,
                        self.ship.nav.route.destination.y,
                    ],
                    [location.x, location.y],
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
