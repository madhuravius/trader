from typing import List

from pytest import fixture

from trader.client.waypoint import Waypoint
from trader.roles.navigator.geometry import (
    generate_graph_from_waypoints_all_connected,
    generate_shortest_path_with_graph,
)
from trader.tests.factories.client import WaypointFactory

PREDETERMINED_COORDS: List[List[int]] = [[0, 5], [1, 3], [4, 1], [5, 3], [2, 2]]


@fixture
def waypoints() -> List[Waypoint]:
    """
    This fixture scaffolds up some waypoint core values and some extra coords for reuse
    """
    waypoints = [WaypointFactory.build() for _ in range(len(PREDETERMINED_COORDS))]
    for idx, waypoint in enumerate(waypoints):
        waypoint.x, waypoint.y = PREDETERMINED_COORDS[idx]
    return waypoints


def test_generate_graph_from_waypoints(waypoints: List[Waypoint]):
    graph = generate_graph_from_waypoints_all_connected(waypoints=waypoints)
    assert len(graph.nodes) == len(PREDETERMINED_COORDS)


def test_generate_shortest_path_with_graph(waypoints: List[Waypoint]):
    graph = generate_graph_from_waypoints_all_connected(waypoints=waypoints)
    route = generate_shortest_path_with_graph(
        starting_position=waypoints[0].symbol, graph=graph
    )
    # ensure every waypoint is hit at least once
    assert len(route) == len(PREDETERMINED_COORDS)
    assert all(
        [
            waypoint in PREDETERMINED_COORDS
            for waypoint in [[waypoint.x, waypoint.y] for waypoint in route]
        ]
    )
