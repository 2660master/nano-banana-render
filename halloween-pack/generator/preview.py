import sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import skylib, concepts

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CAM = {"bloodmoon": (168, 26, 86), "nebula": (112, 27, 100), "graveyard": (312, 16, 88),
       "witching": (268, 28, 92), "void": (250, 16, 90)}

def tonemap(rgb):
    """Luminance-based rolloff: keeps colour in the bright cores instead of clipping to white."""
    x = np.clip(rgb, 0, None)
    L = x @ np.array([0.2126, 0.7152, 0.0722])
    Ln = L / (1.0 + L * 0.45)
    x = x * (Ln / np.maximum(L, 1e-6))[..., None]
    w = np.clip((L - 0.9) / 1.3, 0, 1) ** 1.5 * 0.45
    x = x * (1 - w)[..., None] + w[..., None] * np.clip(Ln, 0, 1)[..., None]
    x = np.clip(x * 1.10, 0, 1)
    return (x ** (1 / 1.05) * 255 + 0.5).astype(np.uint8)

def render(slug, fn, W=1280, H=720, PW=1280):
    yaw, pitch, fov = CAM[slug]
    d = skylib.perspective_dirs(W, H, fov, yaw, pitch)
    persp = tonemap(fn(d))
    PH = PW // 2
    dp = skylib.equirect_dirs(PW, PH, lon_offset=np.radians(yaw - 180))
    pano_full = tonemap(fn(dp))
    r0 = int((90 - 58) / 180 * PH); r1 = int((90 + 42) / 180 * PH)
    return persp, pano_full[r0:r1]

def compose(cid, name, desc, persp, pano):
    W = persp.shape[1]
    TH, GAP, BH = 92, 14, 30
    ph = pano.shape[0]
    canvas = Image.new("RGB", (W, TH + persp.shape[0] + GAP + BH + ph + 16), (14, 12, 18))
    dr = ImageDraw.Draw(canvas)
    dr.rectangle([0, 0, W, TH], fill=(24, 18, 28))
    dr.text((28, 20), f"{cid}. {name.upper()}", font=ImageFont.truetype(FONTB, 38), fill=(255, 158, 44))
    dr.text((30, 62), desc, font=ImageFont.truetype(FONT, 19), fill=(190, 180, 200))
    canvas.paste(Image.fromarray(persp), (0, TH))
    y = TH + persp.shape[0] + GAP
    dr.text((28, y + 6), "360° PANORAMA  (N - O - Z - W)", font=ImageFont.truetype(FONTB, 16), fill=(150, 140, 160))
    canvas.paste(Image.fromarray(pano), (0, y + BH))
    d2 = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONTB, 15)
    for i, lab in enumerate(["N", "O", "Z", "W", "N"]):
        x = int(i * W / 4)
        x = min(max(x, 12), W - 24)
        d2.text((x, y + BH + pano.shape[0] - 24), lab, font=f, fill=(230, 220, 235),
                stroke_width=3, stroke_fill=(0, 0, 0))
    return canvas

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    sheets = []
    for cid, name, slug, fn, desc in concepts.CONCEPTS:
        t = time.time()
        persp, pano = render(slug, fn)
        img = compose(cid, name, desc, persp, pano)
        path = f"{out}/sky_{cid}_{slug}.png"
        img.save(path, optimize=True)
        sheets.append((path, img))
        print(f"{path}  {img.size}  {time.time()-t:.1f}s")
