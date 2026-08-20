"""Asset generator for Lexicora — open-world English adventure.

Produces small native-resolution pixel-art atlases that the canvas engine
scales up with imageSmoothingEnabled=false. Everything is procedurally
drawn so the art can be regenerated/tweaked without external asset packs.

Run:  python3 scripts/generate_assets.py
"""
from PIL import Image, ImageDraw
import random, os, math

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(OUT, exist_ok=True)

random.seed(7)

TILE = 32
T = (0, 0, 0, 0)


# ----------------------------------------------------------------- helpers
def img(w, h):
    return Image.new("RGBA", (w, h), T)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


def vgrad(d, x, y, w, h, top, bot):
    for i in range(h):
        t = i / (h - 1) if h > 1 else 0
        d.rectangle([x, y + i, x + w - 1, y + i], fill=lerp(top, bot, t))


def speckle(im, x, y, w, h, colors, density=0.10, rnd=None):
    rnd = rnd or random
    px = im.load()
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if xx < 0 or yy < 0 or xx >= im.width or yy >= im.height:
                continue
            if px[xx, yy][3] == 0:
                continue
            if rnd.random() < density:
                px[xx, yy] = rnd.choice(colors)


def shadow(im, cx, by, w, h, alpha=90):
    """Soft ground shadow ellipse, alpha-composited."""
    layer = img(im.width, im.height)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - w // 2, by - h // 2, cx + w // 2, by + h // 2], fill=(20, 14, 30, alpha))
    return Image.alpha_composite(im, layer)


def outline(im, color=(24, 18, 32, 255)):
    """Add a 1px dark outline around opaque pixels."""
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


# ----------------------------------------------------------------- palette
GRASS = ((104, 168, 78, 255), (70, 126, 58, 255))
GRASS_HI = [(126, 192, 92, 255), (88, 148, 66, 255), (146, 206, 104, 255)]
FOREST = ((72, 120, 62, 255), (48, 88, 46, 255))
FOREST_HI = [(92, 142, 74, 255), (58, 102, 52, 255)]
SAND = ((226, 200, 138, 255), (198, 168, 108, 255))
SAND_HI = [(240, 218, 160, 255), (208, 178, 118, 255)]
SNOW = ((238, 244, 252, 255), (200, 214, 236, 255))
SNOW_HI = [(255, 255, 255, 255), (214, 228, 246, 255)]
STONE = ((146, 142, 150, 255), (108, 104, 116, 255))
STONE_HI = [(168, 164, 172, 255), (92, 88, 100, 255)]
ASH = ((92, 74, 78, 255), (62, 48, 54, 255))
ASH_HI = [(120, 92, 88, 255), (48, 36, 42, 255), (168, 82, 48, 255)]
VOID = ((62, 48, 106, 255), (36, 26, 68, 255))
VOID_HI = [(96, 76, 152, 255), (188, 168, 255, 255), (28, 20, 54, 255)]
DIRT = ((168, 130, 88, 255), (136, 102, 66, 255))
DIRT_HI = [(188, 150, 106, 255), (120, 90, 58, 255)]
PSTONE = ((176, 172, 178, 255), (140, 136, 146, 255))
WATER = ((72, 148, 208, 255), (44, 104, 168, 255))
ICE = ((176, 220, 240, 255), (132, 184, 216, 255))
LAVA = ((252, 168, 48, 255), (208, 68, 24, 255))

GOLD = (232, 184, 75, 255)
GOLD_D = (168, 122, 36, 255)


# ================================================================ TERRAIN
TERRAIN_ROWS = [
    "grass", "forest", "sand", "snow", "stone", "ash",
    "void", "dirt", "pstone", "water", "ice", "lava",
]
TVARIANTS = 4


