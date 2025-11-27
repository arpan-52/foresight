# Foresight
Foresight is a Psychic-type Pokémon move that allows the user to foresee the near future. I’ve always been a big fan of Noctowl, one of the Pokémon known for using this attack. Inspired by that, the Foresight software now integrates the TGSS and NVSS catalogs—almost like seeing into the future—to predict and identify known source positions.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7746d954-fb07-4b23-9ab7-4b6fb43686ef" />

## Description

Foresight creates WSClean-compatible source lists and FITS masks from the TGSS-NVSS spectral index catalog. Given a measurement set and the catalog, it automatically:

- Extracts pointing center and observation frequency from MS
- Finds catalog sources within the image field of view
- Creates WSClean source list with appropriate reference frequencies
- Generates FITS mask for constraining deconvolution to known source positions

## Installation

```bash
git clone https://github.com/yourusername/foresight.git
cd foresight
pip install -e .
```

## Quick Start

```bash
# Usage with an MS file 
foresight observation.ms --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug
# Usage with any custom direction or frequency
foresight --ra 12:34:56.789 --dec -45:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug
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
