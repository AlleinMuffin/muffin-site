#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procedural pixel-art scene generator for the MUFIFN site.

Produces theme-consistent placeholder "screenshots" (SVG) so the site looks
finished before real Minecraft screenshots are dropped in. Everything is
deterministic (seeded) -> re-running gives identical files.

Usage:  python tools/gen-art.py
Output: assets/img/hero.svg, assets/img/gallery-01..06.svg
"""

import math
import os
import random

# ---------------------------------------------------------------------------
# pixel grid every scene is drawn on (scaled up in the SVG viewBox)
# ---------------------------------------------------------------------------
W, H = 160, 90
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "img")


# ---------------------------------------------------------------------------
# tiny colour helpers
# ---------------------------------------------------------------------------
def clamp(v, lo=0, hi=255):
    return int(max(lo, min(hi, v)))


def hx(c):
    return "#%02X%02X%02X" % (clamp(c[0]), clamp(c[1]), clamp(c[2]))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def shade(c, k):
    """k<1 darker, k>1 lighter"""
    return (clamp(c[0] * k), clamp(c[1] * k), clamp(c[2] * k))


Grid = list  # grid[y][x] = (r,g,b)


def new_grid(base):
    return [[tuple(base) for _ in range(W)] for _ in range(H)]


def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = tuple(c)


def rect(g, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            g[y][x] = tuple(c)


def row(g, y, c):
    rect(g, 0, y, W, y + 1, c)


def disc(g, cx, cy, r, c):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                put(g, x, y, c)


def ridge_fn(rng, base, amps, freqs):
    """Smooth silhouette generator (sum of sines with random phases)."""
    phases = [rng.uniform(0, math.tau) for _ in amps]
    amps = list(amps)
    freqs = list(freqs)

    def f(x):
        v = base
        for a, fr, ph in zip(amps, freqs, phases):
            v += a * math.sin(x * fr + ph)
        return v

    return f


def stars(g, rng, count, top, bottom, bright=(214, 226, 245)):
    for _ in range(count):
        x = rng.randrange(0, W)
        y = rng.randrange(top, bottom)
        k = rng.random()
        if k > 0.93:
            put(g, x, y, bright)
            put(g, x + 1, y, mix(bright, (10, 13, 20), 0.55))
            put(g, x, y + 1, mix(bright, (10, 13, 20), 0.55))
        elif k > 0.72:
            put(g, x, y, mix(bright, (12, 16, 26), 0.35))
        else:
            put(g, x, y, mix(bright, (12, 16, 26), 0.62))


def moon(g, mx, my, mr, halo=6, halo_k=0.16):
    """Moon with a soft halo (large-to-small so discs layer correctly)."""
    base = g[my][mx]
    for i in range(halo, 0, -1):
        disc(g, mx, my, mr + i * 1.7, mix(base, C_MOON, (halo - i + 1) / float(halo) * halo_k))
    disc(g, mx, my, mr, C_MOON)
    disc(g, mx - 2, my - 1, 1.3, mix(C_MOON, (150, 160, 180), 0.45))
    disc(g, mx + 1, my + 2, 0.9, mix(C_MOON, (150, 160, 180), 0.6))


def sky_gradient(g, top_c, bot_c, horizon, gamma=1.35, band=2):
    for y in range(horizon):
        t = ((y / max(1, horizon - 1)) ** gamma)
        banded = (y // band) * band
        t = ((banded / max(1, horizon - 1)) ** gamma)
        c = mix(top_c, bot_c, t)
        row(g, y, c)


def reflect(g, ground_y, rng, jitter=1, break_p=0.45):
    """Cheap vertical water reflection of whatever sits above ground_y."""
    depth = H - ground_y
    for x in range(W):
        src = None
        for y in range(ground_y - 1, ground_y - 26, -1):
            c = g[y][x]
            if sum(c) > 90:  # something bright enough to reflect
                src = c
                break
        if src is None:
            continue
        col = mix(src, (8, 11, 18), 0.62)
        for d in range(depth):
            if rng.random() < break_p:
                continue
            xx = x + rng.randint(-jitter, jitter)
            fade = 1.0 - d / max(1, depth)
            put(g, xx, ground_y + d, mix((8, 11, 18), col, fade * 0.9))


# ---------------------------------------------------------------------------
# palette (kept close to the site tokens: dark slate + mint accent)
# ---------------------------------------------------------------------------
C_MINT = (110, 231, 183)
C_MINT_DIM = (62, 132, 108)
C_WARM = (245, 199, 119)
C_WARM_DIM = (128, 96, 52)
C_MOON = (232, 238, 247)


# ---------------------------------------------------------------------------
# scene 1 - night city skyline
# ---------------------------------------------------------------------------
def scene_city(seed=7):
    rng = random.Random(seed)
    g = new_grid((9, 12, 22))
    horizon = 68

    sky_gradient(g, (7, 9, 18), (30, 45, 74), horizon)
    stars(g, rng, 150, 0, horizon - 14)

    # moon + halo
    mx, my, mr = rng.choice([118, 126, 134]), 17, 5
    moon(g, mx, my, mr, halo=6, halo_k=0.14)

    # thin cloud bands
    for _ in range(5):
        cy = rng.randrange(24, horizon - 12)
        cx = rng.randrange(0, W)
        ln = rng.randrange(10, 34)
        col = mix(g[cy][cx], (120, 140, 180), 0.22)
        for i in range(ln):
            yy = cy + int(math.sin(i * 0.4) * 0.6)
            put(g, (cx + i) % W, yy, col)

    # distant hills
    f = ridge_fn(rng, 54, [5, 2.6, 1.2], [0.035, 0.09, 0.23])
    for x in range(W):
        top = int(f(x))
        put(g, x, top, mix(g[top][x], (110, 130, 170), 0.22))
        rect(g, x, top + 1, x + 1, horizon, (16, 21, 34))

    # skyline
    facades = [(26, 30, 40), (21, 25, 34), (31, 36, 46), (18, 22, 30)]
    x = 0
    towers = []
    while x < W:
        bw = rng.choice([5, 6, 8, 9, 11, 13])
        tall = rng.random() < 0.22
        bh = rng.randrange(38, 58) if tall else rng.randrange(12, 34)
        bh = min(bh, horizon - 6)
        top = horizon - bh
        base = facades[rng.randrange(len(facades))]
        base = shade(base, rng.uniform(0.85, 1.15))
        rect(g, x, top, x + bw, horizon, base)
        # right edge shadow + lit top edge
        rect(g, x + bw - 1, top, x + bw, horizon, shade(base, 0.6))
        row_put(g, x, x + bw, top, shade(base, 1.5))
        if tall:
            towers.append((x + bw // 2, top, base))

        # windows
        for wx in range(x + 1, x + bw - 1, 3):
            for wy in range(top + 2, horizon - 1, 4):
                lit = rng.random()
                if lit > 0.62:
                    col = C_MINT if rng.random() < 0.09 else C_WARM
                    col = mix(col, (0, 0, 0), rng.uniform(0.0, 0.22))
                    rect(g, wx, wy, wx + 2, wy + 2, col)
                elif lit > 0.5:
                    rect(g, wx, wy, wx + 2, wy + 2, (12, 15, 21))

        x += bw

    # antennas with blinking beacons
    for (cx, top, base) in towers:
        ah = rng.randrange(4, 10)
        for i in range(ah):
            put(g, cx, top - 1 - i, shade(base, 0.8))
        put(g, cx, top - 1 - ah, (255, 92, 92))
        put(g, cx + 1, top - 1 - ah, mix(g[top - 1 - ah][cx + 1], (255, 92, 92), 0.35))

    # water front
    rect(g, 0, horizon, W, H, (9, 12, 20))
    reflect(g, horizon, rng)
    return g


def row_put(g, x0, x1, y, c):
    for x in range(max(0, x0), min(W, x1)):
        put(g, x, y, c)


# ---------------------------------------------------------------------------
# scene 2 - mountain range at dawn
# ---------------------------------------------------------------------------
def scene_mountains(seed=11):
    rng = random.Random(seed)
    g = new_grid((8, 10, 18))
    horizon = 60

    sky_gradient(g, (8, 11, 21), (44, 58, 88), horizon, gamma=1.5)
    stars(g, rng, 90, 0, horizon - 22)
    # faint cold glow on the horizon
    for y in range(horizon - 16, horizon):
        t = (y - (horizon - 16)) / 16.0
        row(g, y, mix(g[y][0], (72, 96, 130), t * 0.45))

    layers = [
        (46, [9, 4, 2], [0.02, 0.055, 0.14], (38, 48, 72), (96, 112, 146)),
        (52, [7, 3.5, 1.6], [0.028, 0.08, 0.2], (27, 35, 54), (70, 84, 116)),
        (60, [6, 3, 1.2], [0.04, 0.11, 0.27], (17, 22, 35), (46, 57, 82)),
    ]
    for i, (base, amps, freqs, body, cap) in enumerate(layers):
        f = ridge_fn(rng, base, amps, freqs)
        for x in range(W):
            top = int(f(x))
            rect(g, x, top, x + 1, H, body)
            # snow / rim light on the crest
            if rng.random() < 0.65:
                put(g, x, top, mix(body, cap, rng.uniform(0.4, 0.85)))
                if rng.random() < 0.4:
                    put(g, x, top + 1, mix(body, cap, 0.3))

    # foreground trees
    ground = ridge_fn(rng, 78, [3, 1.5], [0.06, 0.19])
    for x in range(W):
        top = int(ground(x))
        rect(g, x, top, x + 1, H, (9, 12, 18))
    for tx in range(2, W, rng.randrange(4, 7)):
        ty = int(ground(tx)) - 1
        th = rng.randrange(5, 11)
        for i in range(th):
            halfw = max(0, int((th - i) * 0.45))
            row_put(g, tx - halfw, tx + halfw + 1, ty - i, (10, 13, 20))
        put(g, tx, ty + 1, (10, 13, 20))
    return g


# ---------------------------------------------------------------------------
# scene 3 - cavern with mint crystals
# ---------------------------------------------------------------------------
def scene_cave(seed=23):
    rng = random.Random(seed)
    AIR = (7, 9, 13)
    ROCK = (21, 24, 31)
    ROCK_HI = (34, 39, 49)
    ROCK_LO = (15, 17, 23)
    g = new_grid(AIR)

    # ceiling + floor profiles (rocky, irregular)
    ceil = ridge_fn(rng, 14, [8, 4, 2], [0.05, 0.13, 0.31])
    floor = ridge_fn(rng, 72, [7, 3.5, 1.6], [0.045, 0.12, 0.29])
    ctop = [int(ceil(x)) for x in range(W)]
    ftop = [int(floor(x)) for x in range(W)]

    # rock bodies with sparse speckle texture
    for x in range(W):
        for y in range(0, ctop[x]):
            g[y][x] = ROCK
        for y in range(ftop[x], H):
            g[y][x] = ROCK
        # hi/lo speckles (sparse, keeps SVG small)
        for _ in range(3):
            y = rng.randrange(0, ctop[x])
            put(g, x, y, ROCK_LO if rng.random() < 0.55 else ROCK_HI)
        for _ in range(3):
            y = rng.randrange(ftop[x], H)
            put(g, x, y, ROCK_LO if rng.random() < 0.55 else ROCK_HI)
        # edge highlights facing the cave
        put(g, x, ctop[x], ROCK_HI)
        put(g, x, ftop[x], ROCK_HI)

    # stalactites / stalagmites (dark silhouettes against the air)
    for x in range(3, W, 6):
        top = ctop[x]
        ln = rng.randrange(5, 16)
        for i in range(ln):
            wdt = max(0, int((ln - i) * 0.32))
            row_put(g, x - wdt, x + wdt + 1, top + i, ROCK_LO)
        put(g, x, top + ln, ROCK_HI)
    for x in range(6, W, 8):
        base = ftop[x]
        ln = rng.randrange(4, 12)
        for i in range(ln):
            wdt = max(0, int((ln - i) * 0.32))
            row_put(g, x - wdt, x + wdt + 1, base - i, ROCK_LO)
        put(g, x, base - ln, ROCK_HI)

    # crystal clusters on the floor + hanging from the ceiling
    clusters = []
    for _ in range(3):
        cx = rng.randrange(10, W - 10)
        clusters.append((cx, ftop[cx], 1, rng.randrange(9, 16)))
    for _ in range(2):
        cx = rng.randrange(14, W - 14)
        clusters.append((cx, ctop[cx] + 3, -1, rng.randrange(7, 12)))

    glow_pts = []
    for (cx, base, sgn, size) in clusters:
        glow_pts.append((cx, base + sgn * size // 2, size))
        for i in range(size):
            halfw = max(0, int((size - i) * 0.38))
            t = i / float(size)
            col = mix(mix(C_MINT, C_MINT_DIM, t * 0.7), (255, 255, 255), 0.12 if i > size * 0.6 else 0.0)
            yy = base + sgn * (size - i)
            row_put(g, cx - halfw, cx + halfw + 1, yy, col)
        put(g, cx, base + sgn * size, (235, 255, 246))

    # soft mint ambience around each cluster (radial falloff on the air)
    for (gx_, gy_, size) in glow_pts:
        r = size * 2.4
        for y in range(int(gy_ - r), int(gy_ + r) + 1):
            for x in range(int(gx_ - r), int(gx_ + r) + 1):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                d = math.hypot(x - gx_, y - gy_) / r
                if d < 1.0 and g[y][x] in (AIR, ROCK_LO, ROCK):
                    k = (1 - d) ** 2 * 0.5
                    put(g, x, y, mix(g[y][x], C_MINT, k))

    # floating dust motes
    for _ in range(45):
        x = rng.randrange(0, W)
        y = rng.randrange(16, H - 12)
        if g[y][x] == AIR:
            put(g, x, y, mix(AIR, C_MINT, rng.uniform(0.2, 0.5)))
    return g


# ---------------------------------------------------------------------------
# scene 4 - keep / fortress over water
# ---------------------------------------------------------------------------
def scene_fortress(seed=31):
    rng = random.Random(seed)
    g = new_grid((8, 10, 17))
    horizon = 72

    sky_gradient(g, (7, 9, 16), (26, 34, 54), horizon, gamma=1.4)
    stars(g, rng, 120, 0, horizon - 20)
    moon(g, 30, 20, 4, halo=5, halo_k=0.14)

    stone = (30, 33, 42)
    dark = (20, 22, 29)
    # main keep body
    kx0, kx1, ktop = 48, 112, 40
    rect(g, kx0, ktop, kx1, horizon, stone)
    rect(g, kx0, ktop, kx1, ktop + 1, shade(stone, 1.5))
    rect(g, kx1 - 2, ktop, kx1, horizon, dark)
    # crenellations
    for x in range(kx0, kx1, 4):
        rect(g, x, ktop - 3, x + 2, ktop, stone)
    # towers
    for cx in (kx0 - 4, kx1 - 1):
        rect(g, cx - 3, ktop - 14, cx + 3, horizon, shade(stone, 0.92))
        rect(g, cx - 4, ktop - 18, cx + 4, ktop - 14, shade(stone, 1.1))
        for x in range(cx - 4, cx + 4, 3):
            rect(g, x, ktop - 21, x + 2, ktop - 18, shade(stone, 1.1))
    # windows + gate
    for wy in range(ktop + 5, horizon - 6, 9):
        for wx in range(kx0 + 4, kx1 - 5, 11):
            rect(g, wx, wy, wx + 3, wy + 4, mix(dark, (0, 0, 0), 0.3))
            if rng.random() < 0.6:
                col = C_MINT if rng.random() < 0.12 else C_WARM
                rect(g, wx + 1, wy + 1, wx + 3, wy + 4, mix(col, (0, 0, 0), 0.15))
    gate_w, gate_h = 12, 16
    gx = (kx0 + kx1) // 2 - gate_w // 2
    rect(g, gx, horizon - gate_h, gx + gate_w, horizon, (12, 13, 16))
    rect(g, gx, horizon - gate_h, gx + gate_w, horizon - gate_h + 1, shade(stone, 1.3))
    rect(g, gx + 3, horizon - gate_h + 3, gx + gate_w - 3, horizon, mix((20, 16, 13), C_WARM, 0.06))

    # torch posts
    for tx in (kx0 - 10, kx1 + 8):
        rect(g, tx, horizon - 12, tx + 2, horizon, (26, 29, 37))
        rect(g, tx - 1, horizon - 14, tx + 3, horizon - 12, (34, 38, 48))
        put(g, tx, horizon - 15, C_WARM)
        put(g, tx + 1, horizon - 15, mix(C_WARM, (255, 255, 255), 0.3))

    # water
    rect(g, 0, horizon, W, H, (9, 11, 19))
    reflect(g, horizon, rng, jitter=1)
    return g


# ---------------------------------------------------------------------------
# scene 5 - beacon hall (vertical light shaft)
# ---------------------------------------------------------------------------
def scene_beacon(seed=41):
    rng = random.Random(seed)
    g = new_grid((11, 13, 18))
    floor_y = 74

    # back wall bricks
    for y in range(0, floor_y, 6):
        offset = 0 if (y // 6) % 2 == 0 else 6
        rect(g, 0, y, W, y + 1, (17, 20, 27))
        for x in range(-offset, W, 12):
            rect(g, x, y, x + 1, y + 6, (17, 20, 27))
    for y in range(0, floor_y):
        for x in range(0, W, 3):
            if rng.random() < 0.25:
                put(g, x, y, mix(g[y][x], (50, 56, 70), 0.35))

    # floor slabs
    for y in range(floor_y, H, 5):
        rect(g, 0, y, W, y + 1, (14, 16, 22))
    rect(g, 0, floor_y, W, floor_y + 1, (30, 34, 44))
    for x in range(0, W, 16):
        rect(g, x, floor_y, x + 1, H, (14, 16, 22))

    # pillars
    for px0 in (10, 32, 118, 140):
        rect(g, px0, 16, px0 + 8, floor_y, (26, 30, 39))
        rect(g, px0, 16, px0 + 2, floor_y, (32, 37, 47))
        rect(g, px0 + 6, 16, px0 + 8, floor_y, (16, 19, 25))
        rect(g, px0 - 1, 12, px0 + 9, 16, (32, 37, 47))

    # altar + beacon block
    cx = W // 2
    rect(g, cx - 12, floor_y - 6, cx + 12, floor_y, (28, 32, 41))
    rect(g, cx - 12, floor_y - 6, cx + 12, floor_y - 5, (40, 46, 58))
    rect(g, cx - 4, floor_y - 12, cx + 4, floor_y - 6, mix(C_MINT_DIM, C_MINT, 0.5))
    rect(g, cx - 4, floor_y - 12, cx + 4, floor_y - 11, mix(C_MINT, (255, 255, 255), 0.35))

    # light shaft
    for y in range(0, floor_y - 10):
        halfw = int(3 + (y / max(1, floor_y)) * 5)
        t = y / float(floor_y)
        for x in range(cx - halfw, cx + halfw + 1):
            d = abs(x - cx) / max(1, halfw)
            k = (1 - d) * (0.35 + t * 0.4)
            put(g, x, y, mix(g[y][x], C_MINT, max(0.0, min(0.55, k))))

    # glow ring on the floor + motes
    for x in range(cx - 26, cx + 26):
        d = abs(x - cx) / 26.0
        if rng.random() < (1 - d):
            put(g, x, floor_y + 1, mix(g[floor_y + 1][x], C_MINT, (1 - d) * 0.4))
            put(g, x, floor_y + 2, mix(g[floor_y + 2][x], C_MINT, (1 - d) * 0.2))
    for _ in range(70):
        x = rng.randrange(cx - 18, cx + 18)
        y = rng.randrange(6, floor_y - 6)
        if abs(x - cx) < 7:
            put(g, x, y, mix(g[y][x], C_MINT, rng.uniform(0.2, 0.6)))
    return g


# ---------------------------------------------------------------------------
# scene 6 - terraced fields at dusk
# ---------------------------------------------------------------------------
def scene_fields(seed=53):
    rng = random.Random(seed)
    g = new_grid((10, 12, 20))
    horizon = 44

    sky_gradient(g, (10, 13, 24), (54, 62, 86), horizon, gamma=1.6)
    stars(g, rng, 70, 0, horizon - 16)
    # warm dusk glow just above the horizon
    for y in range(horizon - 12, horizon):
        t = (y - (horizon - 12)) / 12.0
        row(g, y, mix(g[y][0], (104, 88, 70), t * 0.4))

    # far hills
    f = ridge_fn(rng, 40, [5, 2.5, 1.2], [0.03, 0.08, 0.2])
    for x in range(W):
        top = int(f(x))
        rect(g, x, top, x + 1, horizon, (24, 28, 40))
        put(g, x, top, mix((24, 28, 40), (86, 96, 122), 0.35))

    # windmill silhouette
    wx0, wy0 = 122, 30
    rect(g, wx0, wy0, wx0 + 7, horizon - 2, (18, 21, 29))
    for i, (dx, dy) in enumerate([(1, -1), (1, 1), (-1, 1), (-1, -1)]):
        for k in range(7):
            put(g, wx0 + 3 + dx * k, wy0 - 2 + dy * k, (24, 28, 37))
            if k > 2:
                put(g, wx0 + 3 + dx * k + (1 if dy < 0 else 0), wy0 - 2 + dy * k, (24, 28, 37))

    # terraces
    soil = (34, 30, 26)
    cropa = (58, 74, 52)
    cropb = (74, 92, 62)
    y = horizon
    while y < H:
        band_h = rng.randrange(4, 8)
        rect(g, 0, y, W, min(H, y + band_h), soil)
        rect(g, 0, y, W, y + 1, shade(soil, 1.45))
        for x in range(0, W, 3):
            c = mix(cropa, cropb, rng.random())
            put(g, x, y + 1, c)
            if rng.random() < 0.5:
                put(g, x, y + 2, mix(c, (0, 0, 0), 0.3))
        y += band_h + 1

    # path + lanterns
    px = 30
    for y in range(horizon, H):
        wdt = int(2 + (y - horizon) * 0.09)
        row_put(g, px - wdt, px + wdt, y, mix((40, 36, 32), (70, 64, 56), rng.random() * 0.4))
    for ly in (horizon + 6, horizon + 22, horizon + 38):
        lw = int(2 + (ly - horizon) * 0.09)
        rect(g, px - lw - 1, ly - 7, px - lw, ly, (22, 24, 30))
        put(g, px - lw - 1, ly - 8, C_WARM)
        rect(g, px + lw, ly - 7, px + lw + 1, ly, (22, 24, 30))
        put(g, px + lw, ly - 8, C_WARM)
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if rng.random() < 0.35 and abs(dx) + abs(dy) < 5:
                    put(g, px - lw - 1 + dx, ly - 8 + dy, mix(g[ly - 8 + dy][px - lw - 1 + dx], C_WARM, 0.3))
                    put(g, px + lw + dx, ly - 8 + dy, mix(g[ly - 8 + dy][px + lw + dx], C_WARM, 0.3))
    return g


# ---------------------------------------------------------------------------
# SVG output (greedy rectangle merge keeps the files small)
# ---------------------------------------------------------------------------
def to_rects(g):
    used = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        for x in range(W):
            if used[y][x]:
                continue
            c = g[y][x]
            w = 1
            while x + w < W and not used[y][x + w] and g[y][x + w] == c:
                w += 1
            h = 1
            while y + h < H and all(
                (not used[y + h][x + i]) and g[y + h][x + i] == c for i in range(w)
            ):
                h += 1
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    used[yy][xx] = True
            out.append((x, y, w, h, c))
    return out


def write_svg(g, path, scale, title):
    rects = to_rects(g)
    cache = {}
    body = []
    for (x, y, w, h, c) in rects:
        col = cache.get(c)
        if col is None:
            col = hx(c)
            cache[c] = col
        body.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (x, y, w, h, col))
    vw, vh = W * scale, H * scale
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">'
        % (vw, vh, vw, vh, title),
        '<title>%s</title>' % title,
        '<g shape-rendering="crispEdges" transform="scale(%d)">' % scale,
        "".join(body),
        "</g>",
        "</svg>",
    ]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(svg))
    return len(rects), os.path.getsize(path)


def main():
    scenes = [
        ("hero.svg", scene_city(seed=7), 12, "Mufifn server - city at night"),
        ("gallery-01.svg", scene_city(seed=19), 8, "Skyline from the harbour"),
        ("gallery-02.svg", scene_mountains(seed=11), 8, "Mountain range at dawn"),
        ("gallery-03.svg", scene_cave(seed=23), 8, "Deep cave crystals"),
        ("gallery-04.svg", scene_fortress(seed=31), 8, "Fortress over the water"),
        ("gallery-05.svg", scene_beacon(seed=41), 8, "Beacon hall"),
        ("gallery-06.svg", scene_fields(seed=53), 8, "Terraced fields at dusk"),
    ]
    total = 0
    for name, grid, scale, title in scenes:
        path = os.path.join(OUT_DIR, name)
        n, size = write_svg(grid, path, scale, title)
        total += size
        print("%-16s rects=%-6d %6.1f KB" % (name, n, size / 1024.0))
    print("total %.1f KB" % (total / 1024.0))


if __name__ == "__main__":
    main()
