#!/usr/bin/env bash
# Re-download the upstream LPC art that assets/src/ is built from.
#
# The repo already vendors everything scripts/build_assets.py needs, so you
# only need this when you want to pull a newer upstream revision or add a
# layer that isn't vendored yet.
#
# Usage:  bash scripts/fetch_assets.sh [workdir]
set -euo pipefail

WORK="${1:-/tmp/lexicora-art}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LPC="$WORK/lpc-revised"      # ElizaWy/LPC          - terrain, props   (CC-BY 3.0 / OGA-BY 3.0)
ULPC="$WORK/ulpc"            # sanderfrenken/ULPC   - characters       (CC-BY-SA 3.0 / GPL 3.0)

mkdir -p "$WORK" "$ROOT/assets/src/lpc" "$ROOT/assets/src/ulpc/mon"

clone() {   # blobless clone: the trees are huge, we only want a few files
  local url="$1" dir="$2"
  [ -d "$dir/.git" ] && return 0
  echo "cloning $url"
  git clone --depth 1 --filter=blob:none --no-checkout "$url" "$dir"
}

grab() {    # grab REPO_DIR SRC_PATH DEST_PATH
  local dir="$1" src="$2" dst="$3"
  if ( cd "$dir" && git show "HEAD:$src" ) > "$dst" 2>/dev/null && [ -s "$dst" ]; then
    echo "  ok   $(basename "$dst")"
  else
    echo "  MISS $src" >&2
    rm -f "$dst"
  fi
}

clone https://github.com/ElizaWy/LPC "$LPC"
clone https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator "$ULPC"

echo "terrain + props (LPC Revised)"
for f in terrain_spring terrain_summer terrain_autumn terrain_winter terrain_winter_ice \
         trees_spring trees_summer trees_autumn trees_winter \
         plants_summer plants_autumn flowers mushrooms cliff_summer cliff_winter tilled_soil; do
  grab "$LPC" "Terrain/$f.png" "$ROOT/assets/src/lpc/$f.png"
done
grab "$LPC" "Terrain/Rocks, Grasslands.png"        "$ROOT/assets/src/lpc/Rocks__Grasslands.png"
grab "$LPC" "Terrain/Rocks, Cliffs.png"            "$ROOT/assets/src/lpc/Rocks__Cliffs.png"
grab "$LPC" "Terrain/Credits.txt"                  "$ROOT/assets/src/lpc/Credits.txt"
grab "$LPC" "Structure/Floor/Tile A.png"           "$ROOT/assets/src/lpc/Tile_A.png"
grab "$LPC" "Structure/Floor/Gritty Dirt.png"      "$ROOT/assets/src/lpc/Gritty_Dirt.png"
grab "$LPC" "Structure/Pillars/Stone Pillar A.png" "$ROOT/assets/src/lpc/Stone_Pillar_A.png"
grab "$LPC" "Objects/Small Items/Flowers.png"      "$ROOT/assets/src/lpc/Small_Flowers.png"
grab "$LPC" "README.md"                            "$ROOT/assets/src/lpc/README-LPC-Revised.md"

echo "character layers (ULPC)"
grab "$ULPC" "spritesheets/body/bodies/male/light.png"                  "$ROOT/assets/src/ulpc/body.png"
grab "$ULPC" "spritesheets/head/heads/human/male/light.png"             "$ROOT/assets/src/ulpc/head.png"
grab "$ULPC" "spritesheets/hair/messy1/male/chestnut.png"               "$ROOT/assets/src/ulpc/hair.png"
grab "$ULPC" "spritesheets/torso/armour/plate/male/steel.png"           "$ROOT/assets/src/ulpc/torso_plate.png"
grab "$ULPC" "spritesheets/torso/armour/leather/male/brown.png"         "$ROOT/assets/src/ulpc/torso_leather.png"
grab "$ULPC" "spritesheets/torso/clothes/longsleeve/laced/male/blue.png" "$ROOT/assets/src/ulpc/torso_robe.png"
grab "$ULPC" "spritesheets/legs/armour/plate/male/steel.png"            "$ROOT/assets/src/ulpc/legs_plate.png"
grab "$ULPC" "spritesheets/legs/pants/male/forest.png"                  "$ROOT/assets/src/ulpc/legs_pants.png"
grab "$ULPC" "spritesheets/legs/leggings/male/navy.png"                 "$ROOT/assets/src/ulpc/legs_leggings.png"
grab "$ULPC" "spritesheets/feet/boots/male/brown.png"                   "$ROOT/assets/src/ulpc/feet_boots.png"
grab "$ULPC" "spritesheets/weapon/sword/arming/universal/fg.png"        "$ROOT/assets/src/ulpc/wpn_sword.png"
grab "$ULPC" "spritesheets/weapon/ranged/bow/recurve/universal/foreground.png" "$ROOT/assets/src/ulpc/wpn_bow.png"
grab "$ULPC" "spritesheets/weapon/magic/gnarled/universal/foreground.png"      "$ROOT/assets/src/ulpc/wpn_staff.png"
grab "$ULPC" "CREDITS.csv"                                             "$ROOT/assets/src/ulpc/CREDITS-ULPC.csv"
grab "$ULPC" "LICENSE"                                                 "$ROOT/assets/src/ulpc/LICENSE.txt"

echo "monster bodies + heads (ULPC)"
M="$ROOT/assets/src/ulpc/mon"
grab "$ULPC" "spritesheets/body/bodies/child/bright_green.png"     "$M/goblin.png"
grab "$ULPC" "spritesheets/body/bodies/muscular/dark_green.png"    "$M/orc.png"
grab "$ULPC" "spritesheets/body/bodies/skeleton/skeleton.png"      "$M/skeleton.png"
grab "$ULPC" "spritesheets/body/bodies/muscular/fur_grey.png"      "$M/wolfkin.png"
grab "$ULPC" "spritesheets/body/bodies/muscular/blue.png"          "$M/troll.png"
grab "$ULPC" "spritesheets/body/bodies/child/amber.png"            "$M/imp.png"
grab "$ULPC" "spritesheets/body/bodies/male/olive.png"             "$M/raider.png"
grab "$ULPC" "spritesheets/body/bodies/muscular/lavender.png"      "$M/wraith.png"
grab "$ULPC" "spritesheets/body/bodies/muscular/fur_black.png"     "$M/beast.png"
grab "$ULPC" "spritesheets/head/heads/goblin/adult/bright_green.png" "$M/h_goblin.png"
grab "$ULPC" "spritesheets/head/heads/orc/male/dark_green.png"       "$M/h_orc.png"
grab "$ULPC" "spritesheets/head/heads/skeleton/adult/skeleton.png"   "$M/h_skeleton.png"
grab "$ULPC" "spritesheets/head/heads/wolf/male/fur_grey.png"        "$M/h_wolf.png"
grab "$ULPC" "spritesheets/head/heads/troll/adult/blue.png"          "$M/h_troll.png"
grab "$ULPC" "spritesheets/head/heads/goblin/child/amber.png"        "$M/h_imp.png"
grab "$ULPC" "spritesheets/head/heads/human/male/olive.png"          "$M/h_human.png"
grab "$ULPC" "spritesheets/head/heads/vampire/adult/lavender.png"    "$M/h_wraith.png"
grab "$ULPC" "spritesheets/head/heads/minotaur/male/fur_black.png"   "$M/h_beast.png"

echo
echo "done. now run:  python3 scripts/build_assets.py"
