"""Procedurally generate pixel-art sprites for Lexicora Adventure.
Small native resolution, meant to be displayed scaled up with
image-rendering: pixelated in the browser."""
from PIL import Image, ImageDraw
import os

OUT = "/home/user/my-tense-game/assets"
os.makedirs(f"{OUT}/sprites", exist_ok=True)
os.makedirs(f"{OUT}/icons", exist_ok=True)
os.makedirs(f"{OUT}/fx", exist_ok=True)

# ---------------------------------------------------------------- palette
K   = (26,22,34,255)      # outline
SK  = (232,177,140,255)   # skin
SKd = (196,140,104,255)
HR  = (92,58,33,255)      # hair
HRd = (61,38,20,255)
CL  = (61,90,128,255)     # tunic blue
CLd = (41,67,92,255)
PN  = (90,66,44,255)      # pants
PNd = (61,44,28,255)
BT  = (74,50,32,255)      # boots
BTd = (48,32,20,255)
ST  = (201,214,223,255)   # steel light
STd = (140,151,161,255)
STh = (240,244,247,255)   # steel highlight
GD  = (244,196,48,255)    # gold
GDd = (188,140,28,255)
RD  = (214,69,80,255)
RDd = (156,46,57,255)
GR  = (76,154,91,255)     # green
GRd = (47,107,58,255)
WD  = (122,82,48,255)     # wood
WDd = (77,51,25,255)
PU  = (150,110,240,255)   # purple / arcane
PUd = (95,64,168,255)
WH  = (255,255,255,255)
EM  = (255,120,60,255)    # ember
EMd = (196,68,20,255)
ICE = (172,224,226,255)
ICEd= (98,163,186,255)
VO  = (58,36,92,255)      # void
VOd = (34,20,56,255)
STN = (120,126,138,255)   # stone
STNd= (74,80,92,255)
TAN = (196,168,124,255)
TANd= (150,120,80,255)
TRANS = (0,0,0,0)

def new_img(w,h):
    return Image.new("RGBA", (w,h), TRANS)

def px(d, x, y, color, w=1, h=1):
    if color is None: return
    d.rectangle([x, y, x+w-1, y+h-1], fill=color)

def save(img, path, scale=8):
    big = img.resize((img.width*scale, img.height*scale), Image.NEAREST)
    big.save(path)
    print("saved", path, big.size)

# ================================================================ HERO
HW, HH = 20, 26

