#!/usr/bin/env node
/**
 * Record a short product walkthrough of a running app to docs/assets/demo.mp4.
 *   node scripts/record-demo.mjs http://localhost:5188/ [--mobile]
 * Needs ffmpeg on PATH. Set CHROME_PATH to use a specific Chromium build.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const app = process.argv[2] || "http://localhost:5188/";
const mobile = process.argv.includes("--mobile");
const size = mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 };
const dir = path.join(root, ".local", "video");
fs.rmSync(dir, { recursive: true, force: true });
fs.mkdirSync(dir, { recursive: true });

const exe = process.env.CHROME_PATH;
const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const ctx = await browser.newContext({ viewport: size, deviceScaleFactor: mobile ? 2 : 1, colorScheme: "light", hasTouch: mobile });
// Demo profile: a learner a few weeks in, so the galaxy has lit stars.
const index = JSON.parse(fs.readFileSync(path.join(root, "public/atlas/index.json"), "utf8"));
const seeded = index.words.filter((w, i) => w[4] <= 2 && i % 3 === 0).slice(0, 640).map((w) => w[0]);
await ctx.addInitScript((ids) => {
  if (!sessionStorage.getItem("demo")) {
    localStorage.clear();
    localStorage.setItem("word-atlas:settings", JSON.stringify({ onboarded: true, startLevel: 2, dailyNew: 10, autoplay: false, splash: true }));
    const now = Date.now();
    const cards = Object.fromEntries(
      ids.map((id, i) => [id, { due: now + (1 + (i % 9)) * 86400000, s: i % 3 ? 8 : 40, d: 5, el: 3, sd: 6, ls: 0, reps: 4, lapses: 0, st: 2, seen: i < 18 ? now - 3600000 : now - (10 + (i % 20)) * 86400000 }]),
    );
    localStorage.setItem("word-atlas:v2:word-atlas-open", JSON.stringify({ version: 2, datasetId: "word-atlas-open", cards, bookmarks: [], days: {}, typing: [], session: null, mistakes: [] }));
    sessionStorage.setItem("demo", "1");
  }
}, seeded);
const page = await ctx.newPage();
const wait = (ms) => page.waitForTimeout(ms);

// Capture frames through the DevTools screencast (works headless, no extra binaries).
const cdp = await ctx.newCDPSession(page);
const frames = [];
cdp.on("Page.screencastFrame", async ({ data, sessionId, metadata }) => {
  const file = path.join(dir, `f${String(frames.length).padStart(5, "0")}.jpg`);
  fs.writeFileSync(file, Buffer.from(data, "base64"));
  frames.push({ file, t: metadata.timestamp });
  await cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => null);
});
await cdp.send("Page.startScreencast", { format: "jpeg", quality: 88, maxWidth: size.width * (mobile ? 2 : 1), maxHeight: size.height * (mobile ? 2 : 1) });
const glide = async (to, steps = 40) => {
  const from = await page.evaluate(() => scrollY);
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    await page.evaluate((y) => scrollTo(0, y), from + (to - from) * e);
    await wait(16);
  }
};

await page.goto(app, { waitUntil: "networkidle" });
// The splash: particles gather into the logo, then the doors open.
await wait(3000);
await page.mouse.click(size.width / 2, size.height / 2);
await wait(2400);
await glide(mobile ? 1500 : 700, 70);
await wait(900);
await glide(0, 40);
await wait(500);

// One learning step: meet a word, then recall it.
await page.getByRole("button", { name: /开始今天的旅程|继续旅程/ }).click();
await wait(2600);
await page.keyboard.press("Enter");
await wait(1800);

// The atlas: scroll the illustrated wall, open a word.
await page.goto(new URL("#/atlas", app).href, { waitUntil: "networkidle" });
await wait(1500);
await glide(mobile ? 2600 : 1600, 110);
await wait(600);
await page.locator(".tile").filter({ has: page.locator("img") }).nth(mobile ? 2 : 6).click();
await wait(2600);
await page.keyboard.press("ArrowRight");
await wait(1600);
await page.keyboard.press("ArrowRight");
await wait(1600);
await page.keyboard.press("Escape");
await wait(500);

// The word galaxy: every word a star.
await page.goto(new URL("#/atlas?view=galaxy", app).href, { waitUntil: "networkidle" });
await wait(4200);
const box = await page.locator(".galaxy-full canvas").boundingBox();
if (box) {
  for (let k = 0; k <= 30; k++) {
    await page.mouse.move(box.x + box.width * (0.35 + k * 0.006), box.y + box.height * (0.4 + k * 0.004));
    await wait(30);
  }
  await wait(900);
  await page.mouse.down();
  for (let k = 0; k <= 40; k++) {
    await page.mouse.move(box.x + box.width * (0.5 - k * 0.006), box.y + box.height * 0.6);
    await wait(16);
  }
  await page.mouse.up();
  await wait(1600);
}

if (!mobile) {
  await page.keyboard.press("Meta+k");
  await wait(400);
  await page.keyboard.type("envir", { delay: 140 });
  await wait(1400);
  await page.keyboard.press("Enter");
  await wait(2400);
}

await cdp.send("Page.stopScreencast");
await ctx.close();
await browser.close();

// Frames arrive only when the page changes; hold each one until the next.
const list = frames
  .map((f, i) => {
    const next = frames[i + 1]?.t ?? f.t + 0.5;
    return `file '${f.file}'\nduration ${Math.max(0.001, next - f.t).toFixed(4)}`;
  })
  .join("\n");
const concat = path.join(dir, "frames.txt");
fs.writeFileSync(concat, list + `\nfile '${frames.at(-1).file}'\n`);
const out = path.join(root, "docs/assets", mobile ? "demo-mobile.mp4" : "demo.mp4");
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", concat, "-vf", "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "slow", "-movflags", "+faststart", out]);
console.log("wrote", path.relative(root, out), frames.length, "frames");
