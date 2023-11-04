from math import dist

from loguru import logger

from trader.client.waypoint import Waypoint
from trader.roles.common import Common

ALLOWED_WAYPOINT_TYPE = ["ASTEROID_FIELD", "ASTEROID"]

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

    def find_best_location_to_mine(self) -> Waypoint:
        locations = {}
        waypoints = self.fetch_waypoints_possible_for_ship()
        for waypoint in waypoints:
            disallowed_location = False
            for trait in waypoint.traits:
                if trait in DISALLOWED_LOCATION_TYPES:
                    disallowed_location = True
                    break
            if waypoint.waypoint_system_type not in ALLOWED_WAYPOINT_TYPE:
                disallowed_location = True

            if not disallowed_location:
                distance_from_current_location = dist(
                    [
                        self.ship.nav.route.destination.x,
                        self.ship.nav.route.destination.y,
                    ],
                    [waypoint.x, waypoint.y],
                )
                locations[distance_from_current_location] = waypoint
        return locations[min(locations.keys())]

    def mine(self):
        logger.info(f"Ship {self.ship.symbol} starting to mine, then waiting")
        best_location = self.find_best_location_to_mine()
        self.refuel_and_navigate_to_waypoint(
            waypoint_symbol=best_location.symbol,
            system_symbol=best_location.system_symbol,
        )

        while True:
            if self.ship.cargo.units == self.ship.cargo.capacity:
                logger.info(f"Ship {self.ship.symbol} completed mining")
                break
            self.client.extract(call_sign=self.ship.symbol)
            self.wait()

    def survey(self):
        pass