def draw_hero(gear):
    """gear: set of {'helmet','armor','boots','gauntlet','weapon','ring'}"""
    img = new_img(HW, HH)
    d = ImageDraw.Draw(img)

    # legs / pants
    px(d, 7, 18, PN, 2, 5); px(d, 7, 18, PNd, 1, 5)
    px(d, 11, 18, PN, 2, 5); px(d, 12, 18, PNd, 1, 5)
    # boots (base leather, replaced by steel if 'boots' gear)
    bc, bcd = (BT, BTd) if 'boots' not in gear else (ST, STd)
    px(d, 6, 22, bc, 3, 3); px(d, 6, 22, bcd, 1, 3)
    px(d, 11, 22, bc, 3, 3); px(d, 13, 22, bcd, 1, 3)
    if 'boots' in gear:
        px(d, 6, 22, GD, 3, 1); px(d, 11, 22, GD, 3, 1)

    # arms (sleeves)
    sleeve = CL if 'armor' not in gear else ST
    sleeved = CLd if 'armor' not in gear else STd
    px(d, 3, 11, sleeve, 3, 5); px(d, 3, 11, sleeved, 1, 5)
    px(d, 14, 11, sleeve, 3, 5); px(d, 16, 11, sleeved, 1, 5)
    # hands
    px(d, 3, 16, SK, 3, 2)
    px(d, 14, 16, SK, 3, 2)

    # torso / tunic (or armor chestplate)
    if 'armor' in gear:
        px(d, 6, 10, ST, 8, 8)
        px(d, 6, 10, STh, 8, 1)
        px(d, 6, 17, STd, 8, 1)
        px(d, 9, 11, GD, 2, 6)  # gold trim center
    else:
        px(d, 6, 10, CL, 8, 8)
        px(d, 6, 10, CLd, 1, 8)
        px(d, 6, 16, GD, 8, 1)  # belt

    # neck
    px(d, 8, 8, SK, 4, 2)

    # head
    px(d, 6, 2, SK, 8, 7)
    px(d, 6, 2, SKd, 1, 7)
    # eyes
    px(d, 8, 5, K, 1, 1)
    px(d, 12, 5, K, 1, 1)
    # hair (unless helmet covers it)
    if 'helmet' not in gear:
        px(d, 5, 0, HR, 10, 3)
        px(d, 5, 3, HR, 2, 2)
        px(d, 13, 3, HR, 2, 2)
        px(d, 5, 0, HRd, 10, 1)
    else:
        px(d, 5, 0, ST, 10, 4)
        px(d, 5, 0, STh, 10, 1)
        px(d, 5, 3, STd, 10, 1)
        px(d, 8, 3, GD, 4, 1)  # helmet band
        px(d, 9, 4, K, 2, 1)   # visor slit

    # gauntlet overlay on hands
    if 'gauntlet' in gear:
        px(d, 3, 16, ST, 3, 2); px(d, 3, 16, STh, 3, 1)
        px(d, 14, 16, ST, 3, 2); px(d, 14, 16, STh, 3, 1)

    # weapon (sword) held in right hand
    if 'weapon' in gear:
        px(d, 17, 6, ST, 1, 11)   # blade
        px(d, 17, 5, STh, 1, 1)
        px(d, 16, 16, GDd, 3, 1)  # crossguard
        px(d, 17, 17, WD, 1, 2)   # hilt

    # ring aura glow near hand
    if 'ring' in gear:
        px(d, 3, 15, GD, 1, 1)
        px(d, 15, 15, GD, 1, 1)
        px(d, 2, 14, PU, 1, 6)
        px(d, 18, 14, PU, 1, 6)

    return img

TIERS = [
    ("hero_tier0", set()),
    ("hero_tier1", {"helmet"}),
    ("hero_tier2", {"helmet","armor"}),
    ("hero_tier3", {"helmet","armor","boots"}),
    ("hero_tier4", {"helmet","armor","boots","gauntlet"}),
    ("hero_tier5", {"helmet","armor","boots","gauntlet","weapon"}),
    ("hero_tier6", {"helmet","armor","boots","gauntlet","weapon","ring"}),
]
for name, gear in TIERS:
    save(draw_hero(gear), f"{OUT}/sprites/{name}.png", scale=8)

# ================================================================ BOSSES
BW, BH = 32, 32

def boss_canvas():
    return new_img(BW, BH), None

def boss_forest_golem():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 9, 6, GRd, 14, 4)          # shoulders/moss cap
    px(d, 10, 4, GR, 12, 4)          # head block
    px(d, 12, 8, K, 2, 2); px(d, 18, 8, K, 2, 2)  # eyes glow
    px(d, 12, 8, (255,255,180,255), 1, 1); px(d, 18, 8, (255,255,180,255), 1, 1)
    px(d, 7, 12, STN, 18, 12)        # big stone torso
    px(d, 7, 12, STNd, 2, 12)
    px(d, 9, 15, GR, 4, 3); px(d, 19, 17, GR, 5, 3)  # moss patches
    px(d, 3, 13, STN, 4, 9); px(d, 25, 13, STN, 4, 9) # arms
    px(d, 3, 21, STNd, 4, 2); px(d, 25, 21, STNd, 4, 2) # fists
    px(d, 9, 24, STN, 6, 6); px(d, 17, 24, STN, 6, 6)  # legs
    return img

def boss_sand_kobold():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 10, 10, TAN, 12, 8)          # head
    px(d, 6, 12, TANd, 4, 3); px(d, 22, 12, TANd, 4, 3)  # big ears
    px(d, 13, 14, K, 2, 2); px(d, 18, 14, K, 2, 2)
    px(d, 13, 14, RD, 1, 1); px(d, 18, 14, RD, 1, 1)
    px(d, 14, 17, K, 4, 1)             # mouth
    px(d, 15, 17, WH, 1, 2); px(d, 17, 17, WH, 1, 2)  # fangs
    px(d, 9, 18, TANd, 14, 10)         # robe body
    px(d, 9, 18, GRd, 2, 10)
    px(d, 22, 16, STd, 1, 8); px(d, 21, 15, ST, 2, 2)  # dagger
    px(d, 11, 28, TANd, 4, 4); px(d, 17, 28, TANd, 4, 4)  # feet
    return img

