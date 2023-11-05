import math
from typing import List, Tuple

from trader.client.waypoint import Waypoint


def generate_distance_matrix_for_waypoints(
    ship_waypoint_symbol: str, waypoints: List[Waypoint]
) -> Tuple[int | None, List[List[int]]]:
    """
    This function generates a distance matrix for numerous uses when given a series of waypoints.

    It will also include the present index if supplied and if it is present in the distance matrix.
    The matrix is mirrored, so the index represents the same position on either side of the matrix's triangle.
    """
    ship_waypoint_idx = None
    distance_matrix: List[List[int]] = [
        [0] * len(waypoints) for _ in range(len(waypoints))
    ]
    for i in range(len(waypoints)):
        if waypoints[i].symbol == ship_waypoint_symbol:
            ship_waypoint_idx = i

        for j in range(i, len(waypoints)):
            distance = math.dist(
                [waypoints[i].x, waypoints[i].y], [waypoints[j].x, waypoints[j].y]
            )
            distance_matrix[i][j] = int(distance)
            distance_matrix[j][i] = int(distance)

    return ship_waypoint_idx, distance_matrix


def generate_nearest_neighbor_path(
    starting_position: int, distance_matrix: List[List[int]]
) -> List[int]:
    """
    For a given distance matrix (2d array), check every nearest neighbor and determine
    the shortest path for that as one traverses through the matrix.

    Implementation based on: https://en.wikipedia.org/wiki/Nearest_neighbour_algorithm
    Where u is `starting_position`.
    """
    visited: List[bool] = [False] * len(distance_matrix)
    visited[starting_position] = True

    route: List[int] = [starting_position]
    current_vertex = starting_position

    while not all(visited):
        unvisited_nodes_distances: List[float] = []
        for idx, visited_already in enumerate(visited):
            if visited_already:
                unvisited_nodes_distances.append(math.inf)
            else:
                unvisited_nodes_distances.append(
                    float(distance_matrix[current_vertex][idx])
                )

        nearest_neighbor = unvisited_nodes_distances.index(
            min(unvisited_nodes_distances)
        )
        visited[nearest_neighbor] = True
        current_vertex = nearest_neighbor
        route.append(current_vertex)

    return route
