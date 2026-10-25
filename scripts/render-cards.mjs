#!/usr/bin/env node
/**
 * Render the social card, README banner and app screenshots with headless Chromium.
 *   node scripts/render-cards.mjs [--app http://localhost:5188/]
 * Set CHROME_PATH to use a specific Chromium build.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appArg = process.argv.indexOf("--app");
const app = appArg > 0 ? process.argv[appArg + 1] : null;
const index = JSON.parse(fs.readFileSync(path.join(root, "public/atlas/index.json"), "utf8"));
const font = pathToFileURL(path.join(root, "node_modules/@fontsource-variable/fraunces/files/fraunces-latin-opsz-normal.woff2")).href;
const fontItalic = pathToFileURL(path.join(root, "node_modules/@fontsource-variable/fraunces/files/fraunces-latin-opsz-italic.woff2")).href;
const thumb = (id) => pathToFileURL(path.join(root, "public/atlas/thumb", `${id}.webp`)).href;

// Illustrated words, spread across levels and topics, deterministic.
const illustrated = index.words.filter((w) => w[6] & 1);
const pick = (n, seed = 7) => {
  const out = [];
  const step = Math.max(1, Math.floor(illustrated.length / n));
  for (let i = 0; out.length < n && i < illustrated.length; i++) out.push(illustrated[(i * step + seed) % illustrated.length]);
  return out;
};

const fmt = (n) => n.toLocaleString("en-US");
const base = `
@font-face{font-family:F;src:url(${font}) format("woff2");font-weight:100 900}
@font-face{font-family:F;font-style:italic;src:url(${fontItalic}) format("woff2");font-weight:100 900}
*{box-sizing:border-box;margin:0}
body{background:#f3ecdf;color:#1e2640;font-family:-apple-system,"PingFang SC","Hiragino Sans GB",sans-serif;-webkit-font-smoothing:antialiased}
.serif{font-family:F,"Songti SC","STSong",serif;font-variation-settings:"opsz" 144}
.mosaic{display:grid;gap:10px}
.mosaic figure{position:relative;border-radius:14px;overflow:hidden;background:#ece3d2;box-shadow:0 10px 24px -14px rgba(30,38,64,.45)}
.mosaic img{width:100%;height:100%;object-fit:cover;display:block}
.mosaic figcaption{position:absolute;left:10px;bottom:8px;color:#fff;font:600 15px F,serif;text-shadow:0 1px 8px rgba(0,0,0,.5)}
`;

function card({ width, height, cols, rows, title, sub, chips, tile }) {
  const words = pick(cols * rows);
  return `<!doctype html><html><head><meta charset="utf-8"><style>${base}
  body{width:${width}px;height:${height}px;overflow:hidden;position:relative}
  .mosaic{position:absolute;inset:-40px -60px -40px 52%;grid-template-columns:repeat(${cols},${tile}px);grid-auto-rows:${tile}px;transform:rotate(-8deg);transform-origin:center}
  .fade{position:absolute;inset:0;background:linear-gradient(90deg,#f3ecdf 46%,rgba(243,236,223,.0) 66%)}
  .copy{position:absolute;left:72px;top:0;bottom:0;width:52%;display:flex;flex-direction:column;justify-content:center;gap:22px}
  .brand{display:flex;align-items:center;gap:14px;font:600 30px F,serif}
  .brand small{font:600 22px "Songti SC",serif;color:#7c7f8c;letter-spacing:.12em}
  h1{font-weight:600;font-size:${Math.round(height * 0.105)}px;line-height:1.08;letter-spacing:-.02em}
  h1 em{font-style:italic;color:#c4573a}
  p.sub{font-size:${Math.round(height * 0.04)}px;color:#444d68;line-height:1.5}
  .chips{display:flex;flex-wrap:wrap;gap:10px}
  .chips span{padding:8px 16px;border-radius:999px;background:#fbf8f2;border:1px solid rgba(30,38,64,.14);font-size:${Math.round(height * 0.03)}px;font-weight:600;color:#444d68}
  </style></head><body>
  <div class="mosaic">${words.map((w) => `<figure><img src="${thumb(w[0])}"><figcaption>${w[1]}</figcaption></figure>`).join("")}</div>
  <div class="fade"></div>
  <div class="copy">
    <div class="brand"><svg width="40" height="40" viewBox="0 0 32 32"><circle cx="16" cy="16" r="14.5" fill="none" stroke="#1e2640" stroke-width="1.5"/><path d="M16 3.5 19 16 16 28.5 13 16Z" fill="#1e2640"/><path d="M16 3.5 19 16H13Z" fill="#c4573a"/><circle cx="16" cy="16" r="1.6" fill="#f3ecdf"/></svg>词光 <small>WORD ATLAS</small></div>
    <h1 class="serif">${title}</h1>
    <p class="sub">${sub}</p>
    <div class="chips">${chips.map((c) => `<span>${c}</span>`).join("")}</div>
  </div></body></html>`;
}

const exe = process.env.CHROME_PATH;
const browser = await chromium.launch(exe ? { executablePath: exe } : {});
const shot = async (html, w, h, out, type = "jpeg") => {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
  // Load from a file URL so the page may read local fonts and illustrations.
  const tmp = path.join(root, ".local", "render-card.html");
  fs.mkdirSync(path.dirname(tmp), { recursive: true });
  fs.writeFileSync(tmp, html);
  await page.goto(pathToFileURL(tmp).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.screenshot({ path: out, type, quality: type === "jpeg" ? 88 : undefined });
  await page.close();
  fs.rmSync(tmp, { force: true });
  console.log("wrote", path.relative(root, out));
};

const title = `一词一画，<br><em>点亮雅思</em>。`;
const sub = `${fmt(index.count)} 个雅思词，每个都有一幅画<br>${fmt(index.examples)} 条原创例句 · 英美发音 · 免费开源`;
await shot(card({ width: 1200, height: 630, cols: 6, rows: 7, tile: 150, title, sub, chips: ["无需注册", "手机可用", "CC BY 4.0 词库"] }), 1200, 630, path.join(root, "public/brand/og-card.jpg"));
await shot(card({ width: 1600, height: 720, cols: 7, rows: 7, tile: 170, title, sub, chips: ["无需注册", "词汇星图", "JSON / CSV 下载"] }), 1600, 720, path.join(root, "docs/assets/banner.jpg"));

// App icon (maskable: artwork kept inside the safe zone).
await shot(
  `<!doctype html><html><body style="margin:0;width:256px;height:256px;background:#1E2640;display:grid;place-items:center"><svg width="165" height="165" viewBox="0 0 32 32"><circle cx="16" cy="16" r="13" fill="none" stroke="#F3ECDF" stroke-width="1.2"/><circle cx="16" cy="16" r="9.5" fill="none" stroke="#F3ECDF" stroke-width=".6" stroke-dasharray="1 1.8" opacity=".5"/><path d="M16 4 18.8 16 16 28 13.2 16Z" fill="#F3ECDF"/><path d="M16 4 18.8 16H13.2Z" fill="#E07A5A"/><path d="M4 16 16 13.6 28 16 16 18.4Z" fill="#F3ECDF" opacity=".35"/><circle cx="16" cy="16" r="1.4" fill="#1E2640"/></svg></body></html>`,
  256,
  256,
  path.join(root, "public/icon-512.png"),
  "png",
);

// A dense wall of illustrations for README and launch posts.
const wall = pick(12 * 6, 3);
await shot(
  `<!doctype html><html><head><meta charset="utf-8"><style>${base}body{width:1600px;height:820px;padding:24px;overflow:hidden}.mosaic{grid-template-columns:repeat(12,1fr);grid-auto-rows:120px}</style></head><body><div class="mosaic">${wall.map((w) => `<figure><img src="${thumb(w[0])}"><figcaption>${w[1]}</figcaption></figure>`).join("")}</div></body></html>`,
  1600,
  820,
  path.join(root, "docs/assets/mosaic.jpg"),
);

if (app) {
  const views = [
    ["today-desktop", "#/", 1440, 900],
    ["atlas-desktop", "#/atlas", 1440, 900],
    ["word-desktop", `#/atlas?w=${pick(1, 41)[0][0]}`, 1440, 900],
    ["today-mobile", "#/", 390, 844],
    ["atlas-mobile", "#/atlas", 390, 844],
    ["word-mobile", `#/atlas?w=${pick(1, 41)[0][0]}`, 390, 844],
  ];
  for (const [name, hash, w, h] of views) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, colorScheme: "light" });
    const page = await ctx.newPage();
    await page.addInitScript(() => localStorage.setItem("word-atlas:settings", JSON.stringify({ onboarded: true, startLevel: 2, splash: false })));
    await page.goto(new URL(hash, app).href, { waitUntil: "networkidle" });
    await page.waitForTimeout(1600);
    await page.screenshot({ path: path.join(root, `docs/assets/${name}.jpg`), type: "jpeg", quality: 86 });
    await ctx.close();
    console.log("wrote", `docs/assets/${name}.jpg`);
  }
}
await browser.close();
