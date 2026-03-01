#!/usr/bin/env python3

import argparse
import sys
import os
from . import get_catalog_path
from .core import (
    get_pointing_center_and_frequency,
    load_tgss_nvss_catalog,
    filter_sources_in_fov,
    create_wsclean_source_list,
    create_fits_mask,
    create_flux_image,
    parse_source_types,
)

def parse_ra(ra_str):
    """Parse RA in HH:MM:SS.sss format to decimal degrees."""
    parts = ra_str.split(':')
    if len(parts) != 3:
        raise ValueError(f"RA must be in HH:MM:SS.sss format, got: {ra_str}")
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    ra_deg = (hours + minutes/60.0 + seconds/3600.0) * 15.0  # Convert hours to degrees
    if ra_deg < 0 or ra_deg > 360:
        raise ValueError(f"RA out of range (0-360°): {ra_deg}")
    return ra_deg

def parse_dec(dec_str):
    """Parse DEC in ±DD:MM:SS.sss format to decimal degrees."""
    is_negative = dec_str.startswith('-')
    dec_str = dec_str.lstrip('+-')
    parts = dec_str.split(':')
    if len(parts) != 3:
        raise ValueError(f"DEC must be in ±DD:MM:SS.sss format, got: {dec_str}")
    degrees = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    dec_deg = degrees + minutes/60.0 + seconds/3600.0
    if is_negative:
        dec_deg = -dec_deg
    if dec_deg < -90 or dec_deg > 90:
        raise ValueError(f"DEC out of range (-90 to +90°): {dec_deg}")
    return dec_deg

