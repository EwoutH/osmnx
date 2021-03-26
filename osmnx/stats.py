"""
Calculate geometric and topological network measures.

This module defines streets as the edges in an undirected representation of
the graph. Using undirected graph edges prevents double-counting bidirectional
edges of a two-way street, but may double-count a divided road's separate
centerlines with different end point nodes. If `clean_periphery=True` when the
graph was created (which is the default parameterization), then you will get
accurate node degrees (and in turn streets-per-node counts) even at the
periphery of the graph.

You can use NetworkX directly for additional topological network measures.
"""

import logging as lg
import warnings

import networkx as nx
import numpy as np

from . import distance
from . import projection
from . import simplification
from . import utils
from . import utils_graph


def streets_per_node(G):
    """
    Count streets (undirected edges) incident on each node.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    spn : dict
        dictionary with node ID keys and street count values
    """
    spn = dict(nx.get_node_attributes(G, "street_count"))
    if set(spn) != set(G.nodes):
        utils.log("Graph nodes changed since `street_count`s were calculated", level=lg.WARN)
    return spn


def streets_per_node_avg(G):
    """
    Calculate graph's average count of streets per node.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    spna : float
        average count of streets per node
    """
    spn_vals = streets_per_node(G).values()
    return sum(spn_vals) / len(G.nodes)


def streets_per_node_counts(G):
    """
    Calculate streets-per-node counts.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    spnc : dict
        dictionary keyed by count of streets incident on each node, and with
        values of how many nodes in the graph have this count
    """
    spn_vals = list(streets_per_node(G).values())
    return {i: spn_vals.count(i) for i in range(max(spn_vals) + 1)}


def streets_per_node_proportions(G):
    """
    Calculate streets-per-node proportions.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    spnp : dict
        dictionary keyed by count of streets incident on each node, and with
        values of what proportion of nodes in the graph have this count
    """
    n = len(G.nodes)
    spnc = streets_per_node_counts(G)
    return {i: count / n for i, count in spnc.items()}


def intersection_count(G=None, min_streets=2):
    """
    Count the intersections in a graph.

    Intersections are defined as nodes with at least `min_streets` number of
    streets incident on them.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    min_streets : int
        a node must have at least `min_streets` incident on them to count as
        an intersection

    Returns
    -------
    count : int
        count of intersections in graph
    """
    spn = streets_per_node(G)
    node_ids = set(G.nodes)
    return sum(count >= min_streets and node in node_ids for node, count in spn.items())


def street_segment_count(Gu):
    """
    Count the street segments in a graph.

    Parameters
    ----------
    Gu : networkx.MultiGraph
        undirected input graph

    Returns
    -------
    count : int
        count of street segments in graph
    """
    if nx.is_directed(Gu):
        raise ValueError("`Gu` must be undirected")
    return len(Gu.edges)


def street_length_total(Gu):
    """
    Calculate graph's total street segment length.

    Parameters
    ----------
    Gu : networkx.MultiGraph
        undirected input graph

    Returns
    -------
    length : float
        total length (meters) of streets in graph
    """
    if nx.is_directed(Gu):
        raise ValueError("`Gu` must be undirected")
    return sum(d["length"] for u, v, d in Gu.edges(data=True))


def edge_length_total(G):
    """
    Calculate graph's total edge length.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph

    Returns
    -------
    length : float
        total length (meters) of edges in graph
    """
    return sum(d["length"] for u, v, d in G.edges(data=True))


def self_loop_proportion(Gu):
    """
    Calculate percent of edges that are self-loops in a graph.

    A self-loop is defined as an edge from node `u` to node `v` where `u==v`.

    Parameters
    ----------
    Gu : networkx.MultiGraph
        undirected input graph

    Returns
    -------
    proportion : float
        proportion of graph edges that are self-loops
    """
    if nx.is_directed(Gu):
        raise ValueError("`Gu` must be undirected")
    return sum(u == v for u, v, k in Gu.edges) / len(Gu.edges)


def circuity_avg(Gu):
    """
    Calculate average street circuity using edges of undirected graph.

    Circuity is the sum of edge lengths divided by the sum of straight-line
    distances between edge endpoints. Calculates straight-line distance as
    euclidean distance if projected or great-circle distance if unprojected.

    Parameters
    ----------
    Gu : networkx.MultiGraph
        undirected input graph

    Returns
    -------
    circuity_avg : float
        the graph's average undirected edge circuity
    """
    if nx.is_directed(Gu):
        raise ValueError("`Gu` must be undirected")

    # extract the edges' endpoint nodes' coordinates
    coords = np.array(
        [
            (Gu.nodes[u]["y"], Gu.nodes[u]["x"], Gu.nodes[v]["y"], Gu.nodes[v]["x"])
            for u, v, _ in Gu.edges
        ]
    )
    y1 = coords[:, 0]
    x1 = coords[:, 1]
    y2 = coords[:, 2]
    x2 = coords[:, 3]

    # calculate straight-line distances as euclidean distances if projected or
    # great-circle distances if unprojected
    if projection.is_projected(Gu.graph["crs"]):
        sl_dists = distance.euclidean_dist_vec(y1=y1, x1=x1, y2=y2, x2=x2)
    else:
        sl_dists = distance.great_circle_vec(lat1=y1, lng1=x1, lat2=y2, lng2=x2)

    # return the ratio, handling possible division by zero
    sl_dists_total = sl_dists[~np.isnan(sl_dists)].sum()
    try:
        return edge_length_total(Gu) / sl_dists_total
    except ZeroDivisionError:
        return None


