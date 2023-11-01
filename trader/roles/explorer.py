from math import dist
from typing import List

from loguru import logger
from tsp_solver import greedy

from trader.client.waypoint import Waypoint
from trader.roles.common import Common


class Explorer(Common):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # lowest base priority as this is purely navigation and information related
        # and can afford to wait. does not impact revenue stream directly if blocked
        self.base_priority = 1
        self.client.set_base_priority(base_priority=self.base_priority)

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

    def traverse_all_waypoints_and_check_markets(
        self, waypoints: List[Waypoint]
    ) -> None:
        logger.info(f"{self.ship.symbol} is navigating {len(waypoints)} waypoints")
        for waypoint in waypoints:
            self.navigate_to_waypoint(waypoint_symbol=waypoint.symbol)

            if "MARKETPLACE" not in [trait.symbol for trait in waypoint.traits]:
                continue

            self.refresh_market_data(
                system_symbol=waypoint.system_symbol, waypoint_symbol=waypoint.symbol
            )

            self.client.orbit(call_sign=self.ship.symbol)
