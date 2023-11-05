from typing import List

from pytest import fixture

from trader.client.waypoint import Waypoint
from trader.roles.navigator.geometry import (
    generate_distance_matrix_for_waypoints,
    generate_nearest_neighbor_path,
)
from trader.tests.factories.client import WaypointFactory

PREDETERMINED_COORDS: List[List[int]] = [[0, 5], [1, 3], [4, 1], [5, 3], [2, 2]]
PRECALCULATED_DISTANCE_MATRIX: List[List[int]] = [
    [0, 2, 5, 5, 3],
    [2, 0, 3, 4, 1],
    [5, 3, 0, 2, 2],
    [5, 4, 2, 0, 3],
    [3, 1, 2, 3, 0],
]


@fixture
def waypoints() -> List[Waypoint]:
    """
    This fixture scaffolds up some waypoint core values and some extra coords for reuse
    """
    waypoints = [WaypointFactory.build() for _ in range(len(PREDETERMINED_COORDS))]
    for idx, waypoint in enumerate(waypoints):
        waypoint.x, waypoint.y = PREDETERMINED_COORDS[idx]
    return waypoints


def test_generate_distance_matrix_for_waypoints_with_ship(waypoints: List[Waypoint]):
    ship_waypoint_idx, distance_matrix = generate_distance_matrix_for_waypoints(
        waypoints=waypoints, ship_waypoint_symbol=waypoints[2].symbol
    )
    assert ship_waypoint_idx == 2
    assert distance_matrix == PRECALCULATED_DISTANCE_MATRIX


def test_generate_distance_matrix_for_waypoints_without_ship(waypoints: List[Waypoint]):
    ship_waypoint_idx, distance_matrix = generate_distance_matrix_for_waypoints(
        waypoints=waypoints, ship_waypoint_symbol="DOES NOT EXIST"
    )
    assert ship_waypoint_idx == None
    assert distance_matrix == PRECALCULATED_DISTANCE_MATRIX


def test_generate_nearest_neighbor_path(waypoints: List[Waypoint]):
    # this test is a bit jank but gives me a feeling that this will work repeatedly, but not sure how else to properly assert
    predetermined_shortest_nn_paths = [
        [0, 1, 4, 2, 3],
        [1, 4, 2, 3, 0],
        [2, 3, 4, 1, 0],
        [3, 2, 4, 1, 0],
        [4, 1, 0, 2, 3],
    ]

    for idx in range(len(PREDETERMINED_COORDS)):
        ship_waypoint_idx, distance_matrix = generate_distance_matrix_for_waypoints(
            waypoints=waypoints, ship_waypoint_symbol=waypoints[idx].symbol
        )
        assert ship_waypoint_idx is not None
        route = generate_nearest_neighbor_path(
            starting_position=ship_waypoint_idx, distance_matrix=distance_matrix
        )
        assert route == predetermined_shortest_nn_paths[idx]
