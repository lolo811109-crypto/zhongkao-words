import { duck } from "./sound";
import { toast } from "../ui/Toast";

/*
 * One shared <audio> element, unlocked on the first tap. iOS Safari / WeChat
 * only allow programmatic play() on an element that has already played inside
 * a user gesture, so creating `new Audio()` per word made auto-play silent.
 */
const SILENT = "data:audio/mpeg;base64,SUQzBAAAAAAAIlRTU0UAAAAOAAADTGF2ZjYxLjcuMTAzAAAAAAAAAAAAAAD/83DAAAAAAAAAAAAASW5mbwAAAA8AAAAGAAADKQBaWlpaWlpaWlpaWlpaWlpae3t7e3t7e3t7e3t7e3t7e3ucnJycnJycnJycnJycnJycvb29vb29vb29vb29vb29vb3e3t7e3t7e3t7e3t7e3t7e3v////////////////////8AAAAATGF2YzYxLjE5AAAAAAAAAAAAAAAAJAKjAAAAAAAAAymyjycdAAAAAAAAAAAAAAAAAP/zQMQAAAADSAAAAABMQU1FMy4xMDBVVVVVVVVVVVVVTEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NCxFsAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVTEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NAxKQAAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVMQU1FMy4xMDBVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVX/80LEowAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVMQU1FMy4xMDBVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVX/80DEpAAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVf/zQsSjAAADSAAAAABVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVQ==";

const el: HTMLAudioElement | null = typeof Audio !== "undefined" ? new Audio() : null;
if (el) {
  el.preload = "auto";
  el.setAttribute("playsinline", "");
  el.setAttribute("webkit-playsinline", "");
}
let unlocked = false;
let token = 0;
let warned = false;

function unlock() {
  if (unlocked || !el) return;
  unlocked = true;
  try {
    el.src = SILENT;
    el.muted = true;
    const p = el.play();
    if (p) p.then(() => { el.pause(); el.muted = false; }).catch(() => { el.muted = false; unlocked = false; });
  } catch { unlocked = false; }
  try {
    if ("speechSynthesis" in window) {
      const u = new SpeechSynthesisUtterance(" ");
      u.volume = 0;
      speechSynthesis.speak(u);
    }
  } catch {}
}
if (typeof window !== "undefined") {
  for (const ev of ["touchend", "pointerdown", "click", "keydown"]) window.addEventListener(ev, unlock, { capture: true, passive: true });
  // Voices load asynchronously on iOS/Chrome.
  try { speechSynthesis?.getVoices(); speechSynthesis?.addEventListener?.("voiceschanged", () => speechSynthesis.getVoices()); } catch {}
}

export function stopAudio() {
  token++;
  if (el) el.pause();
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
}

/** Play a recording, falling back to the device voice. Resolves when playback ends. */
export async function play(url: string | null | undefined, text: string, accent: "uk" | "us" = "uk", rate = 1) {
  duck(true);
  try {
    return await speak(url, text, accent, rate);
  } finally {
    duck(false);
  }
}

function playOnce(a: HTMLAudioElement, url: string, rate: number, mine: number) {
  return new Promise<"ok" | "blocked" | "error" | "stopped">((resolve) => {
    a.muted = false;
    a.src = url;
    a.playbackRate = rate;
    const done = (r: "ok" | "error" | "stopped") => { a.onended = a.onerror = a.onpause = null; resolve(r); };
    a.onended = () => done("ok");
    a.onerror = () => done("error");
    a.onpause = () => done(mine === token ? "ok" : "stopped");
    const p = a.play();
    if (p) p.catch((e: DOMException) => {
      a.onended = a.onerror = a.onpause = null;
      if (mine !== token) resolve("stopped");
      else resolve(e && e.name === "NotAllowedError" ? "blocked" : "error");
    });
  });
}

async function speak(url: string | null | undefined, text: string, accent: "uk" | "us", rate: number) {
  stopAudio();
  const mine = ++token;
  if (url && el) {
    for (let attempt = 0; attempt < 2; attempt++) {
      const r = await playOnce(el, attempt ? `${url}${url.includes("?") ? "&" : "?"}r=${Date.now()}` : url, rate, mine);
      if (r === "ok") return "recorded" as const;
      if (r === "stopped" || mine !== token) return "stopped" as const;
      if (r === "blocked") {
        if (!warned) { warned = true; toast("点一下 🔊 按钮即可播放读音（手机需先点击屏幕）"); }
        return "blocked" as const;
      }
      await new Promise((res) => setTimeout(res, 300));
    }
  }
  if (mine !== token || !("speechSynthesis" in window)) return "unsupported" as const;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = accent === "uk" ? "en-GB" : "en-US";
  u.rate = rate * 0.95;
  const voices = speechSynthesis.getVoices().filter((v) => v.lang.replace("_", "-") === u.lang);
  const best = voices.find((v) => /premium|enhanced|natural|google/i.test(v.name)) || voices[0];
  if (best) u.voice = best;
  await new Promise<void>((r) => {
    u.onend = () => r();
    u.onerror = () => r();
    speechSynthesis.speak(u);
    setTimeout(r, 4000);
  });
  return "device" as const;
}
