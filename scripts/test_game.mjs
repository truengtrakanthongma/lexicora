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
page.on('console', m => { if (m.type() === 'error' && !noise.test(m.text())) errors.push(m.text()); });
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

// Zones unlock in order, so a test of zone 7 would otherwise only ever see the
// locked pin. Mark everything cleared in the save and re-open the map.
await page.evaluate(() => {
  const all = JSON.parse(localStorage.getItem('lexicoraSavesV3') || '{}');
  for (const k of Object.keys(all)) all[k].cleared = all[k].cleared.map(() => true);
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
await page.waitForTimeout(700);
// Each zone opens on its grammar scroll; dismiss it so the world is visible.
const lesson = page.locator('#btn-lesson-close');
if (await lesson.isVisible()) await lesson.click();
await page.waitForTimeout(600);

// Frames one second apart: if the liquids animate, the pixels must differ.
const frames = [];
for (let i = 0; i < 3; i++) {
  frames.push(await page.locator('#world').screenshot({ path: `${OUT}/z${ZONE}_f${i}.png` }));
  await page.waitForTimeout(500);
}
const delta = (a, b) => {
  let n = 0;
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) n++;
  return n;
};
console.log('zone', ZONE, 'frame byte deltas', delta(frames[0], frames[1]), delta(frames[1], frames[2]));
console.log(errors.length ? 'CONSOLE ERRORS:\n' + errors.join('\n') : 'no console errors');
await browser.close();
process.exit(errors.length ? 1 : 0);
