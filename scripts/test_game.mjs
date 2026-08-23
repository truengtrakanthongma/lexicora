// Headless smoke + visual check. Boots the game, walks into a zone and
// samples frames so regressions in the render pipeline are measurable.
//   node scripts/test_game.mjs [zoneIndex]
import { createRequire } from 'module';
const { chromium } = createRequire(import.meta.url)('/opt/node22/lib/node_modules/playwright/index.js');
import fs from 'fs';

const ZONE = Number(process.argv[2] ?? 0);
const OUT = process.env.SHOTS || '/tmp/claude-0/-home-user-my-tense-game/85930c9b-50f3-56cf-a6b1-acf64009e318/scratchpad/shots';
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
const page = await browser.newPage({ viewport: { width: 1100, height: 760 } });

const errors = [];
// Google Fonts is unreachable from this sandbox and the browser always probes
// for a favicon; neither says anything about the game, so they are not failures.
const noise = /Failed to load resource/;
page.on('console', m => {
  const t = m.text();
  // The game warns on its own about layouts it could not make playable —
  // a walled-off landmark or a crystal it could not place. Those are failures.
  if (m.type() === 'warning' && t.startsWith('lexicora:')) errors.push(t);
  if (m.type() === 'error' && !noise.test(t)) errors.push(t);
});
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('response', r => {
  if (r.status() < 400) return;
  const u = r.url();
  if (!/favicon|fonts\.(googleapis|gstatic)/.test(u)) errors.push(`HTTP ${r.status()} ${u}`);
});
page.on('requestfailed', r => {
  const u = r.url();
  if (!/favicon|fonts\.(googleapis|gstatic)/.test(u)) errors.push(`request failed ${u}`);
});

await page.goto('http://localhost:8765/index.html');
await page.click('#btn-begin');
await page.fill('#in-name', 'ทดสอบ');
await page.fill('#in-class', 'ป.6');
await page.fill('#in-no', '1');
await page.click('#class-grid > *:first-child');
await page.click('#btn-embark');
await page.waitForSelector('#screen-worldmap.show');

// Zones unlock in order and now also need the zone before to have been passed,
// so a test of zone 7 would otherwise only ever see the locked pin. Mark the
// save as cleared and passed throughout, and mark the pre-test as already sat
// so the run lands in the world rather than in a test paper.
await page.evaluate(() => {
  const all = JSON.parse(localStorage.getItem('lexicoraSavesV3') || '{}');
  for (const k of Object.keys(all)) {
    const s = all[k];
    s.cleared = s.cleared.map(() => true);
    // Any value at or above the test length clears the pass gate; the harness
    // only needs the map open, and hard-coding the length would rot whenever
    // TEST_ITEMS or VOCAB_ITEMS changes.
    s.postBest = s.postBest.map(() => 999);
    s.pre = s.pre.map(() => ({score: 5, total: 14, at: Date.now(), ms: 1}));
    s.lessonSeen = s.lessonSeen.map(() => true);
  }
  localStorage.setItem('lexicoraSavesV3', JSON.stringify(all));
});
await page.reload();
await page.click('#btn-begin');
await page.fill('#in-name', 'ทดสอบ');
await page.fill('#in-class', 'ป.6');
await page.fill('#in-no', '1');
await page.click('#class-grid > *:first-child');
await page.click('#btn-embark');
await page.waitForSelector('#screen-worldmap.show');

await page.locator('#map-markers .zone-pin').nth(ZONE).click();
await page.waitForTimeout(900);
// A zone can open on its pre-test or its grammar scroll; clear whichever is up.
if (await page.locator('#screen-test.show').isVisible()) {
  for (let i = 0; i < 12 && await page.locator('#test-options .opt').first().isVisible(); i++) {
    await page.locator('#test-options .opt').first().click();
    await page.waitForTimeout(80);
  }
  await page.waitForTimeout(250);
  await page.click('#btn-test-close');
  await page.waitForTimeout(500);
}
const lesson = page.locator('#btn-lesson-close');
if (await lesson.isVisible()) await lesson.click();
await page.waitForTimeout(600);

