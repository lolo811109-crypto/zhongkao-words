"""Retry illustrations that the image model's safety system rejected, with a rewritten scene.

Reads FAIL lines from .local/forge/img*.log, asks the text model for a gentler,
unambiguous scene, stores it as scene_alt in the entry, and regenerates.
Usage: python3 scripts/atlas/fix_blocked.py
"""
import json
import re

from common import FORGE, load_env, stream_chat, with_retry
from gen_images import make


def blocked_hids():
    hids = set()
    for log in FORGE.glob("img*.log"):
        for line in log.read_text(errors="ignore").splitlines():
            m = re.match(r"FAIL (\d+) ", line)
            if m and not (FORGE / "img" / f"{m.group(1)}.webp").exists():
                hids.add(int(m.group(1)))
    return sorted(hids)


def main():
    env = load_env()
    files = {}
    for p in sorted((FORGE / "text").glob("*.json")):
        for e in json.loads(p.read_text()):
            files[e["hid"]] = (p, e)
    for hid in blocked_hids():
        path, e = files[hid]
        prompt = (
            f"The illustration idea for the English word '{e['w']}' ({e['senses'][0]['en']}) was rejected by an image safety filter: "
            f"\"{e['scene']}\". Write ONE new scene (max 25 words) that still makes the meaning obvious, is gentle and suitable for all ages, "
            "shows no weapons, injuries, nudity, real people, flags, text, signs or logos. Reply with the scene only."
        )
        scene = with_retry(lambda: stream_chat(env, {"model": "gpt-6", "messages": [{"role": "user", "content": prompt}]}), tries=3).strip().strip('"')
        entry = {**e, "scene": scene}
        try:
            make(env, entry, FORGE / "img")
            status = "ok"
        except Exception as ex:
            status = f"still blocked: {str(ex)[:80]}"
        # Keep the scene that worked alongside the original for provenance.
        entries = json.loads(path.read_text())
        for x in entries:
            if x["hid"] == hid:
                x["scene_alt"] = scene
        path.write_text(json.dumps(entries, ensure_ascii=False))
        print(hid, e["w"], status, "|", scene, flush=True)


if __name__ == "__main__":
    main()
