"""Illustrate every entry in one cohesive art direction (resumable, follows gen_text output).

Usage: python3 scripts/atlas/gen_images.py [--workers 6] [--only hid,hid] [--follow]
Output: .local/forge/img/<hid>.webp (768px) + raw png discarded.
"""
import argparse
import base64
import hashlib
import concurrent.futures as cf
import json
import subprocess
import threading
import time

from common import FORGE, load_env, post_json, with_retry

STYLE = (
    "Mid-century modern editorial illustration, like a plate from a vintage illustrated field guide. "
    "Strict limited palette: deep ink navy, warm terracotta, mustard ochre, muted sage green and soft sky blue on warm cream paper. "
    "Flat geometric shapes, confident clean silhouettes, subtle risograph grain and paper texture, gentle shading, "
    "one clear focal subject with generous negative space, centered square composition, calm and charming mood. "
    "Absolutely no text, letters, words, numbers, captions, signs, logos, watermarks or frames."
)

MODEL = "gpt-image-2.5-flare"


def entries():
    out = {}
    for p in sorted((FORGE / "text").glob("*.json")):
        try:
            for e in json.loads(p.read_text()):
                out[e["hid"]] = e
        except Exception:
            pass
    return out


def make(env, e, outdir):
    out = outdir / f"{e['hid']}.webp"
    if out.exists():
        return "cached"
    prompt = f"{STYLE}\n\nScene: {e['scene']}"
    payload = {"model": MODEL, "prompt": prompt, "size": "1024x1024", "quality": "low", "n": 1}

    def call():
        raw = post_json(
            env["SUB2_BASE_URL"].rstrip("/") + "/images/generations",
            payload,
            {"Authorization": "Bearer " + env["SUB2_API_KEY"]},
            timeout=300,
        )
        d = json.loads(raw)
        b64 = d["data"][0].get("b64_json")
        if not b64:
            raise ValueError("no image")
        return base64.b64decode(b64)

    png = with_retry(call, tries=4, base=10)
    tmp = outdir / f"{e['hid']}.png"
    tmp.write_bytes(png)
    part = outdir / f"{e['hid']}.part.webp"
    subprocess.run(
        ["cwebp", "-quiet", "-q", "78", "-resize", "768", "768", "-m", "6", str(tmp), "-o", str(part)],
        check=True,
    )
    part.rename(out)  # atomic: readers never see a half-written file
    tmp.unlink()
    return "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--out", default="img")
    ap.add_argument("--shard", default="0/1", help="i/n: only handle hids where hid %% n == i")
    a = ap.parse_args()
    env = load_env()
    outdir = FORGE / a.out
    outdir.mkdir(parents=True, exist_ok=True)
    only = {int(x) for x in a.only.split(",") if x}
    si, sn = (int(x) for x in a.shard.split("/"))
    submitted = set()
    stats = {"ok": 0, "fail": 0}
    lock = threading.Lock()

    inflight = [0]

    def run(e):
        try:
            make(env, e, outdir)
            with lock:
                stats["ok"] += 1
        except Exception as ex:
            with lock:
                stats["fail"] += 1
            print("FAIL", e["hid"], e.get("w"), str(ex)[:200], flush=True)
        finally:
            with lock:
                inflight[0] -= 1

    with cf.ThreadPoolExecutor(a.workers) as pool:
        while True:
            es = entries()
            # Learning-path order: easier levels first, so early words are illustrated first.
            rank = {c: i for i, c in enumerate(["A1", "A2", "B1", "B2", "C1", "C2"])}
            path = sorted(es.values(), key=lambda e: (rank.get(e.get("cefr"), 3), hashlib.sha1(e["src"].encode()).hexdigest()))
            todo = [
                e for e in path
                if e["hid"] not in submitted and e["hid"] % sn == si and (not only or e["hid"] in only)
                and not (outdir / f"{e['hid']}.webp").exists()
            ]
            # Keep the queue short so newly generated easy words can jump ahead.
            room = max(0, a.workers * 2 - inflight[0])
            for e in todo[:room]:
                submitted.add(e["hid"])
                with lock:
                    inflight[0] += 1
                pool.submit(run, e)
            if int(time.time()) % 60 < 5:
                print(f"{time.strftime('%H:%M:%S')} todo={len(todo)} ok={stats['ok']} fail={stats['fail']}", flush=True)
            if not todo and inflight[0] == 0 and (not a.follow or len(es) >= 7298):
                break
            time.sleep(5)
    print("finished", stats, flush=True)


if __name__ == "__main__":
    main()
