"""Monster + boss atlas generator for Lexicora.

Builds ~32 roaming monsters (32x32, 2 frames) and 10 zone bosses (64x64,
2 frames) from a small set of body archetypes so every zone gets its own
escalating creature line, Pokemon-style.

Imported by scripts/generate_assets.py.
"""
from PIL import Image, ImageDraw
import math, random

MON = 32
BOSS = 64
T = (0, 0, 0, 0)


def img(w, h):
    return Image.new("RGBA", (w, h), T)


def shade(c, f):
    return (max(0, min(255, int(c[0] * f))), max(0, min(255, int(c[1] * f))),
            max(0, min(255, int(c[2] * f))), c[3] if len(c) > 3 else 255)


def outline(im, color=(22, 16, 28, 255)):
    px = im.load()
    w, h = im.size
    edges = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] > 128:
                    edges.append((x, y))
                    break
    for x, y in edges:
        px[x, y] = color
    return im


def ground_shadow(im, cx, by, w, h, a=80):
    layer = img(im.width, im.height)
    ImageDraw.Draw(layer).ellipse([cx - w // 2, by - h // 2, cx + w // 2, by + h // 2],
                                  fill=(18, 12, 26, a))
    return Image.alpha_composite(im, layer)


def eyes(d, x1, x2, y, col=(24, 22, 34, 255), gw=2, gh=3, glow=None):
    for x in (x1, x2):
        d.rectangle([x, y, x + gw - 1, y + gh - 1], fill=glow or col)
        if glow:
            d.point((x, y), fill=(255, 255, 255, 255))


# --------------------------------------------------------------- archetypes
def a_blob(d, S, col, bob, face=True, crown=None):
    """Slimes and elementals."""
    lo, hi = shade(col, .74), shade(col, 1.2)
    cy = S - 5 - bob
    d.ellipse([5, cy - 15, S - 5, cy], fill=col)
    d.ellipse([5, cy - 6, S - 5, cy + 1], fill=lo)
    d.ellipse([8, cy - 14, S - 11, cy - 7], fill=hi)
    if face:
        eyes(d, 11, 18, cy - 11)
        d.arc([13, cy - 8, 19, cy - 4], 0, 180, fill=(24, 22, 34, 255))
    if crown:
        d.polygon([(11, cy - 16), (13, cy - 21), (16, cy - 17),
                   (19, cy - 21), (21, cy - 16)], fill=crown)


def a_flame(d, S, c1, c2, bob):
    """Fire / water / spirit elemental — a licking tongue of energy."""
    cy = S - 5 - bob
    # outer flame: wavy tongue rather than a flat diamond
    d.polygon([(16, cy - 25), (20, cy - 18), (23, cy - 20), (23, cy - 9),
               (19, cy - 1), (13, cy - 1), (9, cy - 9), (9, cy - 20), (12, cy - 18)],
              fill=c1)
    # inner core
    d.polygon([(16, cy - 18), (20, cy - 10), (17, cy - 3), (13, cy - 4), (11, cy - 11)], fill=c2)
    d.ellipse([13, cy - 9, 19, cy - 3], fill=shade(c2, 1.25))
    # sparks rising off the tips
    d.point((10, cy - 23), fill=c2)
    d.point((22, cy - 22), fill=c2)
    eyes(d, 13, 18, cy - 13, col=(34, 26, 44, 255))


def a_humanoid(d, S, skin, cloth, bob, weapon=None, horns=False, hood=None,
               metal=None, big=False):
    """Goblins, orcs, knights, mages — upright two-legged fighters.

    Every part gets an explicit darker edge; without them the limbs merge
    into one silhouette once the outline pass runs.
    """
    cx = 16
    top = (2 if big else 4) - bob
    hw = 6 if big else 5            # head half-width
    tw = 7 if big else 6            # torso half-width
    skin_d, cloth_d = shade(skin, .70), shade(cloth, .68)
    cloth_h = shade(cloth, 1.18)

    head_b = top + 11               # bottom of head
    torso_b = head_b + 10           # bottom of torso
    foot = S - 3

    # ---- legs (split by a dark gap so they read as two)
    d.rectangle([cx - 5, torso_b - 1, cx - 2, foot], fill=cloth_d)
    d.rectangle([cx + 2, torso_b - 1, cx + 5, foot], fill=cloth_d)
    d.rectangle([cx - 1, torso_b, cx + 1, foot], fill=(0, 0, 0, 0))
    d.rectangle([cx - 6, foot - 1, cx - 2, foot + 1], fill=shade(cloth, .5))
    d.rectangle([cx + 2, foot - 1, cx + 6, foot + 1], fill=shade(cloth, .5))

    # ---- torso
    d.rectangle([cx - tw, head_b - 1, cx + tw, torso_b], fill=cloth)
    d.rectangle([cx - tw, head_b - 1, cx - tw + 2, torso_b], fill=cloth_d)
    d.rectangle([cx - tw + 1, head_b, cx + tw - 3, head_b + 3], fill=cloth_h)
    d.line([cx - tw, torso_b, cx + tw, torso_b], fill=cloth_d)
    d.line([cx - tw, torso_b - 4, cx + tw, torso_b - 4], fill=shade(cloth, .55))  # belt
    if metal:
        d.rectangle([cx - 3, head_b + 1, cx + 3, head_b + 6], fill=metal)
        d.line([cx, head_b + 1, cx, head_b + 6], fill=shade(metal, .7))

    # ---- arms, held slightly clear of the torso
    for sx in (-1, 1):
        ax = cx + sx * (tw + 3)
        d.rectangle([ax - 1, head_b, ax + 1, head_b + 6], fill=cloth)
        d.rectangle([ax - 1, head_b, ax - 1, head_b + 6], fill=cloth_d)
        d.rectangle([ax - 1, head_b + 6, ax + 1, head_b + 9], fill=skin)   # hand

    # ---- head
    d.ellipse([cx - hw, top, cx + hw, head_b], fill=skin)
    d.ellipse([cx - hw, top + 6, cx + hw, head_b], fill=skin_d)
    d.ellipse([cx - hw + 1, top + 1, cx + hw - 3, top + 6], fill=shade(skin, 1.14))
    d.line([cx - hw, head_b - 1, cx + hw, head_b - 1], fill=shade(skin, .55))

    if hood:
        d.polygon([(cx - hw - 2, head_b), (cx, top - 4), (cx + hw + 2, head_b)], fill=hood)
        d.polygon([(cx - hw - 2, head_b), (cx - 1, top - 4), (cx, head_b)], fill=shade(hood, .78))
        d.ellipse([cx - hw + 1, top + 3, cx + hw - 1, head_b - 1], fill=(16, 12, 24, 255))
        eyes(d, cx - 3, cx + 1, top + 6, glow=(130, 244, 208, 255))
    else:
        eyes(d, cx - 3, cx + 1, top + 4)
        d.line([cx - 2, top + 8, cx + 2, top + 8], fill=shade(skin, .5))
    if horns:
        d.polygon([(cx - hw + 1, top + 2), (cx - hw - 4, top - 5), (cx - hw + 3, top)],
                  fill=(240, 230, 206, 255))
        d.polygon([(cx + hw - 1, top + 2), (cx + hw + 4, top - 5), (cx + hw - 3, top)],
                  fill=(240, 230, 206, 255))

    # ---- weapon in the right hand
    wx = cx + tw + 3
    if weapon == "spear":
        d.line([wx, top + 2, wx, foot], fill=(132, 94, 56, 255), width=2)
        d.polygon([(wx, top - 5), (wx + 4, top + 3), (wx - 4, top + 3)], fill=(212, 216, 228, 255))
    elif weapon == "axe":
        d.line([wx, top + 6, wx, foot - 2], fill=(120, 84, 50, 255), width=2)
        d.polygon([(wx, top + 2), (wx + 8, top + 6), (wx, top + 12)], fill=(204, 208, 220, 255))
        d.polygon([(wx + 1, top + 4), (wx + 6, top + 6), (wx + 1, top + 9)], fill=(238, 242, 250, 255))
    elif weapon == "sword":
        d.line([wx, top + 1, wx, head_b + 7], fill=(220, 224, 236, 255), width=2)
        d.line([wx, top + 2, wx, head_b + 3], fill=(248, 250, 255, 255))
        d.line([wx - 2, head_b + 7, wx + 2, head_b + 7], fill=(222, 178, 64, 255))
    elif weapon == "bow":
        d.arc([wx - 2, top + 1, wx + 6, head_b + 9], 270, 90, fill=(146, 104, 60, 255), width=2)
        d.line([wx, top + 2, wx, head_b + 8], fill=(238, 232, 216, 255))
    elif weapon == "staff":
        d.line([wx, top - 1, wx, foot], fill=(112, 78, 48, 255), width=2)
        d.ellipse([wx - 4, top - 8, wx + 4, top], fill=(120, 226, 240, 255))
        d.ellipse([wx - 2, top - 6, wx + 1, top - 3], fill=(238, 252, 255, 255))
    elif weapon == "scythe":
        d.line([wx, top - 4, wx, foot], fill=(96, 70, 48, 255), width=2)
        d.arc([wx - 9, top - 10, wx + 3, top + 2], 180, 340, fill=(224, 230, 242, 255), width=3)


def a_skeleton(d, S, bob, weapon=None, crown=False, shield=False):
    bone = (232, 228, 212, 255)
    boned = (176, 170, 152, 255)
    top = 6 - bob
    cx = 16
    d.rectangle([cx - 3, top + 16, cx - 1, S - 3], fill=bone)
    d.rectangle([cx + 1, top + 16, cx + 3, S - 3], fill=bone)
    d.rectangle([cx - 4, top + 9, cx + 4, top + 16], fill=boned)
    for ry in (top + 10, top + 12, top + 14):
        d.line([cx - 4, ry, cx + 4, ry], fill=bone)
    d.line([cx, top + 9, cx, top + 16], fill=bone)
    d.rectangle([cx - 7, top + 9, cx - 5, top + 16], fill=bone)
    d.rectangle([cx + 5, top + 9, cx + 7, top + 16], fill=bone)
    d.ellipse([cx - 5, top, cx + 5, top + 9], fill=bone)
    d.rectangle([cx - 3, top + 3, cx - 1, top + 6], fill=(30, 26, 38, 255))
    d.rectangle([cx + 1, top + 3, cx + 3, top + 6], fill=(30, 26, 38, 255))
    d.line([cx - 2, top + 8, cx + 2, top + 8], fill=(120, 114, 100, 255))
    if crown:
        d.polygon([(cx - 6, top), (cx - 4, top - 5), (cx - 1, top - 1), (cx + 2, top - 5),
                   (cx + 4, top - 1), (cx + 6, top - 5), (cx + 6, top)], fill=(240, 198, 70, 255))
    if shield:
        d.polygon([(cx - 12, top + 8), (cx - 5, top + 8), (cx - 5, top + 16),
                   (cx - 8, top + 19), (cx - 12, top + 16)], fill=(168, 110, 62, 255))
        d.polygon([(cx - 11, top + 9), (cx - 6, top + 9), (cx - 6, top + 15),
                   (cx - 8, top + 17), (cx - 11, top + 15)], fill=(216, 178, 96, 255))
    if weapon == "bow":
        d.arc([cx + 5, top + 1, cx + 13, top + 17], 270, 90, fill=(140, 100, 58, 255), width=2)
        d.line([cx + 7, top + 2, cx + 7, top + 16], fill=(240, 236, 222, 255))
    elif weapon == "sword":
        d.line([cx + 8, top + 1, cx + 8, top + 13], fill=(216, 220, 232, 255), width=2)
        d.line([cx + 6, top + 13, cx + 10, top + 13], fill=(214, 170, 60, 255))


def a_beast(d, S, fur, bob, heads=1, mane=None, spikes=False, tail=True):
    """Wolves, hounds, cerberus — four-legged prowlers."""
    lo, hi = shade(fur, .74), shade(fur, 1.18)
    by = S - 4 - bob
    d.ellipse([5, by - 14, 26, by - 2], fill=fur)
    d.ellipse([5, by - 8, 26, by - 2], fill=lo)
    d.ellipse([8, by - 13, 21, by - 7], fill=hi)
    for lx in (7, 12, 18, 23):
        d.rectangle([lx, by - 5, lx + 2, by], fill=lo)
    if tail:
        d.line([5, by - 11, 1, by - 17], fill=fur, width=3)
    hx = [22] if heads == 1 else [17, 24, 21]
    hy = [by - 16] if heads == 1 else [by - 14, by - 14, by - 19]
    for i in range(heads):
        x, y = hx[i], hy[i]
        d.ellipse([x - 6, y - 5, x + 5, y + 6], fill=fur)
        d.polygon([(x - 5, y - 3), (x - 7, y - 8), (x - 1, y - 5)], fill=lo)
        d.polygon([(x + 3, y - 3), (x + 5, y - 8), (x, y - 5)], fill=lo)
        d.ellipse([x - 3, y - 1, x - 1, y + 1], fill=(250, 210, 90, 255))
        d.ellipse([x + 1, y - 1, x + 3, y + 1], fill=(250, 210, 90, 255))
        d.polygon([(x + 2, y + 2), (x + 7, y + 3), (x + 2, y + 5)], fill=lo)
    if mane:
        d.ellipse([13, by - 18, 25, by - 6], fill=mane)
    if spikes:
        for sx in range(8, 22, 4):
            d.polygon([(sx, by - 13), (sx + 2, by - 18), (sx + 4, by - 13)], fill=hi)


def a_winged(d, S, body, wing, bob, flap, beak=None, tailfan=False):
    """Bees, griffins, phoenixes, gargoyles, bats."""
    cy = S // 2 - bob
    wl = 8 + flap * 4
    d.polygon([(11, cy), (1, cy - wl), (4, cy + 6)], fill=wing)
    d.polygon([(21, cy), (31, cy - wl), (28, cy + 6)], fill=wing)
    d.ellipse([10, cy - 6, 22, cy + 9], fill=body)
    d.ellipse([12, cy - 5, 20, cy + 1], fill=shade(body, 1.18))
    d.ellipse([12, cy - 12, 21, cy - 3], fill=shade(body, 1.06))
    eyes(d, 14, 18, cy - 9)
    if beak:
        d.polygon([(15, cy - 5), (19, cy - 5), (17, cy - 1)], fill=beak)
    if tailfan:
        for i, a in enumerate((-25, 0, 25)):
            r = math.radians(90 + a)
            d.line([16, cy + 8, 16 + int(math.cos(r) * 12), cy + 8 + int(math.sin(r) * 12)],
                   fill=shade(wing, 1.1), width=3)


def a_serpent(d, S, scale, bob, hair=None, hood=False):
    """Naga, medusa — coiled tail, humanoid torso, snake head."""
    lo, hi = shade(scale, .72), shade(scale, 1.22)
    skin = (232, 206, 176, 255)
    by = S - 3 - bob
    cx = 16

    # ---- coiled tail: two stacked loops, each with its own dark underside
    d.ellipse([3, by - 9, 29, by], fill=lo)
    d.ellipse([5, by - 10, 27, by - 4], fill=scale)
    d.ellipse([8, by - 8, 20, by - 5], fill=hi)
    d.line([3, by - 4, 29, by - 4], fill=shade(scale, .55))
    d.ellipse([7, by - 16, 25, by - 8], fill=lo)
    d.ellipse([9, by - 17, 23, by - 11], fill=scale)
    d.ellipse([11, by - 16, 19, by - 13], fill=hi)

    # ---- torso
    d.rectangle([cx - 5, by - 26, cx + 5, by - 15], fill=skin)
    d.rectangle([cx - 5, by - 26, cx - 3, by - 15], fill=shade(skin, .76))
    d.rectangle([cx - 4, by - 25, cx + 2, by - 22], fill=shade(skin, 1.1))
    d.line([cx - 5, by - 16, cx + 5, by - 16], fill=shade(skin, .6))
    for sx in (-1, 1):                                   # arms
        ax = cx + sx * 7
        d.rectangle([ax - 1, by - 25, ax + 1, by - 18], fill=skin)
        d.rectangle([ax - 1, by - 25, ax - 1, by - 18], fill=shade(skin, .7))

    # ---- head
    d.ellipse([cx - 5, by - 34, cx + 5, by - 25], fill=skin)
    d.ellipse([cx - 5, by - 29, cx + 5, by - 25], fill=shade(skin, .78))
    d.ellipse([cx - 4, by - 33, cx + 1, by - 30], fill=shade(skin, 1.12))
    eyes(d, cx - 3, cx + 1, by - 31, glow=(250, 214, 96, 255))
    d.line([cx - 1, by - 27, cx + 1, by - 27], fill=(150, 96, 90, 255))

    if hood:                                             # cobra hood behind the head
        d.ellipse([cx - 10, by - 36, cx + 10, by - 24], fill=lo)
        d.ellipse([cx - 8, by - 35, cx + 8, by - 27], fill=scale)
        d.ellipse([cx - 5, by - 34, cx + 5, by - 25], fill=skin)
        d.ellipse([cx - 5, by - 29, cx + 5, by - 25], fill=shade(skin, .78))
        eyes(d, cx - 3, cx + 1, by - 31, glow=(250, 214, 96, 255))
    if hair:                                             # writhing snake locks
        for a in (-70, -42, -14, 14, 42, 70):
            r = math.radians(a - 90)
            hx, hy = cx + int(math.cos(r) * 10), by - 31 + int(math.sin(r) * 10)
            d.line([cx, by - 31, hx, hy], fill=hair, width=2)
            d.ellipse([hx - 1, hy - 1, hx + 1, hy + 1], fill=shade(hair, 1.25))


def a_golem(d, S, rock, bob, glow=None, moss=False):
    """Stone constructs — chunky slabs with clear gaps between them."""
    lo, hi = shade(rock, .72), shade(rock, 1.2)
    dk = shade(rock, .5)
    top = 3 - bob

    # ---- head slab
    d.rectangle([10, top, 22, top + 8], fill=rock)
    d.rectangle([10, top + 5, 22, top + 8], fill=lo)
    d.rectangle([11, top + 1, 18, top + 4], fill=hi)
    d.line([10, top + 8, 22, top + 8], fill=dk)
    eyes(d, 13, top + 3, 18, glow=glow or (250, 226, 130, 255)) if False else None
    for ex in (13, 18):
        d.rectangle([ex, top + 3, ex + 2, top + 5], fill=glow or (250, 226, 130, 255))

    # ---- torso slab (gap under the head keeps them distinct)
    ty = top + 10
    d.rectangle([8, ty, 24, S - 7], fill=rock)
    d.rectangle([8, ty, 11, S - 7], fill=lo)
    d.rectangle([10, ty + 1, 20, ty + 5], fill=hi)
    d.line([8, S - 7, 24, S - 7], fill=dk)

    # ---- arms held off the body
    d.rectangle([1, ty, 6, ty + 12], fill=rock)
    d.rectangle([1, ty, 2, ty + 12], fill=lo)
    d.rectangle([26, ty, 31, ty + 12], fill=rock)
    d.rectangle([29, ty, 31, ty + 12], fill=lo)
    d.rectangle([1, ty + 9, 6, ty + 12], fill=dk)
    d.rectangle([26, ty + 9, 31, ty + 12], fill=dk)

    # ---- legs
    d.rectangle([9, S - 6, 14, S - 1], fill=lo)
    d.rectangle([18, S - 6, 23, S - 1], fill=lo)

    if moss:
        for mx, my in ((9, ty + 3), (18, ty + 8), (13, ty + 12)):
            d.ellipse([mx, my, mx + 6, my + 3], fill=(96, 164, 78, 255))
            d.ellipse([mx + 1, my, mx + 4, my + 1], fill=(128, 194, 100, 255))
    if glow:
        for gx, gy, gw in ((10, ty + 6, 5), (18, ty + 9, 6), (13, ty + 13, 5)):
            d.ellipse([gx, gy, gx + gw, gy + 2], fill=glow)
            d.ellipse([gx + 1, gy, gx + gw - 2, gy + 1], fill=shade(glow, 1.3))


def a_float(d, S, col, bob, tail_wisps=True, single_eye=False, hooded=False):
    """Ghosts, beholders, reapers — hovering, no legs."""
    cy = S // 2 - 2 - bob
    lo, hi = shade(col, .78), shade(col, 1.2)
    d.ellipse([6, cy - 12, 26, cy + 8], fill=col)
    d.ellipse([9, cy - 11, 22, cy - 1], fill=hi)
    if tail_wisps:
        for i, x in enumerate((7, 12, 17, 22)):
            h = 5 + (i % 2) * 3
            d.polygon([(x, cy + 4), (x + 5, cy + 4), (x + 2, cy + 4 + h)], fill=lo)
    if single_eye:
        d.ellipse([11, cy - 8, 22, cy + 2], fill=(250, 248, 240, 255))
        d.ellipse([15, cy - 5, 19, cy + 1], fill=(40, 30, 60, 255))
        for a in range(0, 360, 60):
            r = math.radians(a)
            d.line([16, cy - 3, 16 + int(math.cos(r) * 13), cy - 3 + int(math.sin(r) * 13)],
                   fill=lo, width=2)
    elif hooded:
        d.polygon([(6, cy + 2), (16, cy - 15), (26, cy + 2)], fill=shade(col, .6))
        d.ellipse([11, cy - 8, 21, cy + 2], fill=(14, 10, 20, 255))
        eyes(d, 13, 18, cy - 4, glow=(240, 90, 80, 255))
    else:
        eyes(d, 11, 18, cy - 6)
        d.ellipse([13, cy - 1, 19, cy + 4], fill=(24, 20, 34, 255))


def a_plant(d, S, bark, leaf, bob, flowers=False):
    lo = shade(bark, .74)
    top = 4 - bob
    d.rectangle([11, top + 10, 21, S - 3], fill=bark)
    d.rectangle([11, top + 10, 14, S - 3], fill=lo)
    d.ellipse([5, top, 27, top + 16], fill=leaf)
    d.ellipse([8, top - 1, 22, top + 10], fill=shade(leaf, 1.16))
    eyes(d, 13, 18, top + 12, col=(250, 240, 190, 255))
    d.line([8, top + 14, 2, top + 9], fill=bark, width=2)
    d.line([24, top + 14, 30, top + 9], fill=bark, width=2)
    d.rectangle([11, S - 4, 15, S - 1], fill=lo)
    d.rectangle([17, S - 4, 21, S - 1], fill=lo)
    if flowers:
        for fx, fy in ((9, top + 3), (19, top + 1), (14, top + 6)):
            d.ellipse([fx, fy, fx + 3, fy + 3], fill=(244, 150, 200, 255))


def a_spider(d, S, body, bob):
    cy = S - 10 - bob
    lo, hi = shade(body, .72), shade(body, 1.2)
    for side in (-1, 1):
        for i, ly in enumerate((-4, 0, 4)):
            d.line([16, cy + ly, 16 + side * 13, cy + ly - 6 + i * 3], fill=lo, width=2)
    d.ellipse([8, cy - 6, 24, cy + 9], fill=body)
    d.ellipse([11, cy - 5, 21, cy + 1], fill=hi)
    d.ellipse([11, cy - 12, 21, cy - 3], fill=lo)
    for ex in (12, 15, 18):
        d.point((ex, cy - 9), fill=(240, 80, 80, 255))
    eyes(d, 12, 18, cy - 8, glow=(250, 90, 80, 255))


def a_mimic(d, S, bob):
    by = S - 4 - bob
    d.rectangle([5, by - 12, 27, by], fill=(150, 104, 58, 255))
    d.rectangle([5, by - 4, 27, by], fill=(112, 76, 40, 255))
    d.rectangle([5, by - 6, 27, by - 4], fill=(216, 178, 90, 255))
    d.pieslice([5, by - 26, 27, by - 8], 180, 360, fill=(168, 118, 66, 255))
    for tx in range(7, 26, 4):
        d.polygon([(tx, by - 12), (tx + 2, by - 7), (tx + 4, by - 12)], fill=(252, 250, 240, 255))
        d.polygon([(tx, by - 14), (tx + 2, by - 19), (tx + 4, by - 14)], fill=(252, 250, 240, 255))
    d.rectangle([9, by - 24, 13, by - 20], fill=(250, 230, 120, 255))
    d.rectangle([19, by - 24, 23, by - 20], fill=(250, 230, 120, 255))
    d.point((10, by - 23), fill=(30, 24, 40, 255))
    d.point((20, by - 23), fill=(30, 24, 40, 255))


# ------------------------------------------------------------------ roster
# (key, archetype, kwargs)  — order roughly matches difficulty
MONSTERS = [
    ("slime_green",   a_blob,     dict(col=(112, 196, 108, 255))),
    ("slime_blue",    a_blob,     dict(col=(96, 174, 232, 255))),
    ("bee",           a_winged,   dict(body=(246, 202, 70, 255), wing=(226, 240, 250, 255), beak=None)),
    ("wolf",          a_beast,    dict(fur=(158, 162, 172, 255))),
    ("goblin",        a_humanoid, dict(skin=(126, 190, 96, 255), cloth=(150, 96, 62, 255), weapon="spear")),
    ("treant",        a_plant,    dict(bark=(140, 102, 62, 255), leaf=(88, 158, 74, 255))),
    ("spider",        a_spider,   dict(body=(122, 84, 148, 255))),
    ("orc",           a_humanoid, dict(skin=(104, 156, 84, 255), cloth=(128, 74, 52, 255), weapon="axe",
                                       horns=True, big=True)),
    ("skeleton_bow",  a_skeleton, dict(weapon="bow")),
    ("skeleton_sword", a_skeleton, dict(weapon="sword", shield=True)),
    ("sand_imp",      a_humanoid, dict(skin=(214, 164, 96, 255), cloth=(178, 132, 70, 255), horns=True)),
    ("scorpion",      a_spider,   dict(body=(206, 148, 72, 255))),
    ("mummy",         a_humanoid, dict(skin=(226, 216, 186, 255), cloth=(206, 194, 162, 255))),
    ("rock_golem",    a_golem,    dict(rock=(150, 136, 118, 255))),
    ("cave_bat",      a_winged,   dict(body=(122, 96, 146, 255), wing=(92, 72, 116, 255))),
    ("mimic",         a_mimic,    dict()),
    ("ice_slime",     a_blob,     dict(col=(158, 218, 240, 255))),
    ("frost_wolf",    a_beast,    dict(fur=(196, 224, 240, 255), mane=(226, 244, 252, 255))),
    ("yeti",          a_humanoid, dict(skin=(230, 242, 250, 255), cloth=(198, 220, 236, 255), big=True)),
    ("fire_spirit",   a_flame,    dict(c1=(240, 116, 40, 255), c2=(254, 212, 110, 255))),
    ("magma_hound",   a_beast,    dict(fur=(96, 60, 56, 255), mane=(240, 132, 48, 255), spikes=True)),
    ("lava_golem",    a_golem,    dict(rock=(94, 72, 70, 255), glow=(246, 138, 48, 255))),
    ("ghost",         a_float,    dict(col=(214, 226, 246, 255))),
    ("gargoyle",      a_winged,   dict(body=(132, 136, 148, 255), wing=(104, 108, 122, 255))),
    ("dark_mage",     a_humanoid, dict(skin=(198, 172, 148, 255), cloth=(74, 58, 120, 255),
                                       weapon="staff", hood=(58, 44, 96, 255))),
    ("beholder",      a_float,    dict(col=(148, 108, 196, 255), single_eye=True)),
    ("pixie_flower",  a_plant,    dict(bark=(126, 96, 158, 255), leaf=(126, 206, 176, 255), flowers=True)),
    ("thunder_fox",   a_beast,    dict(fur=(248, 206, 92, 255), mane=(255, 246, 190, 255), spikes=True)),
    ("naga",          a_serpent,  dict(scale=(96, 190, 148, 255), hood=True)),
    ("medusa",        a_serpent,  dict(scale=(150, 200, 120, 255), hair=(88, 168, 96, 255))),
    ("imp_red",       a_humanoid, dict(skin=(212, 84, 72, 255), cloth=(120, 44, 44, 255), horns=True)),
    ("dark_knight",   a_humanoid, dict(skin=(96, 100, 118, 255), cloth=(60, 62, 84, 255),
                                       weapon="sword", metal=(178, 182, 198, 255), big=True)),
]

BOSSES = [
    ("king_slime",     a_blob,     dict(col=(96, 200, 126, 255), crown=(244, 206, 84, 255))),
    ("elder_treant",   a_plant,    dict(bark=(122, 88, 54, 255), leaf=(76, 148, 70, 255))),
    ("orc_warlord",    a_humanoid, dict(skin=(92, 148, 78, 255), cloth=(146, 72, 48, 255),
                                        weapon="axe", horns=True, big=True, metal=(196, 160, 70, 255))),
    ("sand_pharaoh",   a_humanoid, dict(skin=(226, 186, 118, 255), cloth=(230, 210, 160, 255),
                                        weapon="staff", metal=(240, 200, 80, 255), big=True)),
    ("cave_golem",     a_golem,    dict(rock=(138, 128, 116, 255), moss=True)),
    ("frost_wyrm",     a_winged,   dict(body=(176, 216, 240, 255), wing=(214, 238, 250, 255),
                                        beak=(232, 244, 252, 255), tailfan=True)),
    ("magma_titan",    a_golem,    dict(rock=(86, 62, 60, 255), glow=(250, 146, 48, 255))),
    ("ruin_sentinel",  a_skeleton, dict(weapon="sword", shield=True, crown=True)),
    ("forest_medusa",  a_serpent,  dict(scale=(126, 200, 132, 255), hair=(70, 156, 92, 255))),
    ("dark_sovereign", a_float,    dict(col=(96, 66, 150, 255), hooded=True)),
]


def build(out_dir):
    # ---- roaming monsters: 2 frames each
    sheet = img(MON * 2, MON * len(MONSTERS))
    for i, (name, fn, kw) in enumerate(MONSTERS):
        for f in range(2):
            c = img(MON, MON)
            d = ImageDraw.Draw(c)
            kwargs = dict(kw)
            kwargs["bob"] = f
            if fn is a_winged:
                kwargs["flap"] = f
            fn(d, MON, **kwargs)
            c = ground_shadow(c, 16, MON - 2, 20, 6)
            c = outline(c)
            sheet.paste(c, (f * MON, i * MON), c)
    sheet.save(f"{out_dir}/monsters.png")
    print("monsters.png", sheet.size, len(MONSTERS), "species")

    # ---- bosses: same archetypes rendered at 2x into a 64px cell
    bsheet = img(BOSS * 2, BOSS * len(BOSSES))
    for i, (name, fn, kw) in enumerate(BOSSES):
        for f in range(2):
            small = img(MON, MON)
            d = ImageDraw.Draw(small)
            kwargs = dict(kw)
            kwargs["bob"] = f
            if fn is a_winged:
                kwargs["flap"] = f
            fn(d, MON, **kwargs)
            big = small.resize((BOSS, BOSS), Image.NEAREST)
            big = ground_shadow(big, 32, BOSS - 3, 42, 10, 95)
            big = outline(big)
            bsheet.paste(big, (f * BOSS, i * BOSS), big)
    bsheet.save(f"{out_dir}/bosses.png")
    print("bosses.png", bsheet.size, len(BOSSES), "bosses")

    return [m[0] for m in MONSTERS], [b[0] for b in BOSSES]
