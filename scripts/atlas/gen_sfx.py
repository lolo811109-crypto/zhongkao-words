"""Generate the app's sound kit with ElevenLabs Sound Effects (resumable).

UI cues get several variants so the best can be picked; ambience tracks loop seamlessly.
Usage: python3 scripts/atlas/gen_sfx.py [--only name,name]
Output: .local/forge/sfx/<name>-<n>.mp3
"""
import argparse
import concurrent.futures as cf
import json
import sys
import urllib.request

from common import FORGE, load_env, with_retry

STYLE = "Warm, soft, organic and calm, recorded close and clean, for a beautiful vintage-paper study app. No music bed, no voices."
UI = {
    "correct": (0.8, "Two quick soft wooden marimba notes rising a major third, gentle and satisfying, a correct-answer cue, clean short tail."),
    "wrong": (0.7, "One soft muted low wooden knock, a gentle 'not quite' cue, never harsh or buzzy, short."),
    "wrong2": (0.9, "A gentle two-note descending soft wooden marimba cue, low and mellow, a kind 'try again' sound, clearly audible, single clean phrase."),
    "flip": (0.6, "A single crisp but soft paper card being flipped over on a desk, quick."),
    "page": (0.9, "One gentle turn of a thick old book page, soft paper swish."),
    "complete": (2.2, "A short warm celebratory flourish: four ascending celesta and marimba notes ending on a soft shimmering chord, like finishing a journey."),
    "streak": (1.4, "A tiny sparkle of small glass bells, a cheerful milestone cue, light and short."),
    "start": (1.2, "A soft whoosh of a map unrolling followed by one warm low chime, the beginning of a journey."),
    "tap": (0.5, "A single very soft pencil tap on a wooden desk, extremely short."),
    "key": (0.5, "One soft vintage typewriter key press, muted and pleasant, single click."),
}
AMBIENT = {
    "rain": "Gentle steady rain on an old library window, soft drips, warm cozy interior room tone, no thunder.",
    "sea": "Calm sea waves softly lapping a pebble shore at dawn, distant seagulls very faint, gentle breeze.",
    "forest": "Peaceful forest morning: soft birdsong, light wind in leaves, a small stream trickling nearby.",
    "fire": "A quiet fireplace crackling at night with soft embers, faint crickets outside, very relaxing.",
    "voyage": "Inside a wooden sailing ship cabin at sea: gentle creaking timbers, soft waves against the hull, calm.",
    "cafe": "A quiet morning cafe without voices: soft clinking cups, espresso machine far away, gentle rain outside.",
}


def keys(env):
    out = [env["ELEVENLABS_API_KEY"]]
    from common import SECRETS
    for p in sorted(SECRETS.glob("elevenlabs-*.key")):
        k = p.read_text().strip()
        if k and k not in out:
            out.append(k)
    return out


def gen(key, name, text, seconds, loop):
    out = FORGE / "sfx" / f"{name}.mp3"
    if out.exists():
        return name, "cached"
    payload = {"text": text, "duration_seconds": seconds, "prompt_influence": 0.55, "model_id": "eleven_text_to_sound_v2"}
    if loop:
        payload["loop"] = True

    def call():
        req = urllib.request.Request(
            "https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
            data=json.dumps(payload).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()

    data = with_retry(call, tries=3, base=5)
    out.write_bytes(data)
    return name, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--variants", type=int, default=3)
    a = ap.parse_args()
    env = load_env()
    ks = keys(env)
    (FORGE / "sfx").mkdir(parents=True, exist_ok=True)
    only = set(filter(None, a.only.split(",")))
    jobs = []
    for name, (sec, text) in UI.items():
        for v in range(a.variants):
            jobs.append((f"{name}-{v}", f"{text} {STYLE}", sec, False))
    for name, text in AMBIENT.items():
        for v in range(2):
            jobs.append((f"amb-{name}-{v}", f"{text} Seamless ambience loop, steady level, no sudden events.", 30, True))
    jobs = [j for j in jobs if not only or j[0].rsplit("-", 1)[0] in only or j[0] in only]
    with cf.ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(gen, ks[i % len(ks)], *j) for i, j in enumerate(jobs)]
        for f in cf.as_completed(futs):
            try:
                print(*f.result(), flush=True)
            except Exception as e:
                print("FAIL", str(e)[:200], flush=True)


if __name__ == "__main__":
    sys.exit(main())
