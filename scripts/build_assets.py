"""Build Lexicora's runtime atlases from the vendored LPC Revised source art.

Source art lives in assets/src/lpc/ and is licensed CC-BY 3.0 / OGA-BY 3.0
(see CREDITS.md). Nothing here draws pixels by hand — every tile and prop is
cut out of the original sheets; we only crop, pick and pack.

Run:  python3 scripts/build_assets.py
"""
from PIL import Image
import json, os, sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "src", "lpc")
OUT = os.path.join(ROOT, "assets")
TILE = 32


def load(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        sys.exit(f"missing source art: {p}\n(run scripts/fetch_assets.sh first)")
    return Image.open(p).convert("RGBA")


def tile_at(im, tx, ty):
    return im.crop((tx * TILE, ty * TILE, (tx + 1) * TILE, (ty + 1) * TILE))


# --------------------------------------------------------------- extraction
def components(im, min_px=120, pad=0):
    """Bounding boxes of connected opaque blobs, ordered top-left to bottom-right."""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    boxes = []
    for sy in range(h):
        for sx in range(w):
            if seen[sy * w + sx] or px[sx, sy][3] < 8:
                continue
            q = deque([(sx, sy)])
            seen[sy * w + sx] = 1
            x0 = x1 = sx
            y0 = y1 = sy
            n = 0
            while q:
                x, y = q.popleft()
                n += 1
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3] >= 8:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            if n >= min_px:
                boxes.append((max(0, x0 - pad), max(0, y0 - pad),
                              min(w, x1 + 1 + pad), min(h, y1 + 1 + pad)))
    boxes.sort(key=lambda b: (b[1] // 24, b[0]))
    return boxes


def cutouts(im, min_px=120, limit=None, min_w=8, min_h=8):
    out = []
    for (x0, y0, x1, y1) in components(im, min_px):
        if x1 - x0 < min_w or y1 - y0 < min_h:
            continue
        out.append(im.crop((x0, y0, x1, y1)))
        if limit and len(out) >= limit:
            break
    return out


# ============================================================ TERRAIN ATLAS
# The LPC sheets are blob-autotile layouts, so most cells are transition
# pieces. We want the solid interior of a blob: fully opaque and low variance.
TERRAIN_ROWS = ["grass", "forest", "sand", "snow", "stone", "ash",
                "void", "dirt", "pstone", "water", "ice", "lava"]
TVARIANTS = 4


def interior_tiles(sheet):
    """Every fully-opaque cell, with its colour spread and mean colour."""
    out = []
    for ty in range(sheet.height // TILE):
        for tx in range(sheet.width // TILE):
            c = tile_at(sheet, tx, ty)
            px = list(c.getdata())
            if any(p[3] < 250 for p in px):
                continue
            n = len(px)
            mean = [sum(p[i] for p in px) / n for i in range(3)]
            var = sum(sum((p[i] - mean[i]) ** 2 for i in range(3)) for p in px) / (n * 3)
            out.append({"tx": tx, "ty": ty, "img": c, "mean": mean, "var": var ** .5})
    return out


def pick_fill(sheet, target, name, spread=14.0, count=TVARIANTS):
    """Interior cells closest to `target`, preferring flat ones for variant 0."""
    cands = [t for t in interior_tiles(sheet) if t["var"] <= spread]
    if not cands:
        sys.exit(f"no interior tile found for {name}")
    def dist(t):
        return sum((t["mean"][i] - target[i]) ** 2 for i in range(3)) ** .5
    cands.sort(key=lambda t: (dist(t), t["var"]))
    best = cands[0]
    near = [t for t in cands if dist(t) < dist(best) + 26][:count]
    while len(near) < count:
        near.append(best)
    print(f"    {name:<7} <- tiles {[(t['tx'], t['ty']) for t in near]} "
          f"rgb={tuple(int(v) for v in best['mean'])}")
    return [t["img"] for t in near[:count]]


def mean_rgb(im):
    px = [p for p in im.getdata() if p[3] > 0] or [(0, 0, 0, 0)]
    return [sum(p[i] for p in px) / len(px) for i in range(3)]


def harmonise(variants, strength=.82):
    """Pull every variant's overall tone onto the first one's.

    Stone, ash and paved stone come off sheets that carry several distinct rock
    colours. Scattered one per 32px tile, those read as a checkerboard rather
    than as ground. Matching the tone leaves only the texture varying, which is
    what actually makes a surface look continuous.
    """
    base = mean_rgb(variants[0])
    out = [variants[0]]
    for v in variants[1:]:
        m = mean_rgb(v)
        mul = tuple((base[i] * strength + m[i] * (1 - strength)) / max(1.0, m[i])
                    for i in range(3))
        out.append(tint(v, mul))
    return out


def tint(im, mul, add=(0, 0, 0)):
    """Recolour a real tile (still an LPC derivative — credited the same way)."""
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            px[x, y] = (min(255, int(r * mul[0] + add[0])),
                        min(255, int(g * mul[1] + add[1])),
                        min(255, int(b * mul[2] + add[2])), a)
    return out


# --------------------------------------------------------------- autotiling
# Each seasonal sheet carries a 3x3 "ring": the eight border tiles of a patch,
# with a soft alpha edge facing outward. Those alpha edges are the shape of a
# real LPC boundary, so we reuse them as stencils: mask a terrain's own fill
# texture through a ring cell and you get an authentic edge in that terrain's
# colour, for terrains LPC never drew a boundary for (stone, ash, lava, void).
EDGE_DIRS = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]
_RING_OFFSET = {          # position of each direction inside the 3x3 ring
    "nw": (0, 0), "n": (1, 0), "ne": (2, 0),
    "w":  (0, 1),               "e":  (2, 1),
    "sw": (0, 2), "s": (1, 2), "se": (2, 2),
}


def ring_masks(sheet, ox, oy):
    """The eight ring cells' alpha channels, keyed by direction."""
    out = {}
    for d, (dx, dy) in _RING_OFFSET.items():
        out[d] = tile_at(sheet, ox + dx, oy + dy).getchannel("A")
    return out


def edge_tiles(fill, masks):
    """Stencil one fill tile through each ring mask."""
    out = {}
    for d, m in masks.items():
        cell = fill.copy()
        cell.putalpha(m)
        out[d] = cell
    return out



def build_terrain():
    spring = load("terrain_spring.png")
    summer = load("terrain_summer.png")
    autumn = load("terrain_autumn.png")
    winter = load("terrain_winter.png")
    ice_sh = load("terrain_winter_ice.png")
    cliff  = load("cliff_summer.png")
    soil   = load("tilled_soil.png")
    floor  = load("Tile_A.png")
    grit   = load("Gritty_Dirt.png")

    print("  picking interior fill tiles:")
    # Organic ground is harmonised gently — some tonal drift there reads as
    # patchy growth. Rock is harmonised hard, where drift reads as a grid.
    grass  = harmonise(pick_fill(spring, (92, 154, 42),   "grass"),  .55)
    forest = harmonise(pick_fill(summer, (70, 130, 50),   "forest"), .55)
    sand   = harmonise(pick_fill(summer, (244, 215, 160), "sand"),   .60)
    snow   = harmonise(pick_fill(winter, (224, 242, 243), "snow"),   .60)
    stone  = harmonise(pick_fill(floor, (150, 150, 155), "stone", spread=40))
    brick  = stone
    dirt   = harmonise(pick_fill(grit,  (150, 112, 70),  "dirt",  spread=44))
    pstone = brick
    water  = pick_fill(summer, (42, 133, 152),  "water")
    ice    = harmonise(pick_fill(ice_sh, (150, 205, 220), "ice", spread=26), .60)
    deep   = harmonise(pick_fill(summer, (23, 58, 85),    "deep"), .85)

    rows = {
        "grass": grass, "forest": forest, "sand": sand, "snow": snow,
        "stone": stone, "dirt": dirt, "pstone": pstone, "water": water, "ice": ice,
        # LPC Revised has no volcanic or void art, so those two are recoloured
        # from real tiles rather than drawn from nothing
        "ash":  [tint(t, (.52, .45, .48)) for t in stone],
        "void": [tint(t, (2.6, .70, 1.30), (18, 6, 26)) for t in deep],
        "lava": [tint(t, (5.4, 1.05, .22), (60, 0, 0)) for t in water],
    }

    sheet = Image.new("RGBA", (TILE * TVARIANTS, TILE * len(TERRAIN_ROWS)), (0, 0, 0, 0))
    for ri, name in enumerate(TERRAIN_ROWS):
        v = rows[name]
        for ci in range(TVARIANTS):
            sheet.paste(v[ci % len(v)], (ci * TILE, ri * TILE))
    sheet.save(os.path.join(OUT, "terrain.png"))
    print("terrain.png", sheet.size, "from LPC Revised terrain sheets")

    # --- the boundary atlas: 8 directions per terrain -----------------------
    # Organic ground borrows the grass ring; liquids and stone borrow the
    # softer soil ring, whose edge is less feathery and suits hard materials.
    organic = ring_masks(summer, 0, 0)
    soilish = ring_masks(soil, 0, 0)
    RING_FOR = {
        "grass": organic, "forest": organic, "snow": organic, "sand": organic,
        "dirt": soilish, "stone": soilish, "pstone": soilish, "ash": soilish,
        "void": soilish, "water": organic, "ice": organic, "lava": soilish,
    }
    edges = Image.new("RGBA", (TILE * len(EDGE_DIRS), TILE * len(TERRAIN_ROWS)), (0, 0, 0, 0))
    for ri, name in enumerate(TERRAIN_ROWS):
        cells = edge_tiles(rows[name][0], RING_FOR[name])
        for di, d in enumerate(EDGE_DIRS):
            edges.paste(cells[d], (di * TILE, ri * TILE))
    edges.save(os.path.join(OUT, "terrain_edges.png"))
    print("terrain_edges.png", edges.size,
          f"({len(EDGE_DIRS)} directions x {len(TERRAIN_ROWS)} terrains, "
          "stencilled through real LPC ring edges)")

    # guard the bug that made water look frozen: a terrain whose variants are
    # all the same tile has no visible shimmer, and liquids must actually move
    for name in TERRAIN_ROWS:
        v = rows[name]
        uniq = {t.tobytes() for t in v}
        if name in ("water", "lava") and len(uniq) < 2:
            print(f"    ! {name}: all {TVARIANTS} animation frames are identical "
                  f"— it will look frozen (handled at runtime by the ripple layer)")


# ============================================================== PROP ATLAS
# Props keep their own size and are drawn anchored at bottom-centre, so a
# 96x128 tree and a 24x20 flower can live in the same atlas.
def build_props():
    picks = []   # (name, PIL image, solid?)

    def take(sheet_name, label, count, solid, min_px=200, skip=0):
        sheet = load(sheet_name)
        cuts = cutouts(sheet, min_px=min_px)[skip:skip + count]
        for i, c in enumerate(cuts):
            picks.append((f"{label}{i}", c, solid))
        if not cuts:
            print(f"    ! no cutouts from {sheet_name}")

    # trees, one set per season so zones can look different       (block movement)
    take("trees_spring.png", "tree_spring", 3, True, min_px=900)
    take("trees_summer.png", "tree_summer", 3, True, min_px=900)
    take("trees_autumn.png", "tree_autumn", 3, True, min_px=900)
    take("trees_winter.png", "tree_winter", 3, True, min_px=900)
    # rocks and crags                                             (block movement)
    take("Rocks__Grasslands.png", "rock", 6, True, min_px=260)
    take("Rocks__Cliffs.png", "crag", 4, True, min_px=260)
    # ground cover                                                    (walkable)
    take("plants_summer.png", "plant", 6, False, min_px=150)
    take("plants_autumn.png", "plant_dry", 4, False, min_px=150)
    take("flowers.png", "flower", 6, False, min_px=90)
    take("mushrooms.png", "mushroom", 4, False, min_px=90)

    # ---- gameplay landmarks, cut from specific cells ----
    pillar = load("Stone_Pillar_A.png")          # 9 x 12 cells of 32px
    # a whole pillar is three stacked cells; take the top three of one column
    for i, col in enumerate((0, 3, 6)):
        shrine = pillar.crop((col * TILE, 0, (col + 1) * TILE, 3 * TILE))
        picks.append((f"shrine{i}", shrine, True))

    vases = load("Small_Flowers.png")            # 9 x 4 cells of 32px
    for i, col in enumerate((0, 1)):             # row 2 holds the glass vials
        picks.append((f"vial{i}", vases.crop((col * TILE, 2 * TILE, (col + 1) * TILE, 3 * TILE)), False))

    # ---- village: LPC ships whole buildings, so the huts are single cutouts
    def take_village(sheet_name, label, count, solid, min_px=200, skip=0):
        sheet = Image.open(os.path.join(SRC, "village", sheet_name)).convert("RGBA")
        cuts = cutouts(sheet, min_px=min_px)[skip:skip + count]
        for i, c in enumerate(cuts):
            picks.append((f"{label}{i}", c, solid))
        if not cuts:
            print(f"    ! no cutouts from village/{sheet_name}")

    take_village("Brick_House_A.png",   "house_a", 1, True, min_px=3000)
    take_village("Brick_House_B.png",   "house_b", 1, True, min_px=3000)
    take_village("Paneled_House_A.png", "house_c", 1, True, min_px=3000)
    take_village("Fountain_A.png",      "fountain", 1, True, min_px=600)
    # the fence sheet's first cutout is a full panel; the rest are posts
    take_village("Plain_Fence_A.png",   "fence", 1, True, min_px=1200)
    take_village("Lighting__Outdoors.png", "lamp", 2, True, min_px=250)
    take_village("Barrel.png",          "barrel", 3, True, min_px=250)
    take_village("Crate.png",           "crate", 2, True, min_px=250, skip=1)
    take_village("Sign_Backgrounds_A.png", "sign", 1, True, min_px=250)

    if not picks:
        sys.exit("no props extracted")

    pad = 2
    W = sum(p[1].width + pad for p in picks) + pad
    H = max(p[1].height for p in picks) + pad * 2
    atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    meta = []
    x = pad
    for name, im, solid in picks:
        y = H - pad - im.height          # bottom aligned in the strip
        atlas.paste(im, (x, y), im)
        meta.append({"n": name, "x": x, "y": y, "w": im.width, "h": im.height, "s": 1 if solid else 0})
        x += im.width + pad
    atlas.save(os.path.join(OUT, "props.png"))

    # a plain <script> beats fetch(): it also works from file://
    with open(os.path.join(OUT, "props.js"), "w") as f:
        f.write("window.LEXICORA_PROPS=" + json.dumps(meta, separators=(",", ":")) + ";\n")

    solid_n = sum(m["s"] for m in meta)
    print(f"props.png {atlas.size}  ({len(meta)} props: {solid_n} solid, {len(meta)-solid_n} decor)")
    print("props.js  metadata for the renderer")
    return meta




# ========================================================= CHARACTER SHEETS
# ULPC layers (assets/src/ulpc) share the classic 21-row layout, so rows 8-11
# are always the walk cycle: up, left, down, right, 9 frames each.
ULPC = os.path.join(ROOT, "assets", "src", "ulpc")
FRAME = 64
WALK_ROW = {"up": 8, "left": 9, "down": 10, "right": 11}
ENGINE_DIRS = ["down", "left", "right", "up"]      # matches DIRS in index.html
WALK_FRAMES = 9

CLASS_KITS = {
    # tier 0 -> 3, drawn back to front
    "hero": [
        ["body", "legs_pants", "feet_boots", "torso_leather", "head", "hair"],
        ["body", "legs_pants", "feet_boots", "torso_plate", "head", "hair", "wpn_sword"],
        ["body", "legs_plate", "feet_boots", "torso_plate", "head", "hair", "wpn_sword"],
        ["body", "legs_plate", "feet_boots", "torso_plate", "head", "hair", "wpn_sword"],
    ],
    "archer": [
        ["body", "legs_pants", "feet_boots", "torso_robe", "head", "hair"],
        ["body", "legs_pants", "feet_boots", "torso_leather", "head", "hair", "wpn_bow"],
        ["body", "legs_pants", "feet_boots", "torso_leather", "head", "hair", "wpn_bow"],
        ["body", "legs_plate", "feet_boots", "torso_leather", "head", "hair", "wpn_bow"],
    ],
    "mage": [
        ["body", "legs_leggings", "feet_boots", "torso_robe", "head", "hair"],
        ["body", "legs_leggings", "feet_boots", "torso_robe", "head", "hair", "wpn_staff"],
        ["body", "legs_leggings", "feet_boots", "torso_robe", "head", "hair", "wpn_staff"],
        ["body", "legs_leggings", "feet_boots", "torso_robe", "head", "hair", "wpn_staff"],
    ],
}


# ------------------------------------------------------------ battle sheets
# The duel used to be two static <img> tags shoved around with CSS. ULPC
# characters already carry proper attack and hurt animations, so the battle
# uses those instead: everything below is a straight cut from the same layers
# the overworld sprites come from. Rows are the standard 21-row layout, in
# up/left/down/right order per action.
BATTLE_ACTIONS = {          # engine name -> (ULPC row facing right, frames)
    "slash":     (15, 6),
    "shoot":     (19, 13),
    "spellcast": (3, 7),
    "walk":      (11, 9),
    "hurt":      (20, 6),
}
CLASS_ATTACK = {"hero": "slash", "archer": "shoot", "mage": "spellcast"}
BATTLE_ROWS = ["attack", "hurt", "idle"]
BATTLE_COLS = max(n for _, n in BATTLE_ACTIONS.values())


def _battle_sheet(compose, attack):
    """One sheet: attack, hurt and idle strips, each padded to BATTLE_COLS."""
    sheet = Image.new("RGBA", (FRAME * BATTLE_COLS, FRAME * len(BATTLE_ROWS)), (0, 0, 0, 0))
    for ri, action in enumerate((attack, "hurt", "walk")):
        row, frames = BATTLE_ACTIONS[action]
        for f in range(frames):
            sheet.paste(compose(row, f), (f * FRAME, ri * FRAME))
    return sheet


# The people who live in the hamlets, in the order the engine indexes them:
# sage, healer, scout.
VILLAGER_KITS = [
    ("sage",   ["body", "legs_leggings", "feet_boots", "torso_robe", "head", "hair_elder"]),
    ("healer", ["body_f", "legs_skirt", "feet_boots", "torso_robe_f", "head_f", "hair_f"]),
    ("scout",  ["body", "legs_pants", "feet_boots", "torso_vest", "head", "hair"]),
]


def build_characters():
    cache = {}

    def layer(name):
        if name not in cache:
            p = os.path.join(ULPC, name + ".png")
            if not os.path.exists(p):
                sys.exit(f"missing ULPC layer: {p}")
            cache[name] = Image.open(p).convert("RGBA")
        return cache[name]

    def stacked(stack):
        def compose(row, f):
            cell = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
            for lname in stack:
                src = layer(lname)
                if src.height < (row + 1) * FRAME:
                    continue
                cell = Image.alpha_composite(
                    cell, src.crop((f * FRAME, row * FRAME, (f + 1) * FRAME, (row + 1) * FRAME)))
            return cell
        return compose

    for cls, tiers in CLASS_KITS.items():
        for ti, stack in enumerate(tiers):
            _battle_sheet(stacked(stack), CLASS_ATTACK[cls]).save(
                os.path.join(OUT, f"battle_{cls}_s{ti}.png"))
        print(f"battle_{cls}_s0..3.png  {FRAME*BATTLE_COLS}x{FRAME*len(BATTLE_ROWS)} "
              f"({CLASS_ATTACK[cls]} / hurt / idle, from ULPC layers)")

    # Villagers share the pipeline: the same layers, different kits, so the
    # people you meet in a hamlet match the hero standing next to them.
    sheet = Image.new("RGBA",
                      (FRAME * WALK_FRAMES, FRAME * len(ENGINE_DIRS) * len(VILLAGER_KITS)),
                      (0, 0, 0, 0))
    for vi, (vname, stack) in enumerate(VILLAGER_KITS):
        compose = stacked(stack)
        for di, dname in enumerate(ENGINE_DIRS):
            for f in range(WALK_FRAMES):
                sheet.paste(compose(WALK_ROW[dname], f),
                            (f * FRAME, (vi * len(ENGINE_DIRS) + di) * FRAME))
    sheet.save(os.path.join(OUT, "villagers.png"))
    print(f"villagers.png  {sheet.size}  ({len(VILLAGER_KITS)} villagers x 4 directions)")

    for cls, tiers in CLASS_KITS.items():
        for ti, stack in enumerate(tiers):
            sheet = Image.new("RGBA", (FRAME * WALK_FRAMES, FRAME * len(ENGINE_DIRS)), (0, 0, 0, 0))
            for di, dname in enumerate(ENGINE_DIRS):
                row = WALK_ROW[dname]
                for f in range(WALK_FRAMES):
                    cell = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
                    for lname in stack:
                        src = layer(lname)
                        if src.height < (row + 1) * FRAME:
                            continue                       # layer lacks this row
                        piece = src.crop((f * FRAME, row * FRAME, (f + 1) * FRAME, (row + 1) * FRAME))
                        cell = Image.alpha_composite(cell, piece)
                    sheet.paste(cell, (f * FRAME, di * FRAME))
            sheet.save(os.path.join(OUT, f"player_{cls}_s{ti}.png"))
        print(f"player_{cls}_s0..3.png  {FRAME * WALK_FRAMES}x{FRAME * len(ENGINE_DIRS)} "
              f"({WALK_FRAMES} frames x 4 directions, from ULPC layers)")




# =========================================================== MONSTER SHEETS
# Monsters reuse the ULPC body variants (goblin-green child, orc muscular,
# skeleton, fur bodies...) plus a gear layer, so they match the player art.
MON_SRC = os.path.join(ULPC, "mon")
# (name, body, head, gear layers) — the head is its own ULPC layer, so a
# headless body is what you get if you forget it.
MONSTERS = [
    ("goblin",   "goblin.png",   "h_goblin.png",   ["torso_leather"]),
    ("orc",      "orc.png",      "h_orc.png",      ["torso_leather", "wpn_sword"]),
    ("skeleton", "skeleton.png", "h_skeleton.png", []),
    ("wolfkin",  "wolfkin.png",  "h_wolf.png",     []),
    ("troll",    "troll.png",    "h_troll.png",    ["legs_pants"]),
    ("imp",      "imp.png",      "h_imp.png",      []),
    ("raider",   "raider.png",   "h_human.png",    ["torso_leather", "legs_pants", "wpn_sword"]),
    ("wraith",   "wraith.png",   "h_wraith.png",   ["torso_robe"]),
    ("beast",    "beast.png",    "h_beast.png",    []),
]

BOSSES = [
    ("goblinking","goblin.png",   "h_goblin.png",   ["torso_plate", "wpn_sword"]),
    ("beastlord", "beast.png",    "h_beast.png",    ["torso_leather", "wpn_sword"]),
    ("raidchief", "raider.png",   "h_human.png",    ["torso_plate", "wpn_bow"]),
    ("bonelord",  "skeleton.png", "h_skeleton.png", ["wpn_sword"]),
    ("frostking", "troll.png",    "h_troll.png",    ["torso_plate", "legs_plate"]),
    ("warlord",   "orc.png",      "h_orc.png",      ["torso_plate", "legs_plate", "wpn_sword"]),
    ("packalpha", "wolfkin.png",  "h_wolf.png",     ["torso_leather", "wpn_sword"]),
    ("archmage",  "wraith.png",   "h_wraith.png",   ["torso_robe", "wpn_staff"]),
    ("implord",   "imp.png",      "h_imp.png",      ["torso_leather", "wpn_staff"]),
    ("darklord",  "orc.png",      "h_orc.png",      ["torso_plate", "legs_plate", "wpn_sword"]),
]


def _crop(path, row, frame):
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    if im.height < (row + 1) * FRAME:
        return None
    return im.crop((frame * FRAME, row * FRAME, (frame + 1) * FRAME, (row + 1) * FRAME))


def _mon_cell(body_file, head_file, gear, row, frame):
    base = _crop(os.path.join(MON_SRC, body_file), row, frame)
    if base is None:
        sys.exit(f"missing monster body: {body_file}")
    for layer_path in ([os.path.join(MON_SRC, head_file)] +
                       [os.path.join(ULPC, g + ".png") for g in gear]):
        piece = _crop(layer_path, row, frame)
        if piece is not None:
            base = Image.alpha_composite(base, piece)
    return base


def build_monsters():
    # Same layout as the player sheets: 9 walk frames across, four directions
    # down, so a monster faces where it is actually heading instead of always
    # staring at the camera through a two-frame bob.
    for out_name, roster in (("monsters.png", MONSTERS), ("bosses.png", BOSSES)):
        sheet = Image.new("RGBA",
                          (FRAME * WALK_FRAMES, FRAME * len(ENGINE_DIRS) * len(roster)),
                          (0, 0, 0, 0))
        for i, (name, body_file, head_file, gear) in enumerate(roster):
            for di, d in enumerate(ENGINE_DIRS):
                for f in range(WALK_FRAMES):
                    cell = _mon_cell(body_file, head_file, gear, WALK_ROW[d], f)
                    sheet.paste(cell, (f * FRAME, (i * len(ENGINE_DIRS) + di) * FRAME))
        sheet.save(os.path.join(OUT, out_name))
        print(f"{out_name}  {sheet.size}  ({len(roster)} kinds x 4 directions "
              f"x {WALK_FRAMES} frames from ULPC bodies)")

    # Battle sheets: the enemy stands on the right of the duel, so it needs the
    # left-facing variants — three rows below each right-facing row in ULPC.
    for out_name, roster in (("battle_mon.png", MONSTERS), ("battle_boss.png", BOSSES)):
        sheet = Image.new("RGBA",
                          (FRAME * BATTLE_COLS, FRAME * len(BATTLE_ROWS) * len(roster)),
                          (0, 0, 0, 0))
        for i, (name, body_file, head_file, gear) in enumerate(roster):
            def compose(row, f, b=body_file, h=head_file, g=gear):
                # row 20 (hurt) has a single direction; the action rows do not
                return _mon_cell(b, h, g, row if row == 20 else row - 2, f)
            sheet.paste(_battle_sheet(compose, "slash"),
                        (0, i * len(BATTLE_ROWS) * FRAME))
        sheet.save(os.path.join(OUT, out_name))
        print(f"{out_name}  {sheet.size}  ({len(roster)} kinds x "
              f"{len(BATTLE_ROWS)} rows, facing left)")




# ============================================================ ICONS AND FX
# Gear icons and battle projectiles are cut straight out of the ULPC gear
# layers. Those layers hold only the item on transparency, so trimming a
# single frame to its opaque bounds gives a clean icon with no redrawing.
ICON_CELL = 32
GEAR_ICON_SRC = [
    ("plate",   "torso_plate.png",   10, 0),   # (name, layer, walk-row, frame)
    ("leather", "torso_leather.png", 10, 0),
    ("boots",   "feet_boots.png",    10, 0),
    ("greaves", "legs_plate.png",    10, 0),
    ("sword",   "wpn_sword.png",     10, 0),
    ("staff",   "wpn_staff.png",     10, 0),
]


def _trim(im):
    box = im.getbbox()
    return im.crop(box) if box else im


def _fit(im, size):
    """Scale down to fit a square cell, keeping pixels crisp and centred."""
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if im.width == 0 or im.height == 0:
        return out
    scale = min(size / im.width, size / im.height, 1.0)
    w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    out.paste(im.resize((w, h), Image.NEAREST), ((size - w) // 2, (size - h) // 2))
    return out


def _layer_frame(layer_file, row, frame):
    p = os.path.join(ULPC, layer_file)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    if im.height < (row + 1) * FRAME:
        return None
    return im.crop((frame * FRAME, row * FRAME, (frame + 1) * FRAME, (row + 1) * FRAME))


def build_icons():
    sheet = Image.new("RGBA", (ICON_CELL * len(GEAR_ICON_SRC), ICON_CELL), (0, 0, 0, 0))
    for i, (name, layer_file, row, frame) in enumerate(GEAR_ICON_SRC):
        cell = _layer_frame(layer_file, row, frame)
        if cell is None:
            sys.exit(f"missing gear layer for icon: {layer_file}")
        sheet.paste(_fit(_trim(cell), ICON_CELL), (i * ICON_CELL, 0))
    sheet.save(os.path.join(OUT, "gear.png"))
    print(f"gear.png  {sheet.size}  ({len(GEAR_ICON_SRC)} icons cut from ULPC gear layers)")

    # battle projectiles: the class's own weapon, flying across the stage
    fx = {
        "slash": ("wpn_sword.png", 12, 3),   # slash row, mid swing
        "arrow": ("arrow.png",     17, 8),   # shoot row, arrow in flight
        "bolt":  ("wpn_staff.png",  2, 5),   # spellcast row, staff lit up
    }
    for name, (layer_file, row, frame) in fx.items():
        cell = _layer_frame(layer_file, row, frame)
        if cell is None or not cell.getbbox():
            cell = _layer_frame(layer_file, 10, 0)
        if cell is None:
            sys.exit(f"missing fx layer: {layer_file}")
        strip = Image.new("RGBA", (ICON_CELL * 4, ICON_CELL), (0, 0, 0, 0))
        base = _fit(_trim(cell), ICON_CELL)
        for f in range(4):                       # a simple 4-step fade-in trail
            frame_img = base.copy()
            alpha = frame_img.getchannel("A").point(lambda a, f=f: int(a * (0.55 + 0.15 * f)))
            frame_img.putalpha(alpha)
            strip.paste(frame_img, (f * ICON_CELL, 0))
        strip.save(os.path.join(OUT, f"fx_{name}.png"))
    print("fx_slash / fx_arrow / fx_bolt.png  cut from ULPC weapon layers")


# ------------------------------------------------------------- liquid motion
# The terrain atlas cannot animate water: the LPC water cells we sample are
# near-identical, so cycling them shows nothing. Eliza Wyatt's FX sheets carry
# the real surface animation instead - caustic sparkles that tile seamlessly,
# a foot ripple and a splash - so the liquids get their movement from those.
FXSRC = os.path.join(SRC, "fx")


def _fx(name):
    return Image.open(os.path.join(FXSRC, name)).convert("RGBA")


def ember(im):
    """Recolour a water caustic into lava ember light, keeping its shape."""
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = (r * 0.30 + g * 0.59 + b * 0.11) / 255.0
            px[x, y] = (255,
                        int(60 + 150 * lum),
                        int(20 * lum),
                        a)
    return out


def build_water_fx():
    refl = _fx("Water_Reflections.png")     # 4 frames x 3 rows of 32px
    ripple = _fx("WaterRipple.png")         # 4 frames, foot ripple
    splash = _fx("Splash.png")              # 6 frames of 64x32

    dense = [tile_at(refl, f, 0) for f in range(4)]
    sparse = [tile_at(refl, f, 1) for f in range(4)]
    drops = [tile_at(refl, f, 2) for f in range(4)]
    feet = [tile_at(ripple, f, 0) for f in range(4)]

    rows = [dense, sparse,
            [ember(c) for c in dense], [ember(c) for c in sparse],
            drops, feet]
    sheet = Image.new("RGBA", (TILE * 4, TILE * len(rows)), (0, 0, 0, 0))
    for ri, row in enumerate(rows):
        for f, cell in enumerate(row):
            sheet.paste(cell, (f * TILE, ri * TILE))
    sheet.save(os.path.join(OUT, "water_fx.png"))

    # The caustics must differ frame to frame or the surface reads as frozen -
    # the exact failure the terrain atlas had. Check it rather than assume it.
    for label, row in (("caustic-dense", dense), ("caustic-sparse", sparse)):
        deltas = []
        for f in range(4):
            a, b = row[f], row[(f + 1) % 4]
            deltas.append(sum(abs(p - q) for p, q in
                              zip(a.tobytes(), b.tobytes())) / (TILE * TILE * 4))
        worst = min(deltas)
        flag = "" if worst > 1.0 else "   << TOO STATIC"
        print(f"    {label} frame deltas "
              f"{[round(d, 2) for d in deltas]}{flag}")

    strip = Image.new("RGBA", (64 * 6, 32), (0, 0, 0, 0))
    for f in range(6):
        strip.paste(splash.crop((f * 64, 0, f * 64 + 64, 32)), (f * 64, 0))
    strip.save(os.path.join(OUT, "splash.png"))
    print("water_fx.png (6 rows x 4) + splash.png (6 frames) <- LPC FX sheets")

    # The campfire ships as an unlit pile on row 0 and four burning frames on
    # row 1; the village only ever wants the fire.
    camp = Image.open(os.path.join(SRC, "village", "Fire__Camp.png")).convert("RGBA")
    fire = Image.new("RGBA", (TILE * 4, TILE), (0, 0, 0, 0))
    for f in range(4):
        fire.paste(tile_at(camp, f, 1), (f * TILE, 0))
    fire.save(os.path.join(OUT, "campfire.png"))
    print("campfire.png (4 frames) <- LPC Objects/Small Items/Fire, Camp")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_terrain()
    build_water_fx()
    build_props()
    build_characters()
    build_monsters()
    build_icons()
    print("done ->", OUT)
