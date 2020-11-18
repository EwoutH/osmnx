"""Expose most common parts of public API directly in `osmnx.` namespace."""

from .bearing import add_edge_bearings
from .distance import get_nearest_edge
from .distance import get_nearest_edges
from .distance import get_nearest_node
from .distance import get_nearest_nodes
from .distance import k_shortest_paths
from .distance import shortest_path
from .elevation import add_edge_grades
from .elevation import add_node_elevations
from .folium import plot_graph_folium
from .folium import plot_route_folium
from .geocoder import geocode
from .geocoder import geocode_to_gdf
from .geometries import geometries_from_address
from .geometries import geometries_from_bbox
from .geometries import geometries_from_place
from .geometries import geometries_from_point
from .geometries import geometries_from_polygon
from .geometries import geometries_from_xml
from .graph import graph_from_address
from .graph import graph_from_bbox
from .graph import graph_from_place
from .graph import graph_from_point
from .graph import graph_from_polygon
from .graph import graph_from_xml
from .io import load_graphml
from .io import save_graph_geopackage
from .io import save_graph_shapefile
from .io import save_graph_xml
from .io import save_graphml
from .plot import plot_figure_ground
from .plot import plot_footprints
from .plot import plot_graph
from .plot import plot_graph_route
from .plot import plot_graph_routes
from .projection import project_gdf
from .projection import project_graph
from .simplification import consolidate_intersections
from .simplification import simplify_graph
from .speed import add_edge_speeds
from .speed import add_edge_travel_times
from .stats import basic_stats
from .stats import extended_stats
from .utils import citation
from .utils import config
from .utils import log
from .utils import ts
from .utils_graph import get_undirected
from .utils_graph import graph_from_gdfs
from .utils_graph import graph_to_gdfs
