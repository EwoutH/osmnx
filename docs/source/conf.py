"""
Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
from pathlib import Path
from typing import Any

# go up two levels from current working dir (/docs/source) to package root
pkg_root_path = str(Path.cwd().parent.parent)
sys.path.insert(0, pkg_root_path)

author = "Geoff Boeing"
copyright = "2016-2024, Geoff Boeing"  # noqa: A001
project = "OSMnx"

# dynamically load version from /osmnx/_version.py
with Path.open(Path("../../osmnx/_version.py")) as f:
    version = release = f.read().split(" = ")[1].replace('"', "")

# mock import all required + optional dependency packages because readthedocs
# does not have them installed
autodoc_mock_imports = [
    "geopandas",
    "matplotlib",
    "networkx",
    "numpy",
    "osgeo",
    "pandas",
    "rasterio",
    "requests",
    "scipy",
    "shapely",
    "sklearn",
]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
language = "en"
needs_sphinx = "7"  # same value as pinned in /docs/requirements.txt
root_doc = "index"
source_suffix = ".rst"
templates_path: list[Any] = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_static_path: list[Any] = []
html_theme = "furo"