def make_terrain():
    sheet = img(TILE * TVARIANTS, TILE * len(TERRAIN_ROWS))

    def cell(row, col, base, hi, density=0.12, seed=0):
        """Flat mid-tone + noise. A per-tile vertical gradient would repeat every
        32px and read as horizontal banding once the tiles are laid out."""
        c = img(TILE, TILE)
        d = ImageDraw.Draw(c)
        mid = lerp(base[0], base[1], 0.5)
        d.rectangle([0, 0, TILE - 1, TILE - 1], fill=mid)
        rnd = random.Random(1000 + row * 17 + col * 3 + seed)
        # soft blotches so large fields still have some large-scale variation
        for _ in range(3):
            bx, by = rnd.randrange(-6, TILE), rnd.randrange(-6, TILE)
            bw, bh = rnd.randrange(10, 22), rnd.randrange(8, 18)
            d.ellipse([bx, by, bx + bw, by + bh], fill=lerp(base[0], base[1], rnd.uniform(0.15, 0.85)))
        speckle(c, 0, 0, TILE, TILE, hi, density, rnd)
        return c

    for ri, name in enumerate(TERRAIN_ROWS):
        for ci in range(TVARIANTS):
            if name == "grass":
                c = cell(ri, ci, GRASS, GRASS_HI, 0.14)
                d = ImageDraw.Draw(c)
                rnd = random.Random(ri * 91 + ci)
                for _ in range(5):  # grass tufts
                    gx, gy = rnd.randrange(2, 30), rnd.randrange(4, 30)
                    d.line([gx, gy, gx, gy - 3], fill=(140, 200, 100, 255))
                    d.line([gx + 1, gy, gx + 2, gy - 2], fill=(118, 178, 86, 255))
            elif name == "forest":
                c = cell(ri, ci, FOREST, FOREST_HI, 0.16)
            elif name == "sand":
                c = cell(ri, ci, SAND, SAND_HI, 0.10)
                d = ImageDraw.Draw(c)
                rnd = random.Random(ri * 41 + ci)
                for _ in range(3):  # ripple lines
                    yy = rnd.randrange(4, 28)
                    d.line([rnd.randrange(0, 10), yy, rnd.randrange(18, 31), yy],
                           fill=(210, 182, 122, 255))
            elif name == "snow":
                c = cell(ri, ci, SNOW, SNOW_HI, 0.10)
            elif name == "stone":
                c = cell(ri, ci, STONE, STONE_HI, 0.16)
                d = ImageDraw.Draw(c)
                rnd = random.Random(ri * 7 + ci)
                for _ in range(2):  # cracks
                    x0, y0 = rnd.randrange(0, 30), rnd.randrange(0, 30)
                    d.line([x0, y0, x0 + rnd.randrange(-8, 9), y0 + rnd.randrange(4, 10)],
                           fill=(84, 80, 92, 255))
            elif name == "ash":
                c = cell(ri, ci, ASH, ASH_HI, 0.14)
            elif name == "void":
                c = cell(ri, ci, VOID, VOID_HI, 0.10)
                d = ImageDraw.Draw(c)
                rnd = random.Random(ri * 13 + ci)
                for _ in range(4):  # stars
                    d.point((rnd.randrange(0, 32), rnd.randrange(0, 32)), fill=(255, 255, 255, 255))
            elif name == "dirt":
                c = cell(ri, ci, DIRT, DIRT_HI, 0.14)
            elif name == "pstone":
                c = img(TILE, TILE)
                d = ImageDraw.Draw(c)
                d.rectangle([0, 0, TILE - 1, TILE - 1], fill=lerp(PSTONE[0], PSTONE[1], .5))
                rnd = random.Random(ri * 29 + ci)
                for by in range(0, TILE, 16):  # brick joints
                    off = 0 if (by // 16) % 2 == 0 else 8
                    d.line([0, by, TILE, by], fill=(120, 116, 126, 255))
                    for bx in range(off, TILE + 16, 16):
                        d.line([bx, by, bx, by + 16], fill=(120, 116, 126, 255))
                speckle(c, 0, 0, TILE, TILE, [(196, 192, 198, 255), (128, 124, 134, 255)], 0.08, rnd)
            elif name == "water":
                c = img(TILE, TILE)
                d = ImageDraw.Draw(c)
                d.rectangle([0,0,TILE-1,TILE-1], fill=lerp(WATER[0], WATER[1], .5))
                phase = ci / TVARIANTS * math.tau
                # rolling wave crests: thin horizontal highlights that drift
                for yy in range(TILE):
                    off = math.sin(yy * 0.5 + phase) * 3.0
                    band = math.sin(yy * 0.8 + phase * 1.4)
                    if band > 0.72:
                        x0 = int(4 + off) % TILE
                        ln = 9 if band > 0.9 else 6
                        for k in range(ln):
                            c.putpixel(((x0 + k) % TILE, yy), (150, 208, 246, 255))
                        for k in range(ln // 2):
                            c.putpixel(((x0 + 14 + k) % TILE, yy), (112, 184, 232, 255))
            elif name == "ice":
                c = cell(ri, ci, ICE, [(212, 240, 252, 255), (110, 162, 200, 255)], 0.08)
                d = ImageDraw.Draw(c)
                rnd = random.Random(ri * 3 + ci)
                x0 = rnd.randrange(2, 24)
                d.line([x0, 2, x0 + 6, 28], fill=(226, 246, 255, 255))
            elif name == "lava":
                c = img(TILE, TILE)
                d = ImageDraw.Draw(c)
                d.rectangle([0,0,TILE-1,TILE-1], fill=lerp(LAVA[0], LAVA[1], .5))
                phase = ci / TVARIANTS * math.tau
                # thin dark crust cracks over molten rock
                for yy in range(TILE):
                    for xx in range(TILE):
                        v = math.sin(xx * 0.55 + math.sin(yy * 0.31 + phase) * 2.2) + \
                            math.sin(yy * 0.48 + math.sin(xx * 0.26 - phase) * 2.0)
                        a = abs(v)
                        if a < 0.16:
                            c.putpixel((xx, yy), (108, 28, 16, 255))
                        elif a < 0.40:
                            c.putpixel((xx, yy), (156, 46, 20, 255))
                        elif a > 1.86:
                            c.putpixel((xx, yy), (255, 240, 176, 255))
            else:
                c = cell(ri, ci, GRASS, GRASS_HI)
            sheet.paste(c, (ci * TILE, ri * TILE))
    sheet.save(f"{OUT}/terrain.png")
    print("terrain.png", sheet.size)


# ================================================================ OBJECTS
OBJ = 64
OBJ_COLS = 5
OBJECT_NAMES = [
    "oak_tree", "pine_tree", "bush", "flower", "log",
    "cactus", "ruin_pillar", "sand_rock", "snow_pine", "ice_crystal",
    "snow_rock", "palm_tree", "coral", "shell", "dead_tree",
    "lava_rock", "ember_vent", "crystal_spire", "float_rock", "star_shard",
    "word_crystal", "shrine", "gate", "chest", "signpost",
]


def draw_tree(c, trunk_a, trunk_b, leaf_a, leaf_b, leaf_hi, shape="round"):
    d = ImageDraw.Draw(c)
    # trunk
    vgrad(d, 28, 40, 8, 20, trunk_a, trunk_b)
    d.line([30, 44, 30, 58], fill=trunk_b)
    if shape == "round":
        d.ellipse([12, 8, 52, 46], fill=leaf_b)
        d.ellipse([14, 6, 48, 40], fill=leaf_a)
        d.ellipse([18, 8, 38, 26], fill=leaf_hi)
    elif shape == "pine":
        for i, (wy, wh) in enumerate([(6, 16), (18, 20), (30, 22)]):
            half = 8 + i * 6
            d.polygon([(32, wy), (32 - half, wy + wh), (32 + half, wy + wh)], fill=leaf_a)
            d.polygon([(32, wy + 2), (32 - half + 4, wy + wh), (32, wy + wh)], fill=leaf_hi)
    elif shape == "palm":
        for ang in (-1.15, -0.55, 0.0, 0.55, 1.15):
            ex = 32 + int(math.sin(ang) * 26)
            ey = 22 - int(math.cos(ang) * 14)
            d.line([32, 24, ex, ey], fill=leaf_a, width=5)
            d.line([32, 24, ex, ey], fill=leaf_hi, width=2)
    return c


def make_objects():
    rows = (len(OBJECT_NAMES) + OBJ_COLS - 1) // OBJ_COLS
    sheet = img(OBJ * OBJ_COLS, OBJ * rows)

    for idx, name in enumerate(OBJECT_NAMES):
        c = img(OBJ, OBJ)
        d = ImageDraw.Draw(c)

        if name == "oak_tree":
            draw_tree(c, (128, 88, 52, 255), (88, 58, 34, 255),
                      (86, 154, 70, 255), (56, 110, 52, 255), (122, 186, 92, 255), "round")
        elif name == "pine_tree":
            draw_tree(c, (110, 76, 46, 255), (76, 50, 30, 255),
                      (54, 112, 66, 255), (36, 82, 50, 255), (78, 142, 84, 255), "pine")
        elif name == "bush":
            d.ellipse([14, 30, 50, 58], fill=(52, 106, 50, 255))
            d.ellipse([17, 27, 44, 50], fill=(78, 142, 66, 255))
            d.ellipse([22, 30, 34, 40], fill=(108, 174, 88, 255))
            for bx, by in ((22, 40), (38, 44), (30, 34)):
                d.ellipse([bx, by, bx + 3, by + 3], fill=(226, 84, 84, 255))
        elif name == "flower":
            d.line([32, 58, 32, 46], fill=(88, 148, 66, 255))
            for ox, oy in ((-4, -4), (4, -4), (-4, 4), (4, 4)):
                d.ellipse([30 + ox, 42 + oy, 34 + ox, 46 + oy], fill=(238, 128, 176, 255))
            d.ellipse([30, 42, 34, 46], fill=(250, 220, 96, 255))
        elif name == "log":
            vgrad(d, 12, 44, 40, 14, (140, 100, 62, 255), (100, 68, 40, 255))
            d.ellipse([8, 44, 20, 58], fill=(168, 128, 82, 255))
            d.ellipse([11, 47, 17, 55], fill=(120, 84, 50, 255))
        elif name == "cactus":
            vgrad(d, 26, 18, 12, 42, (86, 150, 84, 255), (52, 104, 60, 255))
            vgrad(d, 14, 30, 10, 8, (86, 150, 84, 255), (52, 104, 60, 255))
            vgrad(d, 14, 22, 6, 12, (86, 150, 84, 255), (52, 104, 60, 255))
            vgrad(d, 40, 36, 10, 8, (86, 150, 84, 255), (52, 104, 60, 255))
            vgrad(d, 44, 26, 6, 14, (86, 150, 84, 255), (52, 104, 60, 255))
            for yy in range(22, 58, 5):
                d.point((29, yy), fill=(226, 226, 180, 255))
                d.point((35, yy + 2), fill=(226, 226, 180, 255))
        elif name == "ruin_pillar":
            vgrad(d, 22, 14, 20, 44, (206, 186, 150, 255), (150, 130, 100, 255))
            d.rectangle([18, 52, 46, 60], fill=(178, 158, 124, 255))
            d.rectangle([19, 10, 45, 18], fill=(196, 176, 142, 255))
            for yy in (26, 38):
                d.line([22, yy, 42, yy], fill=(132, 114, 88, 255))
            d.polygon([(22, 14), (30, 14), (26, 22)], fill=(0, 0, 0, 0))
        elif name == "sand_rock":
            d.ellipse([14, 34, 50, 58], fill=(186, 160, 116, 255))
            d.ellipse([18, 30, 42, 50], fill=(214, 190, 146, 255))
            d.ellipse([22, 34, 32, 42], fill=(232, 212, 172, 255))
        elif name == "snow_pine":
            draw_tree(c, (98, 72, 50, 255), (68, 48, 34, 255),
                      (48, 96, 72, 255), (32, 72, 56, 255), (72, 126, 96, 255), "pine")
            for wy, half in ((22, 12), (34, 18), (46, 24)):
                d.line([32 - half + 2, wy, 32 + half - 2, wy], fill=(238, 246, 255, 255))
            d.polygon([(32, 6), (26, 14), (38, 14)], fill=(238, 246, 255, 255))
        elif name == "ice_crystal":
            d.polygon([(32, 8), (44, 34), (32, 58), (20, 34)], fill=(150, 206, 236, 255))
            d.polygon([(32, 12), (39, 34), (32, 50), (26, 34)], fill=(206, 238, 252, 255))
            d.polygon([(32, 12), (39, 34), (32, 34)], fill=(238, 250, 255, 255))
        elif name == "snow_rock":
            d.ellipse([14, 34, 50, 58], fill=(150, 158, 176, 255))
            d.ellipse([18, 30, 44, 50], fill=(184, 194, 212, 255))
            d.ellipse([18, 30, 44, 40], fill=(238, 246, 255, 255))
        elif name == "palm_tree":
            draw_tree(c, (146, 112, 70, 255), (104, 76, 46, 255),
                      (72, 152, 88, 255), (46, 112, 66, 255), (110, 190, 118, 255), "palm")
            for bx, by in ((28, 28), (34, 30), (31, 33)):
                d.ellipse([bx, by, bx + 4, by + 4], fill=(196, 140, 60, 255))
        elif name == "coral":
            for ox, h, col in ((-8, 18, (232, 118, 128, 255)), (0, 26, (246, 150, 158, 255)), (8, 16, (214, 96, 118, 255))):
                d.line([32 + ox, 58, 32 + ox, 58 - h], fill=col, width=5)
                d.line([32 + ox, 58 - h, 32 + ox - 5, 58 - h - 6], fill=col, width=4)
                d.line([32 + ox, 58 - h, 32 + ox + 5, 58 - h - 6], fill=col, width=4)
        elif name == "shell":
            d.pieslice([18, 32, 46, 60], 180, 360, fill=(248, 214, 198, 255))
            for a in range(190, 360, 22):
                rad = math.radians(a)
                d.line([32, 60, 32 + int(math.cos(rad) * 14), 60 + int(math.sin(rad) * 14)],
                       fill=(226, 172, 156, 255))
        elif name == "dead_tree":
            vgrad(d, 28, 24, 8, 36, (108, 88, 78, 255), (70, 56, 50, 255))
            d.line([31, 34, 18, 20], fill=(96, 78, 70, 255), width=3)
            d.line([31, 40, 46, 24], fill=(96, 78, 70, 255), width=3)
            d.line([18, 20, 12, 14], fill=(84, 68, 62, 255), width=2)
            d.line([46, 24, 52, 16], fill=(84, 68, 62, 255), width=2)
        elif name == "lava_rock":
            d.ellipse([12, 32, 52, 58], fill=(66, 50, 52, 255))
            d.ellipse([16, 28, 44, 48], fill=(92, 70, 68, 255))
            for lx, ly in ((22, 42), (34, 38), (30, 48)):
                d.ellipse([lx, ly, lx + 6, ly + 4], fill=(240, 128, 40, 255))
                d.ellipse([lx + 1, ly + 1, lx + 4, ly + 3], fill=(255, 208, 110, 255))
        elif name == "ember_vent":
            d.ellipse([16, 40, 48, 60], fill=(58, 44, 46, 255))
            d.ellipse([22, 44, 42, 56], fill=(196, 74, 28, 255))
            d.ellipse([26, 46, 38, 54], fill=(255, 190, 90, 255))
            for ex, ey in ((28, 30), (36, 22), (32, 14)):
                d.ellipse([ex, ey, ex + 4, ey + 4], fill=(250, 156, 60, 255))
        elif name == "crystal_spire":
            d.polygon([(32, 4), (46, 40), (32, 60), (18, 40)], fill=(126, 96, 208, 255))
            d.polygon([(32, 10), (40, 40), (32, 52), (26, 40)], fill=(176, 148, 246, 255))
            d.polygon([(32, 10), (40, 40), (32, 40)], fill=(226, 212, 255, 255))
            d.point((30, 22), fill=(255, 255, 255, 255))
        elif name == "float_rock":
            d.ellipse([14, 26, 50, 48], fill=(74, 60, 118, 255))
            d.ellipse([18, 22, 44, 40], fill=(104, 86, 156, 255))
            d.ellipse([22, 24, 34, 32], fill=(140, 122, 196, 255))
            for sx, sy in ((20, 52), (32, 56), (44, 52)):
                d.point((sx, sy), fill=(196, 180, 255, 255))
        elif name == "star_shard":
            for a in range(0, 360, 45):
                rad = math.radians(a)
                ln = 18 if a % 90 == 0 else 10
                d.line([32, 38, 32 + int(math.cos(rad) * ln), 38 + int(math.sin(rad) * ln)],
                       fill=(250, 236, 160, 255), width=3)
            d.ellipse([27, 33, 37, 43], fill=(255, 252, 226, 255))
        elif name == "word_crystal":
            d.polygon([(32, 12), (44, 34), (32, 56), (20, 34)], fill=(96, 200, 214, 255))
            d.polygon([(32, 18), (39, 34), (32, 48), (26, 34)], fill=(168, 240, 246, 255))
            d.polygon([(32, 18), (39, 34), (32, 34)], fill=(232, 254, 255, 255))
            d.point((29, 26), fill=(255, 255, 255, 255))
        elif name == "shrine":
            d.rectangle([10, 48, 54, 60], fill=(148, 132, 112, 255))
            d.rectangle([13, 44, 51, 50], fill=(182, 166, 140, 255))
            vgrad(d, 18, 16, 28, 30, (206, 190, 162, 255), (152, 136, 112, 255))
            d.polygon([(32, 4), (52, 20), (12, 20)], fill=(178, 146, 82, 255))
            d.polygon([(32, 8), (46, 19), (18, 19)], fill=(214, 182, 112, 255))
            d.ellipse([26, 26, 38, 40], fill=(120, 210, 224, 255))
            d.ellipse([28, 28, 34, 34], fill=(226, 252, 255, 255))
        elif name == "gate":
            for gx in (8, 44):
                vgrad(d, gx, 14, 12, 46, (168, 152, 128, 255), (112, 100, 82, 255))
                d.rectangle([gx - 2, 10, gx + 14, 16], fill=(190, 172, 144, 255))
            d.rectangle([6, 4, 58, 12], fill=(150, 134, 110, 255))
            d.rectangle([20, 20, 44, 60], fill=(72, 54, 44, 255))
            d.rectangle([23, 24, 41, 58], fill=(104, 78, 58, 255))
            d.ellipse([29, 38, 35, 44], fill=GOLD)
        elif name == "chest":
            vgrad(d, 14, 34, 36, 22, (150, 106, 60, 255), (108, 74, 40, 255))
            d.pieslice([14, 22, 50, 46], 180, 360, fill=(172, 124, 70, 255))
            d.rectangle([14, 40, 50, 44], fill=GOLD_D)
            d.rectangle([28, 36, 36, 48], fill=GOLD)
            d.ellipse([30, 40, 34, 44], fill=(70, 50, 28, 255))
        elif name == "signpost":
            vgrad(d, 30, 34, 5, 26, (128, 94, 58, 255), (94, 68, 42, 255))
            d.rectangle([12, 20, 52, 36], fill=(166, 126, 78, 255))
            d.rectangle([14, 22, 50, 34], fill=(196, 158, 106, 255))
            for yy in (26, 30):
                d.line([18, yy, 46, yy], fill=(126, 94, 60, 255))

        if name not in ("word_crystal", "star_shard", "flower"):
            c = shadow(c, 32, 59, 34, 10, 70)
        c = outline(c)
        sheet.paste(c, ((idx % OBJ_COLS) * OBJ, (idx // OBJ_COLS) * OBJ), c)

    sheet.save(f"{OUT}/objects.png")
    print("objects.png", sheet.size, len(OBJECT_NAMES), "objects")


# ================================================================ MONSTERS
MON = 32
MONSTER_NAMES = ["leaf_sprite", "sand_imp", "frost_bat", "tide_crab", "ember_hound", "void_eye"]


def make_monsters():
    frames = 2
    sheet = img(MON * frames, MON * len(MONSTER_NAMES))
    for mi, name in enumerate(MONSTER_NAMES):
        for f in range(frames):
            c = img(MON, MON)
            d = ImageDraw.Draw(c)
            bob = f * 2

            if name == "leaf_sprite":
                d.ellipse([6, 10 - bob, 26, 28 - bob], fill=(84, 156, 76, 255))
                d.ellipse([9, 8 - bob, 22, 22 - bob], fill=(118, 190, 98, 255))
                d.polygon([(16, 2 - bob), (22, 10 - bob), (10, 10 - bob)], fill=(66, 130, 62, 255))
                d.ellipse([11, 15 - bob, 14, 19 - bob], fill=(24, 24, 32, 255))
                d.ellipse([19, 15 - bob, 22, 19 - bob], fill=(24, 24, 32, 255))
            elif name == "sand_imp":
                d.ellipse([7, 12 - bob, 25, 28 - bob], fill=(198, 158, 96, 255))
                d.polygon([(8, 14 - bob), (2, 6 - bob), (12, 10 - bob)], fill=(174, 134, 78, 255))
                d.polygon([(24, 14 - bob), (30, 6 - bob), (20, 10 - bob)], fill=(174, 134, 78, 255))
                d.ellipse([11, 17 - bob, 14, 21 - bob], fill=(196, 48, 40, 255))
                d.ellipse([19, 17 - bob, 22, 21 - bob], fill=(196, 48, 40, 255))
                d.line([12, 24 - bob, 20, 24 - bob], fill=(90, 60, 34, 255))
            elif name == "frost_bat":
                d.ellipse([11, 12 - bob, 21, 24 - bob], fill=(150, 196, 226, 255))
                wing = 6 + f * 3
                d.polygon([(11, 14 - bob), (1, 14 - wing - bob), (4, 22 - bob)], fill=(184, 220, 244, 255))
                d.polygon([(21, 14 - bob), (31, 14 - wing - bob), (28, 22 - bob)], fill=(184, 220, 244, 255))
                d.ellipse([13, 15 - bob, 15, 18 - bob], fill=(40, 80, 120, 255))
                d.ellipse([18, 15 - bob, 20, 18 - bob], fill=(40, 80, 120, 255))
            elif name == "tide_crab":
                d.ellipse([6, 14 - bob, 26, 27 - bob], fill=(216, 104, 84, 255))
                d.ellipse([9, 13 - bob, 22, 22 - bob], fill=(240, 140, 116, 255))
                cl = 2 if f == 0 else 4
                d.ellipse([1, 16 - bob, 8, 23 - bob], fill=(200, 84, 68, 255))
                d.ellipse([24, 16 - bob, 31, 23 - bob], fill=(200, 84, 68, 255))
                d.ellipse([11, 10 - bob, 14, 15 - bob], fill=(30, 30, 40, 255))
                d.ellipse([18, 10 - bob, 21, 15 - bob], fill=(30, 30, 40, 255))
                d.line([4, 27 - bob, 8, 24 - bob], fill=(180, 74, 60, 255), width=cl)
            elif name == "ember_hound":
                d.ellipse([5, 14 - bob, 27, 27 - bob], fill=(72, 52, 54, 255))
                d.ellipse([18, 9 - bob, 30, 21 - bob], fill=(88, 62, 62, 255))
                d.polygon([(20, 10 - bob), (22, 3 - bob), (25, 10 - bob)], fill=(72, 52, 54, 255))
                d.ellipse([24, 13 - bob, 27, 16 - bob], fill=(255, 168, 60, 255))
                for ex in (8, 13, 18):
                    d.ellipse([ex, 10 - bob - f * 2, ex + 3, 13 - bob - f * 2], fill=(248, 140, 48, 255))
                d.line([5, 20 - bob, 1, 14 - bob], fill=(72, 52, 54, 255), width=3)
            elif name == "void_eye":
                d.ellipse([5, 6 - bob, 27, 26 - bob], fill=(64, 44, 108, 255))
                d.ellipse([8, 9 - bob, 24, 23 - bob], fill=(200, 210, 240, 255))
                pupil = 14 + (2 if f else -2)
                d.ellipse([pupil, 12 - bob, pupil + 5, 20 - bob], fill=(30, 20, 50, 255))
                for a in range(0, 360, 60):
                    rad = math.radians(a + f * 20)
                    d.point((16 + int(math.cos(rad) * 14), 16 - bob + int(math.sin(rad) * 14)),
                            fill=(196, 172, 255, 255))

            c = shadow(c, 16, 29, 20, 6, 80)
            c = outline(c)
            sheet.paste(c, (f * MON, mi * MON), c)
    sheet.save(f"{OUT}/monsters.png")
    print("monsters.png", sheet.size)


# ================================================================ BOSSES
BOSS = 64
BOSS_NAMES = ["forest_golem", "sand_pharaoh", "frost_wyrm", "tide_kraken", "ember_titan", "void_sovereign"]


def make_bosses():
    sheet = img(BOSS * 2, BOSS * len(BOSS_NAMES))
    for bi, name in enumerate(BOSS_NAMES):
        for f in range(2):
            c = img(BOSS, BOSS)
            d = ImageDraw.Draw(c)
            bob = f * 2

            if name == "forest_golem":
                d.rectangle([14, 22 - bob, 50, 52 - bob], fill=(112, 118, 124, 255))
                d.rectangle([17, 25 - bob, 47, 40 - bob], fill=(138, 144, 150, 255))
                d.rectangle([20, 8 - bob, 44, 26 - bob], fill=(124, 130, 136, 255))
                d.ellipse([12, 4 - bob, 52, 20 - bob], fill=(74, 138, 70, 255))
                d.ellipse([16, 2 - bob, 44, 16 - bob], fill=(102, 170, 88, 255))
                for ex in (25, 36):
                    d.rectangle([ex, 16 - bob, ex + 4, 20 - bob], fill=(250, 226, 120, 255))
                d.rectangle([2, 26 - bob, 14, 50 - bob], fill=(112, 118, 124, 255))
                d.rectangle([50, 26 - bob, 62, 50 - bob], fill=(112, 118, 124, 255))
                d.rectangle([18, 52 - bob, 28, 62], fill=(96, 102, 110, 255))
                d.rectangle([36, 52 - bob, 46, 62], fill=(96, 102, 110, 255))
                for mx, my in ((20, 30), (38, 42), (28, 46)):
                    d.ellipse([mx, my - bob, mx + 7, my + 5 - bob], fill=(86, 150, 76, 255))
            elif name == "sand_pharaoh":
                d.polygon([(32, 2 - bob), (52, 26 - bob), (12, 26 - bob)], fill=(226, 194, 120, 255))
                d.polygon([(32, 6 - bob), (46, 26 - bob), (32, 26 - bob)], fill=(198, 164, 96, 255))
                d.rectangle([18, 24 - bob, 46, 46 - bob], fill=(232, 210, 168, 255))
                d.rectangle([21, 27 - bob, 43, 40 - bob], fill=(206, 182, 140, 255))
                for ex in (25, 35):
                    d.ellipse([ex, 30 - bob, ex + 5, 35 - bob], fill=(60, 190, 200, 255))
                d.rectangle([14, 44 - bob, 50, 62], fill=(214, 186, 140, 255))
                for yy in range(48, 62, 4):
                    d.line([14, yy - bob, 50, yy - bob], fill=(180, 152, 110, 255))
                d.rectangle([26, 20 - bob, 38, 24 - bob], fill=GOLD)
            elif name == "frost_wyrm":
                d.ellipse([8, 26 - bob, 56, 54 - bob], fill=(148, 200, 232, 255))
                d.ellipse([12, 24 - bob, 44, 44 - bob], fill=(190, 228, 248, 255))
                d.ellipse([34, 8 - bob, 60, 32 - bob], fill=(166, 214, 240, 255))
                d.polygon([(40, 12 - bob), (36, 2 - bob), (46, 8 - bob)], fill=(212, 240, 252, 255))
                d.polygon([(52, 12 - bob), (56, 2 - bob), (58, 12 - bob)], fill=(212, 240, 252, 255))
                d.ellipse([48, 16 - bob, 53, 22 - bob], fill=(40, 96, 150, 255))
                wing = 8 + f * 4
                d.polygon([(20, 28 - bob), (2, 10 - wing - bob), (16, 40 - bob)], fill=(184, 224, 248, 255))
                d.line([8, 52 - bob, 2, 60 - bob], fill=(148, 200, 232, 255), width=5)
            elif name == "tide_kraken":
                d.ellipse([16, 6 - bob, 48, 38 - bob], fill=(88, 158, 156, 255))
                d.ellipse([20, 4 - bob, 42, 26 - bob], fill=(120, 194, 186, 255))
                for ex in (24, 34):
                    d.ellipse([ex, 18 - bob, ex + 7, 27 - bob], fill=(250, 250, 226, 255))
                    d.ellipse([ex + 2, 21 - bob, ex + 5, 25 - bob], fill=(20, 30, 40, 255))
                for i, ox in enumerate((4, 14, 26, 38, 50)):
                    amp = 6 if (i + f) % 2 == 0 else -6
                    d.line([ox + 4, 36 - bob, ox, 48 - bob], fill=(76, 142, 142, 255), width=5)
                    d.line([ox, 48 - bob, ox + amp, 60], fill=(96, 166, 160, 255), width=4)
            elif name == "ember_titan":
                d.rectangle([16, 20 - bob, 48, 50 - bob], fill=(66, 48, 50, 255))
                d.rectangle([19, 23 - bob, 45, 38 - bob], fill=(90, 66, 64, 255))
                d.ellipse([18, 4 - bob, 46, 24 - bob], fill=(74, 54, 56, 255))
                for ex in (24, 34):
                    d.ellipse([ex, 12 - bob, ex + 6, 18 - bob], fill=(255, 176, 62, 255))
                for cx, cy, cw in ((22, 26, 8), (36, 30, 9), (28, 40, 10)):
                    d.ellipse([cx, cy - bob, cx + cw, cy + 5 - bob], fill=(238, 110, 32, 255))
                    d.ellipse([cx + 1, cy + 1 - bob, cx + cw - 2, cy + 4 - bob], fill=(255, 214, 120, 255))
                d.rectangle([2, 24 - bob, 15, 48 - bob], fill=(66, 48, 50, 255))
                d.rectangle([49, 24 - bob, 62, 48 - bob], fill=(66, 48, 50, 255))
                d.rectangle([2, 44 - bob, 15, 48 - bob], fill=(240, 128, 40, 255))
                d.rectangle([49, 44 - bob, 62, 48 - bob], fill=(240, 128, 40, 255))
                d.rectangle([18, 50 - bob, 30, 62], fill=(58, 42, 44, 255))
                d.rectangle([34, 50 - bob, 46, 62], fill=(58, 42, 44, 255))
            elif name == "void_sovereign":
                d.polygon([(32, 2 - bob), (50, 18 - bob), (44, 22 - bob), (20, 22 - bob), (14, 18 - bob)],
                          fill=(58, 38, 92, 255))
                for cx in (20, 32, 44):
                    d.polygon([(cx - 3, 14 - bob), (cx, 4 - bob), (cx + 3, 14 - bob)], fill=GOLD)
                d.ellipse([14, 16 - bob, 50, 44 - bob], fill=(44, 28, 74, 255))
                d.ellipse([18, 18 - bob, 46, 38 - bob], fill=(72, 50, 118, 255))
                for ex in (24, 36):
                    d.ellipse([ex, 24 - bob, ex + 5, 31 - bob], fill=(210, 172, 255, 255))
                    d.ellipse([ex + 1, 26 - bob, ex + 3, 29 - bob], fill=(255, 255, 255, 255))
                d.polygon([(10, 40 - bob), (54, 40 - bob), (58, 62), (6, 62)], fill=(50, 32, 82, 255))
                d.polygon([(16, 42 - bob), (48, 42 - bob), (50, 62), (14, 62)], fill=(68, 46, 108, 255))
                rnd = random.Random(bi * 10 + f)
                for _ in range(10):
                    d.point((rnd.randrange(8, 56), rnd.randrange(44, 62)), fill=(226, 210, 255, 255))

            c = shadow(c, 32, 61, 40, 10, 90)
            c = outline(c)
            sheet.paste(c, (f * BOSS, bi * BOSS), c)
    sheet.save(f"{OUT}/bosses.png")
    print("bosses.png", sheet.size)


# ================================================================ PLAYER
PW, PH = 24, 32
DIRS = ["down", "left", "right", "up"]
STAGES = 4


def make_player():
    SKIN = (240, 198, 152, 255)
    SKIN_D = (198, 152, 112, 255)
    HAIR = (108, 68, 38, 255)
    HAIR_D = (76, 46, 24, 255)

    kits = [
        # tunic, tunic dark, pants, boots, has_helm, has_cape, has_sword, metal
        dict(body=(74, 124, 92, 255), body_d=(50, 90, 68, 255), pants=(96, 72, 50, 255),
             boots=(74, 52, 34, 255), helm=False, cape=False, sword=False, metal=None),
        dict(body=(132, 96, 58, 255), body_d=(98, 68, 40, 255), pants=(88, 66, 46, 255),
             boots=(66, 46, 30, 255), helm=True, cape=False, sword=True, metal=(178, 172, 180, 255)),
        dict(body=(178, 180, 190, 255), body_d=(126, 128, 140, 255), pants=(88, 90, 102, 255),
             boots=(70, 72, 84, 255), helm=True, cape=False, sword=True, metal=(214, 216, 226, 255)),
        dict(body=(224, 226, 236, 255), body_d=(160, 164, 182, 255), pants=(96, 100, 118, 255),
             boots=(76, 80, 96, 255), helm=True, cape=True, sword=True, metal=(246, 248, 255, 255)),
    ]

    for si, kit in enumerate(kits):
        sheet = img(PW * 4, PH * 4)
        for di, dirn in enumerate(DIRS):
            for f in range(4):
                c = img(PW, PH)
                d = ImageDraw.Draw(c)
                # walk cycle: 0,2 = neutral; 1 = left lead; 3 = right lead
                swing = {0: 0, 1: 2, 2: 0, 3: -2}[f]
                bob = 1 if f in (1, 3) else 0
                top = 4 + bob

                # cape behind body
                if kit["cape"] and dirn != "up":
                    d.polygon([(6, top + 9), (18, top + 9), (20, top + 24), (4, top + 24)],
                              fill=(150, 42, 48, 255))
                elif kit["cape"]:
                    d.polygon([(5, top + 8), (19, top + 8), (21, top + 26), (3, top + 26)],
                              fill=(178, 56, 60, 255))

                # legs
                lx1, lx2 = 8, 13
                d.rectangle([lx1, top + 18, lx1 + 3, top + 24 + swing // 2], fill=kit["pants"])
                d.rectangle([lx2, top + 18, lx2 + 3, top + 24 - swing // 2], fill=kit["pants"])
                d.rectangle([lx1, top + 23 + swing // 2, lx1 + 3, top + 26 + swing // 2], fill=kit["boots"])
                d.rectangle([lx2, top + 23 - swing // 2, lx2 + 3, top + 26 - swing // 2], fill=kit["boots"])

                # torso
                d.rectangle([7, top + 9, 17, top + 19], fill=kit["body"])
                d.rectangle([7, top + 9, 9, top + 19], fill=kit["body_d"])
                if kit["metal"]:
                    d.rectangle([10, top + 10, 14, top + 12], fill=kit["metal"])
                    d.line([12, top + 12, 12, top + 18], fill=GOLD)

                # arms
                arm_off = swing // 2
                d.rectangle([4, top + 10 - arm_off, 6, top + 17 - arm_off], fill=kit["body_d"])
                d.rectangle([18, top + 10 + arm_off, 20, top + 17 + arm_off], fill=kit["body_d"])
                d.rectangle([4, top + 16 - arm_off, 6, top + 18 - arm_off], fill=SKIN)
                d.rectangle([18, top + 16 + arm_off, 20, top + 18 + arm_off], fill=SKIN)

                # head
                d.rectangle([8, top, 16, top + 8], fill=SKIN)
                d.rectangle([8, top, 9, top + 8], fill=SKIN_D)
                if kit["helm"]:
                    d.rectangle([7, top - 2, 17, top + 3], fill=kit["metal"])
                    d.rectangle([7, top + 3, 17, top + 4], fill=GOLD_D)
                    if dirn == "down":
                        d.rectangle([10, top + 4, 14, top + 5], fill=(40, 36, 48, 255))
                else:
                    d.rectangle([7, top - 2, 17, top + 3], fill=HAIR)
                    d.rectangle([7, top + 2, 8, top + 5], fill=HAIR_D)
                    d.rectangle([16, top + 2, 17, top + 5], fill=HAIR_D)

                # face
                if dirn == "down":
                    d.point((10, top + 4), fill=(40, 34, 44, 255))
                    d.point((14, top + 4), fill=(40, 34, 44, 255))
                elif dirn == "left":
                    d.point((10, top + 4), fill=(40, 34, 44, 255))
                elif dirn == "right":
                    d.point((14, top + 4), fill=(40, 34, 44, 255))

                # sword
                if kit["sword"]:
                    sx = 20 if dirn != "left" else 3
                    d.line([sx, top + 6, sx, top + 17], fill=kit["metal"] or (200, 200, 210, 255))
                    d.line([sx - 1, top + 17, sx + 1, top + 17], fill=GOLD_D)
                    if si == 3:  # champion blade glows
                        d.line([sx, top + 6, sx, top + 10], fill=(180, 240, 255, 255))

                c = shadow(c, 12, 30, 16, 5, 70)
                c = outline(c)
                sheet.paste(c, (f * PW, di * PH), c)
        sheet.save(f"{OUT}/player_s{si}.png")
        print(f"player_s{si}.png", sheet.size)


# ================================================================ GEAR ICONS
def make_gear_icons():
    names = ["helmet", "armor", "boots", "gauntlet", "weapon", "ring"]
    S = 24
    sheet = img(S * len(names), S)
    ST = (206, 210, 222, 255)
    STD = (140, 146, 162, 255)
    for i, name in enumerate(names):
        c = img(S, S)
        d = ImageDraw.Draw(c)
        if name == "helmet":
            d.pieslice([4, 5, 20, 21], 180, 360, fill=ST)
            d.rectangle([4, 13, 20, 18], fill=STD)
            d.rectangle([9, 13, 15, 18], fill=(48, 44, 58, 255))
            d.rectangle([10, 2, 14, 7], fill=GOLD)
        elif name == "armor":
            d.polygon([(6, 5), (18, 5), (20, 10), (18, 20), (6, 20), (4, 10)], fill=ST)
            d.polygon([(6, 5), (12, 5), (12, 20), (6, 20), (4, 10)], fill=STD)
            d.line([12, 7, 12, 19], fill=GOLD)
        elif name == "boots":
            d.rectangle([7, 4, 13, 16], fill=STD)
            d.polygon([(5, 16), (17, 16), (18, 20), (5, 20)], fill=ST)
            d.line([7, 8, 13, 8], fill=GOLD)
        elif name == "gauntlet":
            d.rectangle([7, 4, 16, 13], fill=ST)
            d.rectangle([6, 13, 17, 18], fill=STD)
            d.line([6, 15, 17, 15], fill=GOLD)
            d.rectangle([9, 18, 14, 21], fill=(240, 198, 152, 255))
        elif name == "weapon":
            d.polygon([(12, 1), (14, 5), (14, 14), (10, 14), (10, 5)], fill=ST)
            d.line([12, 2, 12, 13], fill=(246, 250, 255, 255))
            d.rectangle([6, 14, 18, 16], fill=GOLD_D)
            d.rectangle([11, 16, 13, 21], fill=(122, 84, 48, 255))
            d.ellipse([10, 20, 14, 23], fill=GOLD)
        elif name == "ring":
            d.ellipse([6, 9, 18, 21], outline=GOLD, width=3)
            d.polygon([(12, 1), (17, 7), (12, 11), (7, 7)], fill=(150, 210, 250, 255))
            d.polygon([(12, 3), (15, 7), (12, 9)], fill=(226, 246, 255, 255))
        c = outline(c)
        sheet.paste(c, (i * S, 0), c)
    sheet.save(f"{OUT}/gear.png")
    print("gear.png", sheet.size)


if __name__ == "__main__":
    make_terrain()
    make_objects()
    make_monsters()
    make_bosses()
    make_player()
    make_gear_icons()
    print("ALL DONE ->", OUT)
