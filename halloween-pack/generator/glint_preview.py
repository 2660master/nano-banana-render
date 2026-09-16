import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255.0

def sample(tex, u, v):
    """bilinear, wrapping"""
    S0, S1 = tex.shape[0], tex.shape[1]
    x = (u % 1.0) * S1 - 0.5; y = (v % 1.0) * S0 - 0.5
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    x0 %= S1; y0 %= S0; x1 = (x0 + 1) % S1; y1 = (y0 + 1) % S0
    return (tex[y0, x0] * (1 - fx) * (1 - fy) + tex[y0, x1] * fx * (1 - fy) +
            tex[y1, x0] * (1 - fx) * fy + tex[y1, x1] * fx * fy)

def glint_uv(u, v, scale, tx=0.31, ty=0.17, rot=10.0):
    """vanilla glint texture matrix: translate, rotate 10 deg, scale"""
    a = np.radians(rot)
    su = (u * np.cos(a) - v * np.sin(a)) * scale + tx
    sv = (u * np.sin(a) + v * np.cos(a)) * scale + ty
    return su, sv

def sword16():
    im = Image.new("RGB", (16, 16), (0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.line([(3, 12), (11, 4)], fill=(118, 128, 140), width=2)
    dr.line([(4, 12), (11, 5)], fill=(176, 188, 200), width=1)
    dr.line([(1, 14), (4, 11)], fill=(92, 62, 34), width=2)
    dr.line([(2, 10), (5, 13)], fill=(150, 116, 52), width=2)
    dr.point([(11, 3), (12, 4)], fill=(210, 222, 232))
    a = np.asarray(im).astype(np.float64) / 255.0
    mask = a.sum(-1) > 0.02
    return a, mask

def item_sim(tex, N=16, SS=10, px=26):
    base, mask = sword16()
    out = base.copy()
    su = (np.arange(N * SS) + 0.5) / (N * SS)
    uu, vv = np.meshgrid(su, su)
    gu, gv = glint_uv(uu, vv, 8.0)
    g = sample(tex, gu, gv)
    g = g.reshape(N, SS, N, SS, 3).mean(axis=(1, 3))     # mip-average per item pixel
    out = np.clip(base + g ** 2 * mask[..., None], 0, 1)
    img = Image.fromarray((out * 255).astype(np.uint8)).resize((N * px, N * px), Image.NEAREST)
    return img

def armor_sim(tex, W=250, H=330):
    """chestplate front: armor-layer UV ~ u 0.3125-0.4375, v 0.625-1.0, glint scale 0.16"""
    u = np.linspace(0.3125, 0.4375, W)[None, :] * np.ones((H, 1))
    v = np.linspace(0.625, 1.0, H)[:, None] * np.ones((1, W))
    gu, gv = glint_uv(u, v, 0.16)
    g = sample(tex, gu, gv)
    base = np.zeros((H, W, 3)) + np.array([0.33, 0.35, 0.40])
    yy = np.linspace(0, 1, H)[:, None, None]
    base = base * (1.12 - 0.35 * yy)
    out = np.clip(base + g ** 2, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))

def tile(tex, n=2, size=250):
    im = Image.fromarray((tex * 255).astype(np.uint8))
    big = Image.new("RGB", (im.width * n, im.height * n))
    for i in range(n):
        for j in range(n):
            big.paste(im, (i * im.width, j * im.height))
    return big.resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    d = sys.argv[1]
    it = load(f"{d}/enchanted_glint_item.png")
    ar = load(f"{d}/enchanted_glint_armor.png")
    W, H = 1180, 900
    c = Image.new("RGB", (W, H), (16, 14, 20))
    dr = ImageDraw.Draw(c)
    fb = ImageFont.truetype(FONTB, 22); f = ImageFont.truetype(FONT, 15)
    fs = ImageFont.truetype(FONTB, 15)
    dr.text((26, 20), "ORANJE POMPOEN-GLINT", font=ImageFont.truetype(FONTB, 30), fill=(255, 158, 44))
    dr.text((28, 58), "enchanted_glint_item.png (256px)  +  enchanted_glint_armor.png (1024px) - beide naadloos tilebaar",
            font=f, fill=(180, 172, 190))
    y0 = 100
    c.paste(Image.fromarray((it * 255).astype(np.uint8)).resize((250, 250), Image.LANCZOS), (26, y0))
    c.paste(tile(it, 2, 250), (296, y0))
    c.paste(Image.fromarray((ar * 255).astype(np.uint8)).resize((250, 250), Image.LANCZOS), (620, y0))
    c.paste(tile(ar, 2, 250), (890, y0))
    for x, t in [(26, "ITEM-textuur"), (296, "2x2 getegeld"), (620, "ARMOR-textuur"), (890, "2x2 getegeld")]:
        dr.text((x, y0 + 256), t, font=fs, fill=(210, 200, 220))
    y1 = 400
    dr.text((26, y1), "ZO ZIET HET ER IN-GAME UIT (echte glint-schaal gesimuleerd)", font=fb, fill=(255, 158, 44))
    c.paste(item_sim(it, px=24), (40, y1 + 40))
    dr.text((40, y1 + 40 + 392), "item: glint x8 getegeld -> oranje schittering", font=fs, fill=(210, 200, 220))
    c.paste(armor_sim(ar), (520, y1 + 40))
    dr.text((520, y1 + 40 + 336), "harnas-borststuk: glint x0.16 -> grote zachte pompoenen", font=fs, fill=(210, 200, 220))
    c.save(f"{d}/glint_preview.png", optimize=True)
    print("ok")
