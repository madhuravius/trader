from itertools import product
from math import dist
from typing import List, Sequence, cast

import networkx as nx
import numpy as np
from scipy import spatial
from sklearn.cluster import MeanShift, estimate_bandwidth

from trader.client.waypoint import Waypoint
from trader.dao.waypoints import Waypoint as WaypointDAO


def generate_graph_from_waypoints_means_shift_clustering(
    waypoints: List[Waypoint] | Sequence[WaypointDAO],
) -> nx.DiGraph:
    """
    Generates a graph and only connects with nearest neighbors. It will connect the nearest
    neighbors in an estimate of what it deems is a cluster.
    This resultant graph has a waypoints attribute that contains its children and a core
    designated child (marketplace).

    This utilizes Means Shift clustering to determine nearest groups of waypoints.
    """
    graph = nx.DiGraph()

    waypoints_coords_with_idx = np.array(
        [[waypoint.x, waypoint.y, idx] for idx, waypoint in enumerate(waypoints)]
    )
    waypoints_coords = [
        [waypoint[0], waypoint[1]] for waypoint in waypoints_coords_with_idx
    ]

    bandwidth = estimate_bandwidth(
        waypoints_coords, quantile=0.2, n_samples=len(waypoints_coords)
    )
    ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
    yhat = ms.fit_predict(waypoints_coords)
    clusters = np.unique(yhat)
    centers = ms.cluster_centers_

    for cluster in clusters:
        center = centers[cluster]

        cluster_waypoint_coords = np.where(yhat == cluster)
        cluster_waypoints: List[Waypoint | WaypointDAO] = []
        for cluster_waypoint in cluster_waypoint_coords:
            for waypoint in cluster_waypoint:
                cluster_waypoints.append(waypoints[waypoint])

        selected_center = None
        market_waypoint_found = False
        for cluster_waypoint in cluster_waypoints:
            if "Marketplace" in [trait.name for trait in cluster_waypoint.traits]:
                selected_center = cluster_waypoint
                market_waypoint_found = True
                break

        if not selected_center:
            # if no market waypoint nearby or within the cluster, sadly choose the nearest
            # and mark it as such
            non_market_cluster_wps = np.array(
                [[waypoint.x, waypoint.y] for waypoint in cluster_waypoints]
            )
            non_market_cluster_data_tree = spatial.KDTree(non_market_cluster_wps)
            _, nearest_point_idx = non_market_cluster_data_tree.query(center)
            selected_center = cast(Waypoint, cluster_waypoints[int(nearest_point_idx)])
            market_waypoint_found = False

        graph.add_node(
            selected_center.symbol,
            x=selected_center.x,
            y=selected_center.y,
            waypoint=selected_center,
            cluster_waypoints=cluster_waypoints,
            cluster_waypoints_symbols=[
                waypoint.symbol for waypoint in cluster_waypoints
            ],
            market_waypoint_found=market_waypoint_found,
        )

    return graph


def generate_graph_from_waypoints_all_connected(
    waypoints: List[Waypoint] | List[WaypointDAO],
) -> nx.DiGraph:
    """
    Generate a graph and connect every waypoint with every other waypoint. This is
    useful for things like traveling salesmen problems when trying to hit every node at least
    one time.
    """
    graph = nx.DiGraph()
    for waypoint in waypoints:
        graph.add_node(waypoint.symbol, x=waypoint.x, y=waypoint.y, waypoint=waypoint)

    # connect everything in the graph to everything else
    [
        graph.add_edge(
            waypoints[waypoint_one].symbol,
            waypoints[waypoint_two].symbol,
            weight=dist(
                [waypoints[waypoint_one].x, waypoints[waypoint_one].y],
                [waypoints[waypoint_two].x, waypoints[waypoint_two].y],
            ),
        )
        for waypoint_one, waypoint_two in product(
            range(len(waypoints)), range(len(waypoints))
        )
        if waypoints[waypoint_one].symbol != waypoints[waypoint_two].symbol
    ]
    return graph


def generate_shortest_path_with_graph(
    starting_position: str,
    graph: nx.DiGraph,
) -> List[Waypoint] | List[WaypointDAO]:
    """
    takes a graph from networkx and just applies this function to it
    which should generate the shortest path: traveling_salesman_problem
    """
    route = []
    path = nx.approximation.traveling_salesman_problem(
        G=graph, method=nx.approximation.greedy_tsp, cycle=False
    )
    if graph.nodes:
        base_route = [
            cast(Waypoint, graph.nodes.get(path_step, {}).get("waypoint"))
            for path_step in path
        ]
        # make it loop back to the intended starting point instead of
        # an arbitrary start/end
        for idx, path_node in enumerate(base_route):
            if path_node.symbol == starting_position:
                route = base_route[idx:] + base_route[:idx]
                break
    return route
