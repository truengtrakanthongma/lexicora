# Art credits

Every sprite, tile and prop in Lexicora comes from the **Liberated Pixel Cup
(LPC)** family of open game art. Nothing is drawn by hand for this project —
`scripts/build_assets.py` only crops, layers and packs the original sheets into
the atlases the game loads. The unmodified source art it reads from is kept in
`assets/src/` so the build is reproducible and the originals stay available.

Attribution below is required by the licences. Please keep this file with the
game if you redistribute it.

---

## Terrain, trees, plants and props

**LPC Revised** — <https://github.com/ElizaWy/LPC>
Licence: **CC-BY 3.0 / OGA-BY 3.0** (attribution required, no share-alike)

| Used for | Source files |
|---|---|
| Grass, forest floor, sand, snow fills | `terrain_spring/summer/autumn/winter.png` |
| Ice | `terrain_winter_ice.png` |
| Stone floor, bridges | `Structure/Floor/Tile A.png` |
| Dirt roads | `Structure/Floor/Gritty Dirt.png` |
| Trees (four seasons) | `trees_spring/summer/autumn/winter.png` |
| Rocks and crags | `Rocks, Grasslands.png`, `Rocks, Cliffs.png` |
| Grass tufts, flowers, mushrooms | `plants_summer/autumn.png`, `flowers.png`, `mushrooms.png` |
| Shrines (stone pillars) | `Structure/Pillars/Stone Pillar A.png` |
| Word vials | `Objects/Small Items/Flowers.png` |
| Water and lava surface caustics, raindrop rings | `FX/Water Reflections.png` |
| Ripple around feet in water | `FX/WaterRipple.png` |
| Splash | `FX/Splash.png` |

The four water FX sheets are by **Eliza Wyatt (DeathsDarling)** under
**OGA-BY 3.0** (`assets/src/lpc/fx/Credits.txt`). The lava surface uses the
same caustics recoloured to ember light.

Artists credited in the upstream per-folder `Credits.txt` (copied to
`assets/src/lpc/Credits.txt`) include **Eliza Wyatt (DeathsDarling)**,
**Lanea Zimmerman (Sharm)** and **Hyptosis**.

The volcanic, ash and void tiles have no LPC equivalent, so they are recolours
of real LPC tiles (stone, dirt and deep water) — still derivative works of the
art above and credited the same way.

---

## Characters and monsters

**Universal LPC Spritesheet Character Generator** —
<https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator>
Licence: **CC-BY-SA 3.0 and/or GPL 3.0 / OGA-BY 3.0**, varying per layer.
The full per-file table is copied to `assets/src/ulpc/CREDITS-ULPC.csv`, and the
upstream licence text to `assets/src/ulpc/LICENSE.txt`.

Because several character layers are **CC-BY-SA 3.0**, the composited character
and monster sheets in `assets/player_*.png`, `assets/monsters.png` and
`assets/bosses.png` are likewise released under **CC-BY-SA 3.0**.

Layers used, with the authors listed upstream:

| Layer | Authors |
|---|---|
| Base bodies (male, child, muscular, skeleton) | bluecarrot16, Benjamin K. Smith (BenCreating), ElizaWy, MuffinElZangano, Evert, TheraHedwig, Durrani, Sander Frenken, Johannes Sjölund (wulax), Stephen Challener (Redshrike) |
| Human head, hair | Stephen Challener (Redshrike), Manuel Riecke (MrBeast) |
| Goblin / orc / skeleton / wolf / troll / vampire / minotaur heads | bluecarrot16, Stephen Challener (Redshrike), Nila122, kheftel, Matthew Krohn (makrohn), Marcel van de Steeg (MadMarcel), AntumDeluge, Tuomo Untinen (reemax), Evert, Daniel Eddeland (daneeklu), Sander Frenken (castelonia), Benjamin K. Smith (BenCreating) |
| Plate armour and plate legs | bluecarrot16, Michael Whitlock (bigbeargames), Matthew Krohn (makrohn) |
| Leather armour | Johannes Sjölund (wulax), adapted by bluecarrot16 |
| Laced longsleeve (mage robe) | bluecarrot16, JaidynReiman, Johannes Sjölund (wulax) |
| Pants, leggings, boots | ElizaWy, JaidynReiman, dalonedrau, Stephen Challener (Redshrike), bluecarrot16 |
| Arming sword | ElizaWy; walk and down frames by JaidynReiman |
| Recurve bow | Daniel Eddeland (daneeklu), gr3yh47, Johannes Sjölund (wulax), Pierre |
| Gnarled staff | bluecarrot16 |

---

## Everything else

Fonts **Cinzel** and **Kanit** are served from Google Fonts under the
SIL Open Font License 1.1.

Game code, level design, grammar lessons and vocabulary are original work for
this project.
