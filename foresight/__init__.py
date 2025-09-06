"""
Foresight: Radio astronomy source masking from TGSS-NVSS catalog.

This package provides tools for creating WSClean-compatible source lists and 
FITS masks from the TGSS-NVSS spectral index catalog for interferometric imaging.
"""

__version__ = "0.1.0"
__author__ = "Arpan Pal"

import os
import pkg_resources

# Get path to bundled catalog
def get_catalog_path():
    """Get the path to the bundled TGSS-NVSS catalog."""
    try:
        return pkg_resources.resource_filename('foresight', 'data/spidxcat_v1.1b.fits')
    except:
        # Fallback for development
        return os.path.join(os.path.dirname(__file__), 'data', 'spidxcat_v1.1b.fits')

from .core import (
    get_pointing_center_and_frequency,
    load_tgss_nvss_catalog,
    filter_sources_in_fov,
    create_wsclean_source_list,
    create_fits_mask,
    parse_source_types,
)

__all__ = [
    "get_pointing_center_and_frequency",
    "load_tgss_nvss_catalog", 
    "filter_sources_in_fov",
    "create_wsclean_source_list",
    "create_fits_mask",
    "parse_source_types",
    "get_catalog_path",
]