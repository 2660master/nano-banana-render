# Dark fantasy night skies

Procedural night-sky generator for a Minecraft skybox. Five concepts, all
built from the same renderer so they can be compared fairly and retuned by
editing numbers instead of repainting textures.

| # | Name | Character |
|---|------|-----------|
| 1 | Bloedmaan | huge blood-red moon breaking through drifting ash clouds |
| 2 | Verbrijzelde Maan | shattered moon and its fragments in a violet void |
| 3 | Spooklicht | grave-green aurora curtains under a cold pale moon |
| 4 | Asregen | smoke deck, drifting embers, a burning horizon |
| 5 | Heksenvuur | poison-green witchfire nebula with a green and a pale moon |

## How it works

The sky is rendered once as a seamless equirectangular panorama and then
projected onto cube faces. Nothing is painted by hand:

* **Nebulae and clouds** are 3D value-noise fbm sampled on the unit sphere,
  so there are no seams and no pinching at the poles. Each octave is
  rotated before it is sampled, which stops the noise lattice from drawing
  straight edges into the cloud silhouettes.
* **Cloud decks** are banded around an elevation, occlude what is behind
  them, and pick up rim light from the sky's key light. Decks flagged
  `over` are drawn after the moons, so a bank of ash can veil the moon.
* **Moons** are analytic: limb darkening, crater and mare texture, optional
  phase terminator and cracks.
* **Stars** are splatted with latitude-compensated kernels, so they stay
  round after the cube projection instead of smearing near the poles.

Everything accumulates in linear light and goes through an ACES-style
tonemap, so glow falls off the way light does rather than clipping to flat
colour. A little dither is added before quantising because 8-bit dark
gradients band badly otherwise.

## Usage

```bash
pip install numpy pillow

python3 sky_generator.py --list                     # the five concepts
python3 sky_generator.py --preview --width 2048     # preview cards, jpg
python3 sky_generator.py bloodmoon --faces          # 4096 pano + cube faces
python3 sky_generator.py --preview --width 512 --stats   # tuning numbers
```

`--stats` prints luminance percentiles per sky. A night sky should read
mostly black: luma median around 0.03-0.10 and p90 under about 0.35.
Anything well past that has turned into a wall of colour.

## Cube face convention

`--faces` writes `north/south/east/west/top/bottom.png`. The viewer stands
inside the cube, so each face uses `right = forward x up`: facing north,
east is on your right. `top` has north at the top of the image, `bottom`
has south at the top. With that layout all twelve cube edges line up
exactly, which `test_cube_seams.py` checks.

Different consumers want different rotations for `top` and `bottom`
(FabricSkyBoxes, OptiFine's atlas and a hand-written renderer all differ),
so check yours before shipping and rotate if needed.

```bash
python3 test_cube_seams.py
```

## Tuning

Each concept is a dict in `sky_generator.py`. The values that matter most:

* `scale` on a noise layer is *features per unit direction* - 1.5 is a few
  big masses across the sky, 8 is fist-sized detail.
* `strength` is added in linear light. Past roughly 0.3 a layer stops being
  glow and becomes a background colour.
* `lo`/`hi`/`power` decide how much of the sky a layer touches at all.
  Raising `lo` is what buys back empty black sky.
