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
* **Moons** are analytic: limb darkening, maria, phase terminator, cracks
  that still leak light, and bump-mapped relief. The relief is a real
  finite-difference gradient of a height field, so craters catch the light
  on one rim and fall into shadow on the other instead of being painted on.
  Two details matter when tuning it: the difference step has to stay well
  inside one cell of the finest octave, and the height field wants a low
  `bump_gain` or every octave contributes the same slope and the surface
  turns to sand.
* **Debris fields** (`debris_field`) scatter chunks around a broken moon.
  Each chunk is an ordinary moon dict, so it inherits the same lighting and
  relief, with a faceted outline instead of a smooth one. Note that a
  chunk's normal space is a full sphere no matter how small it looks, so
  its texture scales belong in the same range as the moon's.
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

A body near the corner of a face looks stretched when you open the PNG on
its own. That is the cube projection doing its job - the skybox undoes it
and the moon is round again in game.

## Shipped assets

`previews/shattered/` holds the chosen sky as six 1024px cube faces, and
`previews/shattered_panorama_4096.jpg` is the same sky as one panorama.
Everything is reproducible from the generator, which is why the lossless
panorama is not committed:

```bash
python3 sky_generator.py shattered --width 4096 --faces --face-size 2048
```

Face size is a judgement call rather than a quality ceiling: at 1024 the
moon lands about 230px across, at 2048 about 460px, and the relief and the
fissures are worth the bigger faces only if the moon is meant to be looked
at rather than glanced at.

## Tuning

Each concept is a dict in `sky_generator.py`. The values that matter most:

* `scale` on a noise layer is *features per unit direction* - 1.5 is a few
  big masses across the sky, 8 is fist-sized detail.
* `strength` is added in linear light. Past roughly 0.3 a layer stops being
  glow and becomes a background colour.
* `lo`/`hi`/`power` decide how much of the sky a layer touches at all.
  Raising `lo` is what buys back empty black sky.
