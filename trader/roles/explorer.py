from math import dist
from typing import List

from loguru import logger
from tsp_solver import greedy

from trader.client.waypoint import Waypoint
from trader.roles.common import Common


class Explorer(Common):
    """
    This role just hops around markets and logs prices for future sales.
    It also acts as a ship procurer to navigate to a market and make purchases for ships.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def find_optimal_path_to_explore(self) -> List[Waypoint]:
        waypoints = self.client.waypoints(
            system_symbol=self.ship.nav.system_symbol
        ).data
        shortest_waypoint_path: List[Waypoint] = []
        if not waypoints:
            logger.error(
                f"Unable to generate a list of waypoints to find shortest path for ship {self.ship.symbol}"
            )
            return shortest_waypoint_path

        # generate a 2d grid of a list so that the tsp lib can solve
        distance_grid: List[List[int]] = [
            [0] * len(waypoints) for _ in range(len(waypoints))
        ]
        active_waypoint_symbol_idx = None
        for i in range(len(waypoints)):
            if waypoints[i].symbol == self.ship.nav.waypoint_symbol:
                active_waypoint_symbol_idx = i

            for j in range(i, len(waypoints)):
                distance = dist(
                    [waypoints[i].x, waypoints[i].y], [waypoints[j].x, waypoints[j].y]
                )
                distance_grid[i][j] = int(distance)
                distance_grid[j][i] = int(distance)

        [
            shortest_waypoint_path.append(waypoints[idx])
            for idx in greedy.solve_tsp(
                distance_grid, endpoints=(active_waypoint_symbol_idx, None)
            )
        ]

        return shortest_waypoint_path

    def traverse_all_waypoints_and_check_markets_and_shipyards(
        self, waypoints: List[Waypoint]
    ) -> None:
        logger.info(f"{self.ship.symbol} is navigating {len(waypoints)} waypoints")
        for waypoint in waypoints:
            traits_to_check = ["MARKETPLACE", "SHIPYARD"]
            if not any(
                [
                    trait in [trait.symbol for trait in waypoint.traits]
                    for trait in traits_to_check
                ]
            ):
                #  don't bother scouting if not a marketplace, not worth
                continue

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

            self.client.orbit(call_sign=self.ship.symbol)
