# Foresight
Foresight is a Psychic-type Pokémon move that allows the user to foresee the near future. I've always been a big fan of Noctowl, one of the Pokémon known for using this attack. Inspired by that, the Foresight software now integrates the TGSS and NVSS catalogs—almost like seeing into the future—to predict and identify known source positions.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7746d954-fb07-4b23-9ab7-4b6fb43686ef" />

## Description

Foresight creates WSClean-compatible source lists and FITS masks from the TGSS-NVSS spectral index catalog. Given a measurement set and the catalog, it automatically:

- Extracts pointing center and observation frequency from MS
- Finds catalog sources within the image field of view
- Creates WSClean source list with appropriate reference frequencies
- Generates FITS mask for constraining deconvolution to known source positions
- Generates a flux image for the relevant patch of the sky at the observation frequency (with spectral index extrapolation)

## Catalog

This package uses the TGSS-NVSS spectral index catalog (~111 MB, 1.4 million sources) from [de Gasperin, Intema & Frail, MNRAS 474, 5008 (2018)](https://academic.oup.com/mnras/article/474/4/5008/4712230). The catalog is stored using Git LFS and must be pulled before use.

Original source: http://tgssadr.strw.leidenuniv.nl/catalogs/spidxcat_v1.1b.fits

## Installation

### 1. Install Git LFS

Git LFS is required to download the catalog file (~111 MB).

**Linux (Debian/Ubuntu):**
```bash
sudo apt install git-lfs
```

**Linux (Arch):**
```bash
sudo pacman -S git-lfs
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install git-lfs
```

**macOS (Homebrew):**
```bash
brew install git-lfs
```

**Windows:**
Download and run the installer from https://git-lfs.com

### 2. Initialize Git LFS and clone

```bash
# Initialize Git LFS (one-time setup)
git lfs install

# Clone the repository
git clone https://github.com/yourusername/foresight.git
cd foresight

# Pull LFS files (downloads the catalog)
git lfs pull

# Install the package
pip install -e .
```

If you already cloned without LFS, just run:
```bash
cd foresight
git lfs install
git lfs pull
pip install -e .
```

## Quick Start

**Binary Mask (position only):**
```bash
# Usage with an MS file 
foresight observation.ms --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug

# Usage with direct coordinates
# Note: For negative declinations, use --dec=-45:30:22.456 (with equals sign)
foresight --ra 12:34:56.789 --dec=-45:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug
```

**Flux Image (with spectral index extrapolation):**
```bash
# Usage with an MS file 
foresight observation.ms --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug --output-type flux

# Usage with direct coordinates
foresight --ra 12:34:56.789 --dec=-15:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug --output-type flux
```

## Spectral Index

The flux image uses catalog spectral indices to extrapolate flux to observation frequency:

**Formula:** S(ν) = S₀ × (ν/ν₀)^α

Where S₀ is the catalog flux at reference frequency (NVSS: 1.4 GHz, TGSS: 150 MHz), α is the spectral index (or -0.7 if invalid).

**Smart selection:** 
- Closer to TGSS (150 MHz)? Prefer TGSS, fallback to NVSS
- Closer to NVSS (1.4 GHz)? Prefer NVSS, fallback to TGSS
- Skip if both invalid

**Example:** Observation at 200 MHz with NVSS detection (100 mJy @ 1.4 GHz, spidx -0.7) → S(200 MHz) = 100 × (200/1400)^(-0.7) = 329 mJy

## Options

```
--ra HH:MM:SS.sss        Right Ascension (alternative to MS file)
--dec ±DD:MM:SS.sss      Declination (use --dec=-DD:MM:SS.sss for negative values)
--freq Hz                Observation frequency in Hz
--imsize PIXELS          Image size in pixels (required)
--cellsize ARCSEC        Cell size in arcseconds (required)
--output-type mask|flux  Output type: mask (default) or flux with spectral index
--source-types TYPES     Source types to include: S,M,C,L,U,I or 'all' (default: S)
-o, --output FILE        Source list filename (default: sources.txt)
-m, --mask FILE          FITS mask/flux filename (default: source_mask.fits)
--debug                  Enable debug output
```

## Source Types

- **S**: Single point-like sources
- **M**: Multiple/double-lobe sources
- **C**: Complex objects  
- **L**: NVSS-only (upper limit, no TGSS detection)
- **U**: TGSS-only (lower limit, no NVSS detection)
- **I**: Island global values

## Output

**WSClean source list** (sources.txt):
- Standard WSClean format with spectral index for flux extrapolation

**FITS mask/flux** (source_mask.fits):
- Binary mask: pixel = 1 (source) or 0 (background)
- Flux image: pixel = flux in Jy at observation frequency

## Usage with WSClean

```bash
wsclean -fits-mask source_mask.fits -size 4096 4096 -scale 1.5arcsec observation.ms
```

## Troubleshooting

**Error: "No SIMPLE card found, this file does not appear to be a valid FITS file"**

This means the catalog file wasn't downloaded properly. The file is an LFS pointer instead of the actual data. Run:
```bash
git lfs install
git lfs pull
```

**Error: "argument --dec: expected one argument"**

For negative declinations, use the equals sign syntax:
```bash
--dec=-45:30:22.456   # Correct
--dec -45:30:22.456   # Wrong (parsed as separate argument)
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- astropy >= 5.0.0
- python-casacore
- Git LFS (for catalog download)

## Citation

If you use this tool, please cite the TGSS-NVSS spectral index catalog:
> de Gasperin, Intema & Frail, MNRAS, 474, 5008 (2018)

## License

MIT License - see LICENSE file for details.
