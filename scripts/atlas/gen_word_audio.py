"""Synthesize UK + US headword pronunciations with ElevenLabs (resumable).

Usage: python3 scripts/atlas/gen_word_audio.py [--workers 6] [--floor 30000]
Stops when remaining character credits drop below --floor.
"""
import argparse
import concurrent.futures as cf
import json
import threading
import time
import urllib.request

from common import FORGE, load_env, with_retry

VOICES = {"uk": "Xb7hH8MSUJpSbSDYk0k2", "us": "EXAVITQu4vr4xnSDxMaL"}  # Alice, Sarah
MODEL = "eleven_v4_turbo"


def credits_left(key):
    req = urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": key})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return d["character_limit"] - d["character_count"]


def synth(key, voice, text, out):
    payload = json.dumps({"text": text, "model_id": MODEL, "language_code": "en"}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_64",
        data=payload,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )

    def call():
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 2000:
            raise ValueError("audio too small")
        return data

    data = with_retry(call, tries=5, base=3)
    tmp = out.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.rename(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--floor", type=int, default=30000)
    a = ap.parse_args()
    key = load_env()["ELEVENLABS_API_KEY"]
    hw = json.loads((FORGE / "headwords.json").read_text())
    jobs = []
    for g in hw:
        for acc in ("uk", "us"):
            out = FORGE / "audio" / acc / f"{g['hid']}.mp3"
            if not out.exists():
                jobs.append((acc, g["word"], out))
    for acc in VOICES:
        (FORGE / "audio" / acc).mkdir(parents=True, exist_ok=True)
    print(f"jobs={len(jobs)} credits={credits_left(key)}", flush=True)
    stop = threading.Event()
    done = [0, 0]

    def work(job):
        if stop.is_set():
            return
        acc, word, out = job
        synth(key, VOICES[acc], word + ".", out)

    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = []
        for i, j in enumerate(jobs):
            futs.append(ex.submit(work, j))
        for f in cf.as_completed(futs):
            try:
                f.result()
                done[0] += 1
            except Exception as e:
                done[1] += 1
                print("FAIL", str(e)[:160], flush=True)
            if sum(done) % 200 == 0:
                left = credits_left(key)
                print(f"{time.strftime('%H:%M:%S')} done={done[0]} fail={done[1]} credits={left}", flush=True)
                if left < a.floor:
                    print("credit floor reached; stopping", flush=True)
                    stop.set()
    print("finished", done, flush=True)


if __name__ == "__main__":
    main()
