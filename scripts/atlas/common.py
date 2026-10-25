"""Shared helpers for the Word Atlas content forge.

Credentials come from the process environment or from files in the directory
named by ATLAS_SECRETS (default ~/.config/word-atlas): sub2.env with
SUB2_BASE_URL / SUB2_API_KEY, and elevenlabs.key. Nothing here prints or stores keys.
"""
import json
import os
import pathlib
import time
import urllib.request
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[2]
FORGE = ROOT / ".local" / "forge"
SECRETS = pathlib.Path(os.environ.get("ATLAS_SECRETS", pathlib.Path.home() / ".config" / "word-atlas"))


def load_env():
    env = {}
    p = SECRETS / "sub2.env"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    k = SECRETS / "elevenlabs.key"
    if k.exists():
        env["ELEVENLABS_API_KEY"] = k.read_text().strip()
    for name in ("SUB2_BASE_URL", "SUB2_API_KEY", "ELEVENLABS_API_KEY"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


def eleven_keys(env=None):
    """All ElevenLabs keys: the primary one plus any elevenlabs-*.key files in ATLAS_SECRETS."""
    env = env or load_env()
    keys = [env["ELEVENLABS_API_KEY"]] if env.get("ELEVENLABS_API_KEY") else []
    for p in sorted(SECRETS.glob("elevenlabs-*.key")):
        k = p.read_text().strip()
        if k and k not in keys:
            keys.append(k)
    return keys


def post_json(url, payload, headers, timeout=300):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def stream_chat(env, payload, timeout=600):
    """Stream a chat completion so long generations don't hit idle proxy timeouts."""
    payload = {**payload, "stream": True}
    req = urllib.request.Request(
        env["SUB2_BASE_URL"].rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + env["SUB2_API_KEY"]},
    )
    parts = []
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for line in r:
            line = line.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
            except ValueError:
                continue
            for ch in obj.get("choices", []):
                delta = ch.get("delta") or {}
                if delta.get("content"):
                    parts.append(delta["content"])
    return "".join(parts)


def with_retry(fn, tries=5, base=8):
    """Retry transient failures. Gateway back-pressure (429) waits without using up tries."""
    last = None
    i = busy = 0
    while i < tries:
        try:
            return fn()
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode("utf-8", "ignore")
            last = f"HTTP {e.code}: {body}"
            if e.code in (400, 401, 403) and "rate" not in body.lower():
                raise RuntimeError(last)
            if e.code == 429 and busy < 60:
                busy += 1
                time.sleep(min(60, 5 + busy * 3))
                continue
            i += 1
            time.sleep(base * i)
            continue
        except Exception as e:  # network hiccups
            last = repr(e)
            i += 1
            time.sleep(base * i)
    raise RuntimeError(last)
