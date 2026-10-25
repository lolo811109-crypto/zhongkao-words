"""Voice the everyday example sentence of each entry, in learning-path order (resumable).

Usage: python3 scripts/atlas/gen_sentence_audio.py [--workers 3] [--floor 4000] [--follow] [--example 0|1]
With several ElevenLabs keys (see common.eleven_keys) jobs rotate across accounts.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import threading
import time

from common import FORGE, eleven_keys, load_env
from gen_word_audio import VOICES, credits_left, synth

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]


def entries():
    out = {}
    for p in sorted((FORGE / "text").glob("*.json")):
        try:
            for e in json.loads(p.read_text()):
                out[e["hid"]] = e
        except Exception:
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--floor", type=int, default=4000)
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--example", type=int, default=0, choices=[0, 1])
    ap.add_argument("--skip-primary", action="store_true", help="only use the extra accounts")
    a = ap.parse_args()
    keys = eleven_keys(load_env())
    if a.skip_primary:
        keys = keys[1:]
    if not keys:
        raise SystemExit("no ElevenLabs keys")
    alive = list(keys)
    outdir = FORGE / "audio" / ("ex" if a.example == 0 else "ex2")
    outdir.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    stats = {"ok": 0, "fail": 0}
    lock = threading.Lock()
    submitted = set()

    def run(hid, text):
        if stop.is_set() or not alive:
            return
        key = alive[hid % len(alive)]
        try:
            synth(key, VOICES["uk" if a.example == 0 else "us"], text, outdir / f"{hid}.mp3")
            with lock:
                stats["ok"] += 1
                n = stats["ok"]
            if n % 150 == 0:
                for k in list(alive):
                    try:
                        left = credits_left(k)
                    except Exception:
                        continue
                    print(f"{time.strftime('%H:%M:%S')} ok={n} fail={stats['fail']} account#{keys.index(k)} credits={left}", flush=True)
                    if left < a.floor and k in alive:
                        alive.remove(k)
                        print(f"account#{keys.index(k)} reached the credit floor", flush=True)
                if not alive:
                    stop.set()
        except Exception as ex:
            with lock:
                stats["fail"] += 1
            print("FAIL", hid, str(ex)[:160], flush=True)

    with cf.ThreadPoolExecutor(a.workers) as pool:
        while not stop.is_set():
            es = entries()
            order = sorted(
                es.values(),
                key=lambda e: (CEFR.index(e["cefr"]) if e.get("cefr") in CEFR else 3, hashlib.sha1(e["src"].encode()).hexdigest()),
            )
            todo = [e for e in order if e["hid"] not in submitted and len(e.get("ex") or []) > a.example and not (outdir / f"{e['hid']}.mp3").exists()]
            for e in todo:
                submitted.add(e["hid"])
                pool.submit(run, e["hid"], e["ex"][a.example]["en"])
            print(f"{time.strftime('%H:%M:%S')} queued+={len(todo)}", flush=True)
            if not a.follow or (len(es) >= 7298 and not todo):
                break
            time.sleep(120)
    print("finished", stats, flush=True)


if __name__ == "__main__":
    main()