def main():
    parser = argparse.ArgumentParser(
        description="Generate WSClean source list and FITS mask from TGSS-NVSS catalog",
        epilog="""
Source types:
  S (single): Point-like sources with no other detections in same island
  M (multiple): Double-lobe radio galaxies or collections of nearby sources  
  C (complex): Part of complex objects (e.g. one lobe of radio galaxy)
  L (upper-limit): NVSS detection with no TGSS detection
  U (lower-limit): TGSS detection with no NVSS detection
  I (island): Global values of complex islands
  
Output types:
  mask: Binary mask (1=source, 0=background) - position only
  flux: Flux image (pixel value = flux in Jy at obs frequency) - with spectral index extrapolation
  
Examples (MS file mode):
  foresight obs.ms --imsize 4096 --cellsize 1.5
  foresight obs.ms --imsize 9600 --cellsize 1.0 --source-types S,M,L --output-type flux
  foresight obs.ms --imsize 8192 --cellsize 2.0 --source-types all

Examples (Direct coordinates mode):
  foresight --ra 12:34:56.789 --dec=-45:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5
  foresight --ra 00:00:00.0 --dec=+90:00:00.0 --freq 150e6 --imsize 8192 --cellsize 2.0 --output-type flux
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ms_file", nargs='?', help="Measurement Set file (optional if using --ra --dec --freq)")
    parser.add_argument("--ra", help="RA in HH:MM:SS.sss format (alternative to MS file)")
    parser.add_argument("--dec", help="DEC in ±DD:MM:SS.sss format (alternative to MS file)")
    parser.add_argument("--freq", type=float, help="Observation frequency in Hz (alternative to MS file)")
    parser.add_argument("--imsize", type=int, required=True, help="Image size in pixels (square)")
    parser.add_argument("--cellsize", type=float, required=True, help="Cell size in arcseconds")
    parser.add_argument("--source-types", default="S", 
                       help="Comma-separated list of source types to include: S,M,C,L,U,I or single,multiple,complex,upper,lower,island or 'all'")
    parser.add_argument("--output-type", default="mask", choices=["mask", "flux"],
                       help="Output type: 'mask' for binary mask (position only) or 'flux' for flux image with spectral index extrapolation (default: mask)")
    parser.add_argument("-o", "--output", default="sources.txt", help="Output source list file")
    parser.add_argument("-m", "--mask", default="source_mask.fits", help="Output FITS mask/flux file")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    # Determine mode: MS file or direct coordinates
    if args.ra and args.dec and args.freq:
        # Direct coordinates mode
        if args.ms_file:
            print("Error: Cannot specify both MS file and --ra/--dec/--freq")
            sys.exit(1)
        try:
            ra_center = parse_ra(args.ra)
            dec_center = parse_dec(args.dec)
            obs_freq = args.freq
            print(f"Using direct coordinates:")
            print(f"Pointing center: RA={ra_center:.6f}°, DEC={dec_center:.6f}°")
            print(f"Observation frequency: {obs_freq/1e6:.1f} MHz")
        except ValueError as e:
            print(f"Error parsing coordinates: {e}")
            sys.exit(1)
    elif args.ms_file:
        # MS file mode
        if args.ra or args.dec or args.freq:
            print("Error: Cannot specify both MS file and --ra/--dec/--freq")
            sys.exit(1)
        print(f"Reading pointing center and frequency from {args.ms_file}")
        try:
            ra_center, dec_center, obs_freq = get_pointing_center_and_frequency(args.ms_file)
            print(f"Pointing center: RA={ra_center:.6f}°, DEC={dec_center:.6f}°")
            print(f"Observation frequency: {obs_freq/1e6:.1f} MHz")
        except Exception as e:
            print(f"Error reading MS file: {e}")
            sys.exit(1)
    else:
        print("Error: Must provide either MS file or --ra/--dec/--freq arguments")
        parser.print_help()
        sys.exit(1)
    
    # Always use bundled catalog - no option to override
    catalog_file = get_catalog_path()
    if not os.path.exists(catalog_file):
        print(f"Error: Bundled TGSS-NVSS catalog not found at {catalog_file}")
        print("Package installation may be corrupted. Please reinstall foresight.")
        sys.exit(1)
    
    # Parse source types
    if args.source_types.lower() == 'all':
        source_types = ['S', 'M', 'C', 'L', 'U', 'I']
        print("Using all source types: S,M,C,L,U,I")
    else:
        source_types = parse_source_types(args.source_types)
    
    print(f"Loading bundled TGSS-NVSS catalog")
    try:
        catalog = load_tgss_nvss_catalog(catalog_file)
        print(f"Loaded {len(catalog)} sources from catalog")
    except Exception as e:
        print(f"Error loading catalog: {e}")
        sys.exit(1)
    
    print(f"Filtering sources within image FOV (imsize={args.imsize}, cellsize={args.cellsize} arcsec)")
    filtered_sources = filter_sources_in_fov(catalog, ra_center, dec_center, args.imsize, args.cellsize, source_types, debug=args.debug)
    print(f"Found {len(filtered_sources)} sources in image FOV")
    
    if len(filtered_sources) == 0:
        print("No sources found in image FOV!")
        sys.exit(1)
    
    print(f"Creating WSClean source list: {args.output}")
    source_count = create_wsclean_source_list(filtered_sources, obs_freq, args.output)
    
    # Create FITS output (mask or flux image)
    if args.output_type == "flux":
        print(f"Creating FITS flux image: {args.mask}")
        mask_count = create_flux_image(filtered_sources, obs_freq, ra_center, dec_center, args.mask, args.imsize, args.cellsize)
        output_description = "flux image"
    else:
        print(f"Creating FITS binary mask: {args.mask}")
        mask_count = create_fits_mask(filtered_sources, obs_freq, ra_center, dec_center, args.mask, args.imsize, args.cellsize)
        output_description = "binary mask"
    
    # Calculate field of view from image parameters
    fov_arcsec = args.imsize * args.cellsize
    fov_arcmin = fov_arcsec / 60.0
    fov_deg = fov_arcmin / 60.0
    
    print(f"\nSummary:")
    print(f"Image size: {args.imsize}x{args.imsize} pixels")
    print(f"Cell size: {args.cellsize} arcsec/pixel") 
    print(f"Image FOV: {fov_deg:.2f}° ({fov_arcmin:.1f}' or {fov_arcsec:.0f}\")")
    print(f"Source types: {', '.join(source_types)}")
    print(f"Total sources found: {len(filtered_sources)}")
    print(f"Source list: {source_count} sources -> {args.output}")
    print(f"{output_description.capitalize()}: {mask_count} sources -> {args.mask}")
    
    if source_count != len(filtered_sources):
        print(f"Note: {len(filtered_sources) - mask_count} sources fell outside image boundaries")
    
    print("Done!")

if __name__ == "__main__":
    main()