// Walk for a while so movement, footfalls and collision all actually run.
const DIRS = ['ArrowDown', 'ArrowRight', 'ArrowUp', 'ArrowLeft'];
for (const k of DIRS) {
  await page.keyboard.down(k);
  await page.waitForTimeout(700);
  await page.keyboard.up(k);
}

const frames = [];
for (let i = 0; i < 3; i++) {
  // Half the shots are taken mid-stride, so the walk cycle and its dust show.
  if (i > 0) await page.keyboard.down('ArrowDown');
  await page.waitForTimeout(400);
  frames.push(await page.locator('#world').screenshot({ path: `${OUT}/z${ZONE}_f${i}.png` }));
  await page.keyboard.up('ArrowDown');
  await page.waitForTimeout(200);
}
const delta = (a, b) => {
  let n = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) n++;
  return n;
};
console.log('zone', ZONE, 'frame byte deltas', delta(frames[0], frames[1]), delta(frames[1], frames[2]));

// Wander until a monster catches us, then fight a full exchange so the duel
// canvas, both attack animations and the hurt reaction all get exercised.
// Ten monsters roam each zone from random tiles, so there is no fixed route to
// one. Head first for the boss lair (a fixed corner per zone), then quarter the
// map on long legs until something engages. Trees and cliffs stop a leg early,
// hence the many changes of heading rather than one long diagonal.
let fought = false;
// Walking is the thing most easily broken by a layout change, and it fails
// silently: no error, just a hero who cannot leave the tile they landed on.
// So the sweep is bracketed by two shots of the same view, and if they come
// back near-identical the zone is walled in.
const beforeSweep = await page.locator('#world').screenshot();
const engaged = () => page.locator('#screen-battle.show').isVisible();
const leg = async (keys, seconds) => {
  for (const k of keys) await page.keyboard.down(k);
  for (let t = 0; t < seconds*4 && !fought; t++) {
    await page.waitForTimeout(250);
    fought = await engaged();
  }
  for (const k of keys) await page.keyboard.up(k);
  if (!fought) { await page.keyboard.press('e'); await page.waitForTimeout(150); fought = await engaged(); }
};
const V = ZONE < 5 ? 'ArrowUp' : 'ArrowDown';
const H = ZONE % 2 === 0 ? 'ArrowRight' : 'ArrowLeft';
const ROUTE = [[[V, H], 9], [[V], 5], [[H], 5],
               [['ArrowDown'], 7], [['ArrowLeft'], 7],
               [['ArrowUp'], 7], [['ArrowRight'], 7],
               [['ArrowDown', 'ArrowRight'], 7], [['ArrowUp', 'ArrowLeft'], 7]];
for (const [keys, secs] of ROUTE) {
  if (fought) break;
  await leg(keys, secs);
}
if (!fought) {
  // Only meaningful when no battle interrupted the sweep — a battle overlay
  // would explain the difference by itself.
  await page.screenshot({ path: `${OUT}/z${ZONE}_nofight.png` });
  const afterSweep = await page.locator('#world').screenshot();
  const moved = delta(beforeSweep, afterSweep) / Math.max(1, beforeSweep.length);
  console.log('view changed over the sweep:', (moved * 100).toFixed(1) + '%');
  if (moved < 0.2) errors.push(
    `stuck: the view barely changed (${(moved * 100).toFixed(1)}%) over a full ` +
    `sweep of zone ${ZONE} — the hero cannot get anywhere`);
}
if (fought) {
  for (let round = 0; round < 3; round++) {
    const opts = page.locator('#battle-options .opt:not([disabled])');
    if (!(await opts.count())) break;
    await opts.first().click();
    await page.waitForTimeout(240);
    await page.locator('#battle-cv').screenshot({ path: `${OUT}/z${ZONE}_duel${round}.png` });
    await page.waitForTimeout(1400);
  }
  console.log('fought a battle: duel screenshots written');
} else {
  console.log('WARNING: no monster engaged, duel not exercised');
}
console.log(errors.length ? 'CONSOLE ERRORS:\n' + errors.join('\n') : 'no console errors');
await browser.close();
process.exit(errors.length ? 1 : 0);
