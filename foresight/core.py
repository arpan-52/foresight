#!/usr/bin/env python3

import numpy as np
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.wcs import WCS
import casacore.tables as pt

def get_pointing_center_and_frequency(ms_file):
    """Extract pointing center and observation frequency from MS file."""
    # Read FIELD table for pointing center
    field_table = pt.table(f"{ms_file}/FIELD")
    phase_dir = field_table.getcol("PHASE_DIR")
    field_table.close()
    
    # Get RA, DEC of first field (assuming single pointing)
    ra_rad = phase_dir[0, 0, 0]  # radians
    dec_rad = phase_dir[0, 0, 1]  # radians
    
    ra_deg = np.degrees(ra_rad)
    dec_deg = np.degrees(dec_rad)
    
    # Read SPECTRAL_WINDOW table for frequency
    spw_table = pt.table(f"{ms_file}/SPECTRAL_WINDOW")
    chan_freq = spw_table.getcol("CHAN_FREQ")
    spw_table.close()
    
    # Get central frequency (assuming first SPW)
    freq_hz = np.mean(chan_freq[0])
    
    return ra_deg, dec_deg, freq_hz

def load_tgss_nvss_catalog(fits_file):
    """Load TGSS-NVSS catalog from FITS file."""
    with fits.open(fits_file) as hdul:
        data = hdul[1].data  # Assuming binary table in first extension
    return data

def parse_source_types(type_string):
    """Parse source type string into list of valid types."""
    type_mapping = {
        'single': 'S',
        's': 'S',
        'multiple': 'M', 
        'm': 'M',
        'complex': 'C',
        'c': 'C',
        'upper': 'L',
        'upper-limit': 'L',
        'l': 'L',
        'lower': 'U',
        'lower-limit': 'U',
        'u': 'U',
        'island': 'I',
        'i': 'I'
    }
    
    # Split by comma and clean up
    types_input = [t.strip().lower() for t in type_string.split(',')]
    source_types = []
    
    for t in types_input:
        if t in type_mapping:
            mapped_type = type_mapping[t]
            if mapped_type not in source_types:  # Avoid duplicates
                source_types.append(mapped_type)
        else:
            print(f"Warning: Unknown source type '{t}' ignored")
    
    if not source_types:
        print("No valid source types specified, defaulting to 'S' (single)")
        source_types = ['S']
    
    return source_types

def filter_sources_in_fov(catalog, center_ra, center_dec, imsize, cellsize_arcsec, source_types, debug=False):
    """Filter sources within image field of view."""
    # Calculate FOV more conservatively - use full diagonal
    fov_diagonal_arcsec = np.sqrt(2) * imsize * cellsize_arcsec
    fov_radius_deg = (fov_diagonal_arcsec / 2.0) / 3600.0
    
    if debug:
        print(f"Image FOV diagonal: {fov_diagonal_arcsec:.1f} arcsec")
        print(f"Search radius: {fov_radius_deg:.3f}° ({fov_radius_deg*3600:.1f} arcsec)")
    
    # Create SkyCoord objects
    center = SkyCoord(center_ra * u.deg, center_dec * u.deg)
    sources = SkyCoord(catalog['RA'] * u.deg, catalog['DEC'] * u.deg)
    
    # Calculate separations
    separations = center.separation(sources)
    
    # Debug output
    if debug:
        debug_radius_deg = fov_radius_deg * 1.5  # 50% larger for debugging
        debug_mask = separations.deg <= debug_radius_deg
        print(f"\nDEBUG: Sources within {debug_radius_deg:.3f}° ({debug_radius_deg*3600:.0f} arcsec):")
        
        for stype in ['S', 'M', 'C', 'L', 'U', 'I']:
            debug_count = np.sum((catalog['S_code'] == stype) & debug_mask)
            if debug_count > 0:
                print(f"  {stype}: {debug_count} sources")
                # Show first few of each type
                type_sources = catalog[(catalog['S_code'] == stype) & debug_mask][:3]
                for src in type_sources:
                    sep_arcsec = center.separation(SkyCoord(src['RA'] * u.deg, src['DEC'] * u.deg)).arcsec
                    flux_nvss = src['Total_flux_NVSS']
                    flux_tgss = src['Total_flux_TGSS'] 
                    print(f"    RA={src['RA']:.4f}°, DEC={src['DEC']:.4f}°, sep={sep_arcsec:.1f}\", "
                          f"NVSS={flux_nvss:.3f}Jy, TGSS={flux_tgss:.3f}Jy")
    
    # Create source type mask
    type_mask = np.zeros(len(catalog), dtype=bool)
    for source_type in source_types:
        type_mask |= (catalog['S_code'] == source_type)
    
    # Filter by FOV and source type
    mask = (separations.deg <= fov_radius_deg) & type_mask
    
    if debug:
        print(f"\nFinal selection with types {source_types}:")
        for stype in ['S', 'M', 'C', 'L', 'U', 'I']:
            count = np.sum((catalog['S_code'] == stype) & (separations.deg <= fov_radius_deg))
            selected = stype in source_types
            status = "✓" if selected else "✗"
            print(f"  {stype}: {count:5d} sources {status}")
    
    return catalog[mask]

def deg_to_hms_dms(ra_deg, dec_deg):
    """Convert degrees to hh:mm:ss.sss and dd.mm.ss.sss format for WSClean."""
    # Convert to hours and degrees
    ra_hours = ra_deg / 15.0
    
    # RA conversion
    ra_h = int(ra_hours)
    ra_m = int((ra_hours - ra_h) * 60)
    ra_s = ((ra_hours - ra_h) * 60 - ra_m) * 60
    ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:06.3f}"
    
    # DEC conversion
    dec_sign = '+' if dec_deg >= 0 else '-'
    dec_abs = abs(dec_deg)
    dec_d = int(dec_abs)
    dec_m = int((dec_abs - dec_d) * 60)
    dec_s = ((dec_abs - dec_d) * 60 - dec_m) * 60
    dec_str = f"{dec_sign}{dec_d:02d}.{dec_m:02d}.{dec_s:06.3f}"
    
    return ra_str, dec_str

