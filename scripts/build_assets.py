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
    grass  = pick_fill(spring, (92, 154, 42),   "grass")
    forest = pick_fill(summer, (70, 130, 50),   "forest")
    sand   = pick_fill(summer, (244, 215, 160), "sand")
    snow   = pick_fill(winter, (224, 242, 243), "snow")
    stone  = pick_fill(floor,  (150, 150, 155), "stone", spread=40)
    brick  = stone
    dirt   = pick_fill(grit,   (150, 112, 70),  "dirt",  spread=44)
    pstone = brick
    water  = pick_fill(summer, (42, 133, 152),  "water")
    ice    = pick_fill(ice_sh, (150, 205, 220), "ice",   spread=26)
    deep   = pick_fill(summer, (23, 58, 85),    "deep")

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


def build_characters():
    cache = {}

    def layer(name):
        if name not in cache:
            p = os.path.join(ULPC, name + ".png")
            if not os.path.exists(p):
                sys.exit(f"missing ULPC layer: {p}")
            cache[name] = Image.open(p).convert("RGBA")
        return cache[name]

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
MON_FRAMES = 2          # a two-frame idle bob, taken from the walk cycle
MON_ROW = WALK_ROW["down"]

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


def _crop(path, frame):
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    if im.height < (MON_ROW + 1) * FRAME:
        return None
    return im.crop((frame * FRAME, MON_ROW * FRAME, (frame + 1) * FRAME, (MON_ROW + 1) * FRAME))


def _mon_cell(body_file, head_file, gear, frame):
    base = _crop(os.path.join(MON_SRC, body_file), frame)
    if base is None:
        sys.exit(f"missing monster body: {body_file}")
    for layer_path in ([os.path.join(MON_SRC, head_file)] +
                       [os.path.join(ULPC, g + ".png") for g in gear]):
        piece = _crop(layer_path, frame)
        if piece is not None:
            base = Image.alpha_composite(base, piece)
    return base


def build_monsters():
    for out_name, roster in (("monsters.png", MONSTERS), ("bosses.png", BOSSES)):
        sheet = Image.new("RGBA", (FRAME * MON_FRAMES, FRAME * len(roster)), (0, 0, 0, 0))
        for i, (name, body_file, head_file, gear) in enumerate(roster):
            for f in range(MON_FRAMES):
                # walk frames 0 and 4 read as a gentle idle sway
                cell = _mon_cell(body_file, head_file, gear, 0 if f == 0 else 4)
                sheet.paste(cell, (f * FRAME, i * FRAME))
        sheet.save(os.path.join(OUT, out_name))
        print(f"{out_name}  {sheet.size}  ({len(roster)} kinds from ULPC bodies)")




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


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_terrain()
    build_props()
    build_characters()
    build_monsters()
    build_icons()
    print("done ->", OUT)