def boss_frost_wolf():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 8, 6, ICEd, 4, 4); px(d, 20, 6, ICEd, 4, 4)   # ears
    px(d, 9, 8, ICE, 14, 9)             # head/muzzle block
    px(d, 11, 11, (140,220,255,255), 2, 2); px(d, 19, 11, (140,220,255,255), 2, 2)  # glow eyes
    px(d, 13, 15, ICEd, 6, 2)           # snout shade
    px(d, 6, 17, ICE, 20, 9)            # chest/mane
    px(d, 6, 17, WH, 20, 2)
    px(d, 4, 19, ICEd, 4, 6); px(d, 24, 19, ICEd, 4, 6) # side fur tufts
    px(d, 9, 26, ICEd, 5, 4); px(d, 18, 26, ICEd, 5, 4) # legs
    return img

def boss_tide_serpent():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 11, 4, GR, 10, 8)             # head
    px(d, 13, 7, K, 2, 2); px(d, 17, 7, K, 2, 2)
    px(d, 13, 7, (200,255,220,255), 1, 1); px(d, 17, 7, (200,255,220,255), 1, 1)
    px(d, 9, 3, GRd, 3, 3); px(d, 20, 3, GRd, 3, 3)   # fin crest
    px(d, 8, 12, GRd, 16, 6)            # neck coil
    px(d, 6, 18, GR, 20, 8)             # body coil
    px(d, 6, 18, (140,220,190,255), 20, 2)
    px(d, 9, 26, GRd, 14, 4)            # tail curl
    return img

def boss_ember_golem():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 9, 5, STN, 14, 6)             # head
    px(d, 12, 8, EM, 2, 2); px(d, 18, 8, EM, 2, 2)  # glow eyes
    px(d, 7, 11, STNd, 18, 13)          # torso
    px(d, 9, 13, EM, 2, 6); px(d, 21, 13, EM, 2, 6) # lava cracks
    px(d, 14, 16, EM, 4, 2)
    px(d, 3, 12, STN, 4, 10); px(d, 25, 12, STN, 4, 10)  # arms
    px(d, 3, 20, EM, 4, 2); px(d, 25, 20, EM, 4, 2)      # molten fists
    px(d, 9, 24, STN, 6, 7); px(d, 17, 24, STN, 6, 7)
    px(d, 10, 28, EM, 4, 2); px(d, 18, 28, EM, 4, 2)     # cracked feet
    return img

def boss_void_wraith():
    img = new_img(BW, BH); d = ImageDraw.Draw(img)
    px(d, 9, 4, VOd, 14, 8)             # hood
    px(d, 10, 6, VO, 12, 5)
    px(d, 13, 9, (200,160,255,255), 2, 2); px(d, 17, 9, (200,160,255,255), 2, 2)
    px(d, 6, 12, VO, 20, 14)            # robe body (fades)
    px(d, 6, 12, PU, 20, 2)
    for i,(x,w) in enumerate([(6,4),(12,3),(17,3),(22,4)]):
        px(d, x, 24+ (i%2), VOd, w, 4)  # tattered hem wisps
    px(d, 10, 10, WH, 1, 1); px(d, 22, 14, WH, 1, 1); px(d, 8, 20, WH, 1, 1)  # stars
    return img

BOSSES = {
    "boss_whisper_woods": boss_forest_golem,
    "boss_sandstone_ruins": boss_sand_kobold,
    "boss_frostpeak_pass": boss_frost_wolf,
    "boss_tidecaller_bay": boss_tide_serpent,
    "boss_ember_citadel": boss_ember_golem,
    "boss_nebula_spire": boss_void_wraith,
}
for name, fn in BOSSES.items():
    save(fn(), f"{OUT}/sprites/{name}.png", scale=6)

# ================================================================ GEAR ICONS
IW, IH = 16, 16

