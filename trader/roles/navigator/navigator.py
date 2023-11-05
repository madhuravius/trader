from typing import List

from tsp_solver import greedy

from trader.client.waypoint import Waypoint
from trader.roles.common import Common
from trader.roles.navigator.geometry import generate_distance_matrix_for_waypoints


class Navigator(Common):
    """
    This role doesn't do much in terms of moving/actions on ships, but plots courses of various sorts.

    Its sole purpose is to generate routes for other roles to consume and act on. Some routes are generated
    dynamically and on the fly (mining activity), while others are predetermined for individual ships/squads
    to consume (exploration and market refresh circuits).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def shortest_travel_route_with_refueling(
        self, waypoints: List[Waypoint]
    ) -> List[Waypoint]:
        """
        Will attempt to generate a shortest distance between two locations while accounting for
        the need to refuel in between those two locations.
        """
        return []

    def shortest_traveling_salesman_route(
        self, waypoints: List[Waypoint]
    ) -> List[Waypoint]:
        """
        For a given list of waypoints, find an approximate shortest possible route among all provided waypoints.
        """
        ship_waypoint_idx, distance_matrix = generate_distance_matrix_for_waypoints(
            ship_waypoint_symbol=self.ship.nav.waypoint_symbol, waypoints=waypoints
        )

        shortest_waypoint_path: List[Waypoint] = []
        [
            shortest_waypoint_path.append(waypoints[idx])
            for idx in greedy.solve_tsp(
                distance_matrix, endpoints=(ship_waypoint_idx, None)
            )
        ]

        return shortest_waypoint_path

    def shortest_route_between_groups_of_waypoints(
        self, waypoint_group_1: List[Waypoint], waypoint_group_2: List[Waypoint]
    ) -> List[Waypoint]:
        """
        This is to help migrate miners on unprofitable routes (though they might be in maximal LOCAL groupings) to
        profitable pairings in a larger context

        The purpose of this method is to find the shortest route between two separate groups of waypoints:
        1. you need to mine (mining related waypoints)
        2. you need to refuel (refueling related waypoints)
        3. you need to sell (sales related waypoints)
        4. you need to refuel (refueling related waypoints)
           to start again
        """
        return []