def basic_stats(
    G,
    area=None,
    clean_int_tol=None,
    clean_intersects=None,
    tolerance=None,
    circuity_dist=None,
):
    """
    Calculate basic descriptive geometric and topological measures of a graph.

    Density measures are only calculated if `area` is provided and clean
    intersection measures are only calculated if `clean_int_tol` is provided.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        input graph
    area : float
        if not None, calculate density measures and use this area value (in
        square meters) as the denominator
    clean_int_tol : float
        if not None, calculate consolidated intersections count (and density,
        if `area` is also provided) and use this tolerance value; refer to the
        `simplification.consolidate_intersections` function documentation for
        details
    clean_intersects : bool
        deprecated, do not use
    tolerance : float
        deprecated, do not use
    circuity_dist : string
        deprecated, do not use

    Returns
    -------
    stats : dict
        dictionary containing the following attributes
          - `circuity_avg` - see `circuity_avg` function documentation
          - `clean_intersection_count` - see `clean_intersection_count` function documentation
          - `clean_intersection_density_km` - `clean_intersection_count` per sq km
          - `edge_density_km` - `edge_length_total` per sq km
          - `edge_length_avg` - `edge_length_total / m`
          - `edge_length_total` - see `edge_length_total` function documentation
          - `intersection_count` - see `intersection_count` function documentation
          - `intersection_density_km` - `intersection_count` per sq km
          - `k_avg` - graph's average node degree (in-degree and out-degree)
          - `m` - count of edges in graph
          - `n` - count of nodes in graph
          - `node_density_km` - `n` per sq km
          - `self_loop_proportion` - see `self_loop_proportion` function documentation
          - `street_density_km` - `street_length_total` per sq km
          - `street_length_avg` - `street_length_total / street_segment_count`
          - `street_length_total` - see `street_length_total` function documentation
          - `street_segment_count` - see `street_segment_count` function documentation
          - `streets_per_node_avg` - see `streets_per_node_avg` function documentation
          - `streets_per_node_counts` - see `streets_per_node_counts` function documentation
          - `streets_per_node_proportions` - see `streets_per_node_proportions` function documentation
    """
    if circuity_dist is not None:
        msg = (
            "The `circuity_dist` argument has been deprecated and will be "
            "removed in a future release."
        )
        warnings.warn(msg)

    if clean_intersects is None:
        clean_intersects = False
    else:
        msg = (
            "The `clean_intersects` and `tolerance` arguments have been "
            "deprecated and will be removed in a future release. Use the "
            "`clean_int_tol` argument instead."
        )
        warnings.warn(msg)

    if tolerance is None:
        tolerance = 15
    else:
        msg = (
            "The `clean_intersects` and `tolerance` arguments have been "
            "deprecated and will be removed in a future release. Use the "
            "`clean_int_tol` argument instead."
        )
        warnings.warn(msg)

    Gu = utils_graph.get_undirected(G)
    stats = dict()

    stats["n"] = len(G.nodes)
    stats["m"] = len(G.edges)
    stats["k_avg"] = 2 * stats["m"] / stats["n"]
    stats["edge_length_total"] = edge_length_total(G)
    stats["edge_length_avg"] = stats["edge_length_total"] / stats["m"]
    stats["streets_per_node_avg"] = streets_per_node_avg(G)
    stats["streets_per_node_counts"] = streets_per_node_counts(G)
    stats["streets_per_node_proportions"] = streets_per_node_proportions(G)
    stats["intersection_count"] = intersection_count(G)
    stats["street_length_total"] = street_length_total(Gu)
    stats["street_segment_count"] = street_segment_count(Gu)
    stats["street_length_avg"] = stats["street_length_total"] / stats["street_segment_count"]
    stats["circuity_avg"] = circuity_avg(Gu)
    stats["self_loop_proportion"] = self_loop_proportion(Gu)

    # calculate clean intersection counts if requested
    if clean_int_tol:
        stats["clean_intersection_count"] = len(
            simplification.consolidate_intersections(
                G, tolerance=clean_int_tol, rebuild_graph=False, dead_ends=False
            )
        )

    # can only calculate density measures if area was provided
    if area is not None:
        area_km = area / 1_000_000  # convert m^2 to km^2
        stats["node_density_km"] = stats["n"] / area_km
        stats["intersection_density_km"] = stats["intersection_count"] / area_km
        stats["edge_density_km"] = stats["edge_length_total"] / area_km
        stats["street_density_km"] = stats["street_length_total"] / area_km
        if clean_int_tol:
            stats["clean_intersection_density_km"] = stats["clean_intersection_count"] / area_km

    return stats


