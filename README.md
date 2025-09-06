# Foresight

Radio astronomy source masking from TGSS-NVSS catalog for interferometric imaging.

## Description

Foresight creates WSClean-compatible source lists and FITS masks from the TGSS-NVSS spectral index catalog. Given a measurement set and the catalog, it automatically:

- Extracts pointing center and observation frequency from MS
- Finds catalog sources within the image field of view
- Creates WSClean source list with appropriate reference frequencies
- Generates FITS mask for constraining deconvolution to known source positions

## Installation

```bash
pip install foresight
```

Or install from source:
```bash
git clone https://github.com/yourusername/foresight.git
cd foresight
pip install -e .
```

## Quick Start

```bash
# Basic usage
foresight observation.ms tgss_nvss_catalog.fits --imsize 4096 --cellsize 1.5

# Select specific source types
foresight observation.ms catalog.fits --imsize 9600 --cellsize 1.0 --source-types S,M,L

# Custom output files
foresight observation.ms catalog.fits --imsize 8192 --cellsize 2.0 -o my_sources.txt -m my_mask.fits
```

## Source Types

- **S (single)**: Point-like sources with no other detections in same island
- **M (multiple)**: Double-lobe radio galaxies or collections of nearby sources  
- **C (complex)**: Part of complex objects (e.g. one lobe of radio galaxy)
- **L (upper-limit)**: NVSS detection with no TGSS detection
- **U (lower-limit)**: TGSS detection with no NVSS detection
- **I (island)**: Global values of complex islands

## Usage with WSClean

The generated mask can be used with WSClean for constrained cleaning:

```bash
wsclean -fits-mask source_mask.fits [other params] observation.ms
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- astropy >= 5.0.0
- python-casacore >= 3.5.0

## License

MIT License - see LICENSE file for details.
