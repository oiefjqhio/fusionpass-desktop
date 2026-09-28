// Renders the desktop app icon at every size the .ico/.icns need, then packs them (pack-icons.py).
//   NODE_PATH=<dir with playwright-core> node render-desktop.mjs && python3 pack-icons.py
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_CORE || 'playwright-core');
const here = path.dirname(new URL(import.meta.url).pathname);
const exe = process.env.CHROME || fs.readdirSync(`${process.env.HOME}/.cache/ms-playwright`).filter((d) => d.startsWith('chromium-')).map((d) => `${process.env.HOME}/.cache/ms-playwright/${d}/chrome-linux64/chrome`)[0];
const sizes = [16, 32, 48, 64, 128, 256, 512, 1024];
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--allow-file-access-from-files'] });
fs.mkdirSync(`${here}/out/desktop`, { recursive: true });
for (const s of sizes) {
  const p = await b.newPage({ viewport: { width: s, height: s } });
  await p.goto(`file://${here}/render.html?k=icon&w=${s}&h=${s}`);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(120);
  await p.screenshot({ path: `${here}/out/desktop/icon-${s}.png`, omitBackground: true, clip: { x: 0, y: 0, width: s, height: s } });
  await p.close();
}
await b.close();
console.log('rendered', sizes.length, 'sizes');
