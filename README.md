# Foresight
Foresight is a Psychic-type Pokémon move that allows the user to foresee the near future. I’ve always been a big fan of Noctowl, one of the Pokémon known for using this attack. Inspired by that, the Foresight software now integrates the TGSS and NVSS catalogs—almost like seeing into the future—to predict and identify known source positions.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7746d954-fb07-4b23-9ab7-4b6fb43686ef" />

## Description

Foresight creates WSClean-compatible source lists and FITS masks from the TGSS-NVSS spectral index catalog. Given a measurement set and the catalog, it automatically:

- Extracts pointing center and observation frequency from MS
- Finds catalog sources within the image field of view
- Creates WSClean source list with appropriate reference frequencies
- Generates FITS mask for constraining deconvolution to known source positions
- Generate a best possible FITS image for the relevant patch of the sky at those frequencies

## Installation

```bash
git clone https://github.com/yourusername/foresight.git
cd foresight
pip install -e .
```

## Quick Start
**Binary Mask (position only):**
```bash
# Usage with an MS file 
foresight observation.ms --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug
# Usage with any custom direction or frequency
foresight --ra 12:34:56.789 --dec -45:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug
```

**Flux Image (with spectral index):**
```bash
# Usage with an MS file 
foresight observation.ms --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug --output-type flux
# Usage with any custom direction or frequency
foresight --ra 12:34:56.789 --dec -45:30:22.456 --freq 1.4e9 --imsize 4096 --cellsize 1.5 --source-types S,M,L -o sources.txt -m mask.fits --debug --output-type flux
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
--dec ±DD:MM:SS.sss      Declination (alternative to MS file)  
--freq Hz                Observation frequency in Hz
--imsize PIXELS          Image size in pixels (required)
--cellsize ARCSEC        Cell size in arcseconds (required)
--output-type mask|flux  Output type: mask (default) or flux with spectral index
--source-types S,M,L     Source types to include (default: S)
-o, --output FILE        Source list filename (default: sources.txt)
-m, --mask FILE          FITS mask/flux filename (default: source_mask.fits)
--debug                  Enable debug output
```

## Source Types

- **S**: Single point-like sources
- **M**: Multiple/double-lobe sources
- **C**: Complex objects  
- **L**: NVSS-only (no TGSS detection)
- **U**: TGSS-only (no NVSS detection)
- **I**: Island global values

## Output

**WSClean source list** (sources.txt):
- Standard format with spectral index for flux extrapolation

**FITS mask/flux** (source_mask.fits):
- Binary mask: pixel = 1 (source) or 0 (background)
- Flux image: pixel = flux in Jy at observation frequency

## With WSClean

```bash
wsclean -fits-mask source_mask.fits -size 4096 4096 -scale 1.5arcsec observation.ms
```

## Requirements

- Python >= 3.8
- numpy >= 1.20.0
- astropy >= 5.0.0
- python-casacore

## License

MIT License - see LICENSE file for details.