def extended_stats(G, connectivity=False, anc=False, ecc=False, bc=False, cc=False):
    """
    Do not use: deprecated and will be removed in a future release.

    Parameters
    ----------
    G : networkx.MultiDiGraph
        deprecated
    connectivity : bool
        deprecated
    anc : bool
        deprecated
    ecc : bool
        deprecated
    bc : bool
        deprecated
    cc : bool
        deprecated

    Returns
    -------
    dict
    """
    msg = (
        "The extended_stats function has been deprecated and will be removed in a "
        "future release. Use NetworkX directly for extended topological measures."
    )
    warnings.warn(msg)
    stats = dict()
    D = utils_graph.get_digraph(G, weight="length")
    Gu = nx.Graph(D)
    Gs = utils_graph.get_largest_component(G, strongly=True)
    avg_neighbor_degree = nx.average_neighbor_degree(G)
    stats["avg_neighbor_degree"] = avg_neighbor_degree
    stats["avg_neighbor_degree_avg"] = sum(avg_neighbor_degree.values()) / len(avg_neighbor_degree)
    avg_wtd_nbr_deg = nx.average_neighbor_degree(G, weight="length")
    stats["avg_weighted_neighbor_degree"] = avg_wtd_nbr_deg
    stats["avg_weighted_neighbor_degree_avg"] = sum(avg_wtd_nbr_deg.values()) / len(avg_wtd_nbr_deg)
    degree_centrality = nx.degree_centrality(G)
    stats["degree_centrality"] = degree_centrality
    stats["degree_centrality_avg"] = sum(degree_centrality.values()) / len(degree_centrality)
    stats["clustering_coefficient"] = nx.clustering(Gu)
    stats["clustering_coefficient_avg"] = nx.average_clustering(Gu)
    stats["clustering_coefficient_weighted"] = nx.clustering(Gu, weight="length")
    stats["clustering_coefficient_weighted_avg"] = nx.average_clustering(Gu, weight="length")
    pagerank = nx.pagerank(D, weight="length")
    stats["pagerank"] = pagerank
    pagerank_max_node = max(pagerank, key=lambda x: pagerank[x])
    stats["pagerank_max_node"] = pagerank_max_node
    stats["pagerank_max"] = pagerank[pagerank_max_node]
    pagerank_min_node = min(pagerank, key=lambda x: pagerank[x])
    stats["pagerank_min_node"] = pagerank_min_node
    stats["pagerank_min"] = pagerank[pagerank_min_node]
    if connectivity:
        stats["node_connectivity"] = nx.node_connectivity(Gs)
        stats["edge_connectivity"] = nx.edge_connectivity(Gs)
        utils.log("Calculated node and edge connectivity")
    if anc:
        stats["node_connectivity_avg"] = nx.average_node_connectivity(G)
        utils.log("Calculated average node connectivity")
    if ecc:
        length_func = nx.single_source_dijkstra_path_length
        sp = {source: dict(length_func(Gs, source, weight="length")) for source in Gs.nodes}
        utils.log("Calculated shortest path lengths")
        eccentricity = nx.eccentricity(Gs, sp=sp)
        stats["eccentricity"] = eccentricity
        diameter = nx.diameter(Gs, e=eccentricity)
        stats["diameter"] = diameter
        radius = nx.radius(Gs, e=eccentricity)
        stats["radius"] = radius
        center = nx.center(Gs, e=eccentricity)
        stats["center"] = center
        periphery = nx.periphery(Gs, e=eccentricity)
        stats["periphery"] = periphery
    if cc:
        close_cent = nx.closeness_centrality(G, distance="length")
        stats["closeness_centrality"] = close_cent
        stats["closeness_centrality_avg"] = sum(close_cent.values()) / len(close_cent)
        utils.log("Calculated closeness centrality")
    if bc:
        btwn_cent = nx.betweenness_centrality(D, weight="length")
        stats["betweenness_centrality"] = btwn_cent
        stats["betweenness_centrality_avg"] = sum(btwn_cent.values()) / len(btwn_cent)
        utils.log("Calculated betweenness centrality")
    utils.log("Calculated extended stats")
    return stats
