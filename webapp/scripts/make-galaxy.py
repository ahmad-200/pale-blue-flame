"""Draw the page background: a spiral galaxy in the pale blue of a flame in microgravity.

It is a drawing made from noise and a few formulas, not a photograph or a star map.
The seed is fixed, so the same picture comes out every time.

    python3 scripts/make-galaxy.py            # writes public/img/galaxy.webp
    python3 scripts/make-galaxy.py preview.png
"""
import sys
import numpy as np
from PIL import Image

W, H = 2400, 1350
rng = np.random.default_rng(1990)          # the year of the Pale Blue Dot photograph


def fbm(base, octaves=6, persistence=0.55):
    """Fractal noise, 0..1: random grids at several sizes, smoothed and added."""
    total = np.zeros((H, W), np.float32)
    amp, norm = 1.0, 0.0
    for i in range(octaves):
        s = max(2, base >> i)
        small = rng.random((H // s + 2, W // s + 2)).astype(np.float32)
        big = Image.fromarray(small).resize((W + 2 * s, H + 2 * s), Image.Resampling.BICUBIC)
        total += amp * np.asarray(big)[s:s + H, s:s + W]
        norm += amp
        amp *= persistence
    total /= norm
    lo, hi = np.percentile(total, [1, 99])
    return np.clip((total - lo) / (hi - lo), 0, 1)


def blur(a, sigma):
    """Separable Gaussian blur in numpy (Pillow cannot blur float images)."""
    rad = int(3 * sigma + 0.5)
    k = np.exp(-0.5 * (np.arange(-rad, rad + 1) / sigma) ** 2).astype(np.float32)
    k /= k.sum()
    for axis in (0, 1):
        p = np.pad(a, [(rad, rad) if i == axis else (0, 0) for i in (0, 1)])
        n = a.shape[axis]
        a = sum(w * np.take(p, np.arange(i, i + n), axis=axis) for i, w in enumerate(k))
    return a


def fftnoise(shape, beta):
    """Periodic fractal noise, 0..1 (filtered white noise): it wraps, so it can be laid around the galaxy without a seam."""
    F = np.fft.fft2(rng.standard_normal(shape))
    fy, fx = np.meshgrid(np.fft.fftfreq(shape[0]), np.fft.fftfreq(shape[1]), indexing='ij')
    F /= (np.hypot(fx, fy) + 1.0 / max(shape)) ** beta
    n = np.real(np.fft.ifft2(F)).astype(np.float32)
    lo, hi = np.percentile(n, [1, 99])
    return np.clip((n - lo) / (hi - lo), 0, 1)


def sample(tex, a, b):
    """Bilinear lookup of a periodic texture at fractional (row a, column b) positions."""
    R, C = tex.shape
    a0, b0 = np.floor(a).astype(int), np.floor(b).astype(int)
    fa, fb = (a - a0)[..., None][..., 0], (b - b0)
    a0, b0 = a0 % R, b0 % C
    a1, b1 = (a0 + 1) % R, (b0 + 1) % C
    top = tex[a0, b0] * (1 - fb) + tex[a0, b1] * fb
    bot = tex[a1, b0] * (1 - fb) + tex[a1, b1] * fb
    return top * (1 - fa) + bot * fa


# --- the galaxy's own coordinates: a close view, centre right of middle, major axis running down to the left
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = 0.66 * W, 0.40 * H
ang = np.deg2rad(146)
u = (xx - cx) * np.cos(ang) + (yy - cy) * np.sin(ang)
v = (-(xx - cx) * np.sin(ang) + (yy - cy) * np.cos(ang)) / 0.5      # inclination: the disc looks flattened
r = np.hypot(u, v) / (1.05 * W)
theta = np.arctan2(v, u)

warp = fbm(260, 5)
clump = fbm(120, 6, 0.6)
fine = fbm(36, 5, 0.6)
ridge = 1 - np.abs(2 * fbm(70, 5, 0.6) - 1)          # thin wisps, for the dust between the arms

def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)

# two logarithmic spiral arms: broad and soft, roughened by noise; they fade out near the centre
k = 1 / np.tan(np.deg2rad(17))
phase = 2 * (theta - k * np.log(r + 0.03)) + 2.6 * (warp - 0.5)
arms = (0.5 + 0.5 * np.cos(phase)) ** 1.6 * smooth(r, 0.03, 0.14)

disc = np.exp(-r / 0.30)
halo = np.exp(-r / 0.8)
bulge = 0.85 * np.exp(-(r / 0.075) ** 2) + 0.45 * np.exp(-r / 0.045)
core = np.exp(-(r / 0.012) ** 2)

light = disc * (0.42 + 0.95 * arms * (0.55 + 0.7 * clump)) + 0.12 * halo + 1.0 * bulge + 1.4 * core

# noise laid out in the spiral's own coordinates (across the arm, along the arm), so its streaks follow the arms
sp = theta - k * np.log(r + 0.03)                    # constant along an arm
al = np.log(r + 0.03)                                # runs along it
streak = fftnoise((512, 4096), 1.7)
st = sample(streak, (al + 4) * 160, sp / (2 * np.pi) * 4096)
lanes_ridge = 1 - np.abs(2 * st - 1)
light *= 0.86 + 0.18 * st + 0.14 * (clump - 0.5)      # the arms break into long streaks, not round blobs

# dust: dark filaments that follow the inner edge of each arm, and faint wisps between them
lane = (0.5 + 0.5 * np.cos(phase + 0.8)) ** 3
dust = lane * smooth(lanes_ridge, 0.6, 0.92) * 0.9 * smooth(clump, 0.3, 0.75) + smooth(lanes_ridge, 0.8, 0.97) * 0.3 * smooth(ridge, 0.5, 0.9)
dust *= np.exp(-r / 0.5) * smooth(r, 0.03, 0.1)
dust = blur(np.clip(dust, 0, 1), 1.6)
light *= 1 - 0.6 * dust

# knots of young stars along the arms (red in the photo; here a white blue)
knots = smooth(fbm(6, 2), 0.8, 0.95) * arms * smooth(clump, 0.55, 0.85) * smooth(r, 0.1, 0.2) * np.exp(-r / 0.6)
knots = blur(knots, 0.9)

# --- colour: near black, through the flame's pale blue, to white in the core
L = 1 - np.exp(-1.05 * light)                       # soft tone curve: the core never clips hard
bg = np.array([5, 7, 11], np.float32)
blue = np.array([88, 132, 190], np.float32)        # the faint disc
pale = np.array([159, 211, 255], np.float32)       # the flame accent
white = np.array([238, 245, 255], np.float32)
t = np.clip(L, 0, 1)[..., None]
col = bg + (blue - bg) * np.clip(t * 1.5, 0, 1)
col = col + (pale - blue) * smooth(t, 0.4, 0.75)
col = col + (white - pale) * smooth(t, 0.72, 0.95)
col = col * (0.34 + 0.56 * t)                       # keep the faint disc dark, so text on top stays easy to read
col += knots[..., None] * np.array([170, 215, 255], np.float32) * 0.7
col -= np.clip(dust, 0, 1)[..., None] * np.array([10, 13, 18], np.float32)

# --- the star field: many faint points, a few bright ones with soft halos and four short spikes
stars = np.zeros((H, W), np.float32)
n = 9000
sx, sy = rng.integers(0, W, n), rng.integers(0, H, n)
sb = rng.pareto(2.0, n).astype(np.float32) * 0.16 + 0.05
stars[sy, sx] = np.minimum(sb, 2.0)
glow = blur(stars, 0.8) * 3.4 + blur(stars, 3.0) * 2.2
spikes = np.zeros((H, W), np.float32)
for i in np.argsort(-sb)[:9]:
    x, y, b = int(sx[i]), int(sy[i]), float(sb[i])
    ln = int(6 + 9 * min(b, 1.5))
    for d in range(1, ln):
        f = b * 0.35 * (1 - d / ln) ** 2.5
        for px, py in ((x + d, y), (x - d, y), (x, y + d), (x, y - d)):
            if 0 <= px < W and 0 <= py < H:
                spikes[py, px] = max(spikes[py, px], f)
glow += blur(spikes, 0.7) * 1.2
blue_star = np.zeros((H, W), np.float32)
blue_star[sy, sx] = (rng.random(n) < 0.35)
mix = np.clip(blur(blue_star, 2.0) * 6, 0, 1)[..., None]
stc = np.array([240, 242, 255], np.float32) * (1 - mix) + np.array([170, 210, 255], np.float32) * mix
col += np.clip(glow, 0, 1.3)[..., None] * stc * 0.8

# film grain, so the gradients do not band
col += (rng.random((H, W, 1)).astype(np.float32) - 0.5) * 3.0
img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))

out = sys.argv[1] if len(sys.argv) > 1 else 'public/img/galaxy.webp'
if out.endswith('.webp'):
    img.save(out, 'WEBP', quality=80, method=6)
else:
    img.save(out)
print(out, img.size)