def create_wsclean_source_list(filtered_catalog, obs_freq_hz, output_file):
    """Create WSClean source list from filtered catalog - all positions with individual reference frequencies."""
    
    with open(output_file, 'w') as f:
        # Write header without default reference frequency
        f.write("Format = Name, Type, Ra, Dec, I, SpectralIndex, LogarithmicSI, ReferenceFrequency, MajorAxis, MinorAxis, Orientation\n")
        
        # Write ALL sources (just use positions)
        source_count = 0
        for source in filtered_catalog:
            # Convert coordinates
            ra_str, dec_str = deg_to_hms_dms(source['RA'], source['DEC'])
            
            # Get spectral index (handle invalid values)
            spidx = source['Spidx']
            if not np.isfinite(spidx):
                spidx = -0.7  # Default synchrotron spectral index
            
            # Format spectral index as array
            spidx_str = f"[{spidx}]"
            
            # Choose reference frequency and flux based on source type
            if source['S_code'] in ['L']:  # NVSS-only detection
                ref_freq_hz = 1.4e9
                flux = source['Total_flux_NVSS']
            elif source['S_code'] in ['U']:  # TGSS-only detection  
                ref_freq_hz = 150e6
                flux = source['Total_flux_TGSS']
            else:  # S, M, C, I - choose based on observation frequency
                obs_freq_mhz = obs_freq_hz / 1e6
                if abs(obs_freq_mhz - 1400) < abs(obs_freq_mhz - 150):
                    ref_freq_hz = 1.4e9
                    flux = source['Total_flux_NVSS']
                else:
                    ref_freq_hz = 150e6
                    flux = source['Total_flux_TGSS']
            
            # Use minimum flux for position-only purposes
            if flux <= 0 or not np.isfinite(flux):
                flux = 1e-6  # Minimal flux just for position
            
            # Write source line with individual reference frequency
            source_name = f"s{source_count}"
            f.write(f"{source_name},POINT,{ra_str},{dec_str},{flux:.6e},{spidx_str},false,{ref_freq_hz},,,\n")
            source_count += 1
    
    return source_count

def create_fits_mask(filtered_catalog, obs_freq_hz, center_ra, center_dec, output_file, imsize, cellsize_arcsec):
    """Create a FITS mask from filtered catalog sources - ALL positions regardless of flux."""
    
    # Create WCS header - WSClean uses specific conventions
    header = fits.Header()
    
    # Basic image parameters
    header['SIMPLE'] = True
    header['BITPIX'] = -32  # 32-bit float
    header['NAXIS'] = 2
    header['NAXIS1'] = imsize
    header['NAXIS2'] = imsize
    
    # WCS parameters - WSClean convention
    header['CTYPE1'] = 'RA---SIN'
    header['CTYPE2'] = 'DEC--SIN'
    header['CRVAL1'] = center_ra
    header['CRVAL2'] = center_dec
    header['CRPIX1'] = imsize // 2 + 1  # FITS uses 1-based indexing
    header['CRPIX2'] = imsize // 2 + 1
    header['CDELT1'] = -cellsize_arcsec / 3600.0  # Negative for RA (standard)
    header['CDELT2'] = cellsize_arcsec / 3600.0   # Positive for DEC
    header['CUNIT1'] = 'deg'
    header['CUNIT2'] = 'deg'
    
    # Additional standard headers
    header['EQUINOX'] = 2000.0
    header['RADESYS'] = 'FK5'
    header['BUNIT'] = 'JY/BEAM'
    header['BMAJ'] = cellsize_arcsec / 3600.0 * 4  # Rough beam estimate
    header['BMIN'] = cellsize_arcsec / 3600.0 * 4
    header['BPA'] = 0.0
    header['RESTFRQ'] = obs_freq_hz
    header['OBSRA'] = center_ra
    header['OBSDEC'] = center_dec
    header['OBSERVER'] = 'WSClean'
    header['TELESCOP'] = 'GENERIC'
    header['OBJECT'] = 'MASK'
    
    # Create WCS object
    wcs = WCS(header)
    
    # Initialize mask array (0 = masked, 1 = not masked in WSClean convention)
    mask_data = np.zeros((imsize, imsize), dtype=np.float32)
    
    # Convert ALL source positions to pixel coordinates
    valid_source_count = 0
    for source in filtered_catalog:
        # Convert RA/DEC to pixel coordinates - NO FLUX FILTERING
        ra_deg = source['RA']
        dec_deg = source['DEC']
        
        try:
            px, py = wcs.wcs_world2pix(ra_deg, dec_deg, 1)  # 1-based FITS convention
            px = int(round(px - 1))  # Convert to 0-based Python indexing
            py = int(round(py - 1))
            
            # Check if source is within image bounds
            if 0 <= px < imsize and 0 <= py < imsize:
                # Set single pixel mask at source position
                mask_data[py, px] = 1.0
                valid_source_count += 1
                
        except Exception as e:
            print(f"Warning: Could not convert source at RA={ra_deg:.6f}, DEC={dec_deg:.6f} to pixels: {e}")
            continue
    
    # Create FITS file
    hdu = fits.PrimaryHDU(data=mask_data, header=header)
    hdu.writeto(output_file, overwrite=True)
    
    return valid_source_count