def icon_helmet():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    px(d, 3, 6, ST, 10, 6); px(d, 3, 6, STh, 10, 1)
    px(d, 4, 12, STd, 8, 2)
    px(d, 7, 8, GD, 2, 3)
    px(d, 3, 4, ST, 10, 3)
    return img

def icon_armor():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    px(d, 4, 2, ST, 8, 3)
    px(d, 3, 5, ST, 10, 8); px(d, 3, 5, STh, 10, 1)
    px(d, 7, 6, GD, 2, 7)
    px(d, 2, 6, STd, 2, 6); px(d, 12, 6, STd, 2, 6)
    return img

def icon_boots():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    px(d, 4, 2, BT, 4, 8)
    px(d, 3, 10, BT, 7, 4); px(d, 3, 10, BTd, 7, 1)
    px(d, 2, 13, K, 8, 1)
    px(d, 4, 4, GD, 4, 1)
    return img

def icon_gauntlet():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    px(d, 5, 2, ST, 6, 6); px(d, 5, 2, STh, 6, 1)
    px(d, 4, 8, ST, 8, 5)
    px(d, 4, 8, GD, 8, 1)
    px(d, 3, 12, SK, 10, 2)
    return img

def icon_weapon():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    px(d, 7, 1, ST, 2, 9); px(d, 7, 1, STh, 1, 9)
    px(d, 4, 10, GDd, 8, 2)
    px(d, 6, 12, WD, 4, 3)
    return img

def icon_ring():
    img = new_img(IW, IH); d = ImageDraw.Draw(img)
    d.ellipse([3,6,12,15], outline=GD, width=2)
    px(d, 6, 3, PU, 4, 4)
    px(d, 7, 4, WH, 2, 1)
    return img

ICONS = {
    "gear_helmet": icon_helmet, "gear_armor": icon_armor, "gear_boots": icon_boots,
    "gear_gauntlet": icon_gauntlet, "gear_weapon": icon_weapon, "gear_ring": icon_ring,
}
for name, fn in ICONS.items():
    save(fn(), f"{OUT}/icons/{name}.png", scale=8)

# ================================================================ SPELL FX (4-frame strips)
FW, FH = 20, 20

def fx_strip(frame_fn, n=4):
    sheet = new_img(FW*n, FH)
    for i in range(n):
        frame = new_img(FW, FH)
        d = ImageDraw.Draw(frame)
        frame_fn(d, i)
        sheet.paste(frame, (i*FW, 0), frame)
    return sheet

def fireball_frame(d, i):
    r = 3 + i*2
    cx, cy = FW//2, FH//2
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=EM)
    d.ellipse([cx-r+2, cy-r+2, cx+r-2, cy+r-2], fill=(255,220,140,255))
    if i >= 2:
        px(d, cx-r-2, cy-1, EM, 2, 2); px(d, cx+r, cy-1, EM, 2, 2)

def frostnova_frame(d, i):
    r = 2 + i*3
    cx, cy = FW//2, FH//2
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=ICE, width=2)
    if i>0:
        d.ellipse([cx-r+2, cy-r+2, cx+r-2, cy+r-2], outline=WH, width=1)

def divineheal_frame(d, i):
    cx, cy = FW//2, FH-2-i*4
    px(d, cx-1, cy-4, GD, 2, 8)
    px(d, cx-4, cy-1, GD, 8, 2)
    d.ellipse([cx-2,cy-2,cx+2,cy+2], fill=(255,255,220,255))

def lightning_frame(d, i):
    pts_variants = [
        [(10,0),(7,7),(11,7),(6,16)],
        [(10,0),(13,6),(9,6),(12,16)],
        [(10,0),(6,8),(12,8),(8,16)],
        [(10,0),(14,5),(8,10),(11,16)],
    ]
    pts = pts_variants[i % len(pts_variants)]
    d.line(pts, fill=PU, width=2)
    d.line(pts, fill=WH, width=1)

FX = {
    "fx_fireball": fireball_frame, "fx_frostnova": frostnova_frame,
    "fx_divineheal": divineheal_frame, "fx_lightning": lightning_frame,
}
for name, fn in FX.items():
    save(fx_strip(fn), f"{OUT}/fx/{name}.png", scale=6)

print("DONE")
