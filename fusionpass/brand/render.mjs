// Renders the Fusion Pass brand PNGs for the phone app (adaptive icon layers, legacy icons,
// splash, wordmark) from logo.svg + League Spartan.   node render.mjs  -> ./out
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
const here = process.env.BRAND_DIR || path.dirname(new URL(import.meta.url).pathname);
const exe = process.env.CHROME || fs.readdirSync(`${process.env.HOME}/.cache/ms-playwright`).filter((d) => d.startsWith('chromium-')).map((d) => `${process.env.HOME}/.cache/ms-playwright/${d}/chrome-linux64/chrome`)[0];
const dens = [['mdpi', 1], ['hdpi', 1.5], ['xhdpi', 2], ['xxhdpi', 3], ['xxxhdpi', 4]];
const jobs = [
  ...dens.flatMap(([d, m]) => [
    [`ic_launcher-${d}.png`, 'icon', 48 * m, 48 * m],
    [`ic_launcher_round-${d}.png`, 'round', 48 * m, 48 * m],
    [`ic_launcher_foreground-${d}.png`, 'glyph', 108 * m, 108 * m],
    [`ic_launcher_monochrome-${d}.png`, 'glyph', 108 * m, 108 * m],
  ]),
  ['ic_splash_logo.png', 'splash', 288, 288],
  ['app_icon_original.png', 'icon', 256, 256],
  ['app_logo_wordmark.png', 'wordmark', 1085, 344],
];
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--allow-file-access-from-files'] });
fs.mkdirSync(`${here}/out`, { recursive: true });
for (const [name, k, w, h] of jobs) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto(`file://${here}/render.html?k=${k}&w=${w}&h=${h}`);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(120);
  await p.screenshot({ path: `${here}/out/${name}`, omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } });
  await p.close();
}
await b.close();
console.log('rendered', jobs.length, 'files');
