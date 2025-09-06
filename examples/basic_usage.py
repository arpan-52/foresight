#!/usr/bin/env python3
"""
Basic usage example for foresight package.
"""

import foresight

# Example usage as a module
def example_usage():
    ms_file = "observation.ms" 
    catalog_file = "tgss_nvss_catalog.fits"
    imsize = 4096
    cellsize = 1.5  # arcsec
    source_types = ['S', 'M']  # Single and multiple sources
    
    # Get pointing info
    ra, dec, freq = foresight.get_pointing_center_and_frequency(ms_file)
    print(f"Pointing: RA={ra:.6f}°, DEC={dec:.6f}°, freq={freq/1e6:.1f} MHz")
    
    # Load catalog
    catalog = foresight.load_tgss_nvss_catalog(catalog_file)
    print(f"Loaded {len(catalog)} catalog sources")
    
    # Filter sources
    filtered = foresight.filter_sources_in_fov(catalog, ra, dec, imsize, cellsize, source_types)
    print(f"Found {len(filtered)} sources in FOV")
    
    # Create outputs
    source_count = foresight.create_wsclean_source_list(filtered, freq, "sources.txt")
    mask_count = foresight.create_fits_mask(filtered, freq, ra, dec, "mask.fits", imsize, cellsize)
    
    print(f"Created source list ({source_count}) and mask ({mask_count})")

if __name__ == "__main__":
    example_usage()
