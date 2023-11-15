from typing import List

from loguru import logger

from trader.client.waypoint import Waypoint
from trader.dao.shipyards import get_shipyard_ships_by_waypoint
from trader.dao.waypoints import Waypoint as WaypointDAO
from trader.roles.common import Common


class Explorer(Common):
    """
    This role just hops around markets and logs prices for future sales.
    It also acts as a ship procurer to navigate to a market and make purchases for ships.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def find_relevant_paths_to_explore(self, filters: List[str]) -> List[Waypoint]:
        """
        Find paths based on supplied filters
        """
        waypoints: List[Waypoint] = []
        waypoints_data = self.client.waypoints(
            system_symbol=self.ship.nav.system_symbol
        ).data

        if not waypoints_data:
            logger.error(
                f"Unable to generate a list of waypoints to find shortest path for ship {self.ship.symbol}"
            )
            return waypoints

        for waypoint in waypoints_data:
            if not any(
                [
                    trait in [trait.symbol for trait in waypoint.traits]
                    for trait in filters
                ]
            ):
                #  don't bother scouting if not a marketplace, not worth
                continue
            waypoints.append(waypoint)

        return waypoints

    def traverse_all_waypoints_and_check_markets_and_shipyards(
        self, waypoints: List[Waypoint] | List[WaypointDAO]
    ) -> None:
        logger.info(f"{self.ship.symbol} is navigating {len(waypoints)} waypoints")
        for waypoint in waypoints:
            self.refuel_and_navigate_to_waypoint(
                waypoint_symbol=waypoint.symbol, system_symbol=waypoint.system_symbol
            )

            if "MARKETPLACE" in [trait.symbol for trait in waypoint.traits]:
                self.refresh_market_data(
                    system_symbol=waypoint.system_symbol,
                    waypoint_symbol=waypoint.symbol,
                )

            if "SHIPYARD" in [trait.symbol for trait in waypoint.traits]:
                self.refresh_shipyard_data(
                    system_symbol=waypoint.system_symbol,
                    waypoint_symbol=waypoint.symbol,
                )
                # if in a shipyard, and the fleet needs more ships, buy the one we want!
                possible_ships_for_sale = get_shipyard_ships_by_waypoint(
                    engine=self.dao.engine,
                    system_symbol=waypoint.system_symbol,
                    waypoint_symbol=waypoint.symbol,
                )
                # pass these ships in to parent, to determine if purchase is needed

            self.client.orbit(call_sign=self.ship.symbol)
