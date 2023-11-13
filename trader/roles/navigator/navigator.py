from typing import List

from trader.client.waypoint import Waypoint
from trader.dao.waypoints import Waypoint as WaypointDAO
from trader.roles.common import Common
from trader.roles.navigator.geometry import (
    generate_graph_from_waypoints_all_connected,
    generate_shortest_path_with_graph,
)


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
        graph = generate_graph_from_waypoints_all_connected(waypoints=waypoints)
        return []

    def shortest_traveling_salesman_route(
        self, waypoints: List[Waypoint] | List[WaypointDAO]
    ) -> List[Waypoint] | List[WaypointDAO]:
        """
        For a given list of waypoints, find an approximate shortest possible route among all provided waypoints.
        """
        graph = generate_graph_from_waypoints_all_connected(waypoints=waypoints)
        return generate_shortest_path_with_graph(
            starting_position=self.ship.nav.waypoint_symbol, graph=graph
        )

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
