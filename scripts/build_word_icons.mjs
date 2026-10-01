// Cartoon pictures for the word cards, from Microsoft's Fluent Emoji (flat),
// which is MIT-licensed. Every one of the 80 words gets one - abstract words
// too (happy, brave, believe), which a photograph could never show.
//
// Get the icon set (it is not kept in the repo):
//   npm pack @iconify-json/fluent-emoji-flat && tar xzf iconify-json-fluent-emoji-flat-*.tgz
// then:
//   node scripts/build_word_icons.mjs package/icons.json
//
// Writes assets/words/<word>.svg and assets/words/photos.js, the manifest the
// game reads. Stops, naming the word, if a picture named below is missing.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'assets', 'words');
const src = process.argv[2];
if (!src) { console.error('usage: node scripts/build_word_icons.mjs path/to/icons.json'); process.exit(1); }
const set = JSON.parse(fs.readFileSync(src, 'utf8'));

// word -> Fluent Emoji name. Chosen for what the word means in the game, so
// "torch" is a flame (คบเพลิง), not a flashlight.
const PICTURE = {
  // 1 Verdant Woods
  forest: 'evergreen-tree', tree: 'deciduous-tree', river: 'water-wave', bird: 'bird',
  leaf: 'leaf-fluttering-in-wind', path: 'footprints', morning: 'sunrise', walk: 'person-walking',
  // 2 Grass Hills
  hill: 'sunrise-over-mountains', grass: 'herb', sheep: 'ewe', farm: 'tractor',
  village: 'house-with-garden', sky: 'sun-behind-small-cloud', wind: 'wind-face', happy: 'smiling-face-with-smiling-eyes',
  // 3 Sand Desert
  desert: 'desert', sand: 'hourglass-not-done', camel: 'two-hump-camel', oasis: 'desert-island',
  hot: 'hot-face', thirsty: 'cup-with-straw', travel: 'luggage', map: 'world-map',
  // 4 Caves & Crags
  cave: 'hole', rock: 'rock', dark: 'new-moon', torch: 'diya-lamp',
  deep: 'diving-mask', echo: 'speaking-head', found: 'magnifying-glass-tilted-left', climb: 'person-climbing',
  // 5 Snow Peaks
  snow: 'snowflake', ice: 'ice', mountain: 'mountain', cold: 'cold-face',
  freeze: 'thermometer', peak: 'mount-fuji', warm: 'sun', slip: 'banana',
  // 6 Volcano Valley
  fire: 'fire', flame: 'candle', smoke: 'cloud', ash: 'volcano',
  burn: 'wood', danger: 'warning', escape: 'person-running', brave: 'lion',
  // 7 Ancient Ruins
  ruin: 'derelict-house', ancient: 'amphora', temple: 'hindu-temple', statue: 'moai',
  treasure: 'gem-stone', secret: 'shushing-face', history: 'scroll', discover: 'telescope',
  // 8 Enchanted Grove
  magic: 'magic-wand', spell: 'sparkles', fairy: 'woman-fairy', glow: 'glowing-star',
  wish: 'shooting-star', power: 'high-voltage', secretly: 'ninja', believe: 'folded-hands',
  // 9 Shadow Ravine
  shadow: 'bust-in-silhouette', fear: 'fearful-face', silence: 'zipper-mouth-face', bridge: 'bridge-at-night',
  fall: 'fallen-leaf', already: 'check-mark-button', before: 'last-track-button',
  // 10 Dark Castle
  castle: 'castle', king: 'crown', throne: 'chair', sword: 'dagger',
  victory: 'trophy', courage: 'flexed-biceps', final: 'chequered-flag', legend: 'dragon',
};

const missing = Object.entries(PICTURE).filter(([, n]) => !set.icons[n]);
if (missing.length) {
  console.error('not in the icon set: ' + missing.map(([w, n]) => `${w} (${n})`).join(', '));
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });
const manifest = {};
let bytes = 0;
for (const [word, name] of Object.entries(PICTURE)) {
  const ic = set.icons[name];
  const w = ic.width ?? set.width ?? 16, h = ic.height ?? set.height ?? 16;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${ic.left ?? 0} ${ic.top ?? 0} ${w} ${h}">${ic.body}</svg>`;
  fs.writeFileSync(path.join(OUT, `${word}.svg`), svg);
  bytes += svg.length;
  manifest[word] = {
    src: `assets/words/${word}.svg`, kind: 'cartoon', artist: 'Microsoft', license: 'MIT',
    source: 'Fluent Emoji', url: 'https://github.com/microsoft/fluentui-emoji', file: name,
  };
}
fs.writeFileSync(path.join(OUT, 'photos.js'),
  '// Pictures for the word cards. Cartoons from Microsoft Fluent Emoji (MIT, see\n' +
  '// LICENSE-fluent-emoji.txt), written by scripts/build_word_icons.mjs. Photos\n' +
  '// from scripts/fetch_word_photos.py, if ever fetched, use the same shape.\n' +
  'window.LEXICORA_WORD_PHOTOS = ' + JSON.stringify(manifest, null, 1) + ';\n');
console.log(`${Object.keys(manifest).length} pictures, ${(bytes / 1024).toFixed(0)} KB of SVG`);
