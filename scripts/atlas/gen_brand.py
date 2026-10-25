"""Brand and topic artwork in the same art direction as the word illustrations."""
import base64
import concurrent.futures as cf
import json
import sys

from common import FORGE, load_env, post_json, with_retry
from gen_images import STYLE

MODEL = "gpt-image-2.5-flare"
WIDE = "1536x1024"

JOBS = {
    "hero": (WIDE, "A whimsical vintage explorer's atlas spread open on a desk; out of its pages rise tiny landmarks that are everyday objects - a teacup lighthouse, a pencil tower, a book bridge, an apple hill, a paper-boat harbour - connected by a dotted travel route, with a small compass and a hot-air balloon drifting above. Wide panoramic composition with calm sky space on the left half."),
    "og": (WIDE, "A grand illustrated fantasy map of an island continent shaped like an open book, with tiny regions of mountains, forests, a city, a harbour, a university and a lighthouse, a dotted route winding across it, a compass rose in a corner, sea with gentle waves around it. Leave a large calm area of empty cream sky at the top left."),
    "empty": ("1024x1024", "A small friendly fox explorer sitting on a suitcase, studying a folded map under a lantern, cozy and quiet."),
    "done": ("1024x1024", "A tiny explorer planting a terracotta flag on top of a small round hill at sunset, birds flying, sense of accomplishment."),
    "night": ("1024x1024", "A small cabin window at night with a desk lamp glowing over an open notebook, a cup of tea and stars outside."),
    "typing": ("1024x1024", "A charming vintage typewriter on a desk with a sheet of blank paper rolling out and tiny paper birds flying from it."),
    "listen": ("1024x1024", "A large old gramophone horn with gentle sound waves flowing out like ribbons and small birds following them."),
    "data": ("1024x1024", "An open wooden card-catalogue drawer filled with neat index cards, with a magnifying glass resting beside it."),
}
TOPIC_SCENES = {
    "education": "a stack of books with a graduation cap and an apple on top",
    "work": "a tidy office desk with a briefcase, a laptop and a coffee mug",
    "technology": "a friendly robot arm assembling a tiny circuit board",
    "science": "a microscope next to flasks and a model of an atom",
    "environment": "a hand holding a young green seedling over clean soil with wind turbines far behind",
    "health": "a stethoscope curled around a red apple and a glass of water",
    "society": "a diverse small crowd of people gathering in a town square",
    "government": "a classical courthouse building with columns and balanced scales",
    "economy": "a set of coins stacked into growing towers beside a small market stall",
    "media": "a vintage radio microphone and a folded newspaper",
    "arts": "an easel with a painting, a violin and a theatre mask",
    "travel": "a suitcase, a passport and a paper airplane over a world globe",
    "city": "a skyline of apartment buildings, a tram and a bridge",
    "nature": "a mountain lake with pine trees and a deer drinking",
    "daily": "a kitchen table with breakfast, a teapot and a potted plant",
    "emotion": "two friends hugging under an umbrella in light rain",
    "thinking": "a person thinking with a lightbulb glowing and a chess piece",
    "sport": "a football, a tennis racket and a running track",
    "history": "ancient stone ruins with a scroll and an hourglass",
}
for k, v in TOPIC_SCENES.items():
    JOBS[f"topic-{k}"] = ("1024x1024", v + ", arranged as a single neat still-life vignette.")


def run(env, name, size, scene):
    out = FORGE / "brand" / f"{name}.png"
    if out.exists():
        return name, "cached"
    payload = {"model": MODEL, "prompt": f"{STYLE}\n\nScene: {scene}", "size": size, "quality": "high", "n": 1}

    def call():
        raw = post_json(env["SUB2_BASE_URL"].rstrip("/") + "/images/generations", payload,
                        {"Authorization": "Bearer " + env["SUB2_API_KEY"]}, timeout=400)
        return base64.b64decode(json.loads(raw)["data"][0]["b64_json"])

    out.write_bytes(with_retry(call, tries=4, base=10))
    return name, "ok"


def main():
    env = load_env()
    (FORGE / "brand").mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    with cf.ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(run, env, n, s, p) for n, (s, p) in JOBS.items() if not only or n in only]
        for f in cf.as_completed(futs):
            try:
                print(*f.result(), flush=True)
            except Exception as e:
                print("FAIL", str(e)[:200], flush=True)


if __name__ == "__main__":
    main()
