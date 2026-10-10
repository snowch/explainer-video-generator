#!/usr/bin/env python3
"""Synthesise one WAV per scene with Gemini TTS, which reads the script verbatim.

  python3 pipeline/voice.py examples/chapter-example.script.yaml [--scene the-fix] [--out out/audio] [--dry-run]

Needs GEMINI_API_KEY in the environment: never in this file, never in git.
The text sent to the engine is each line's `say`; delivery comes from the host's
or the line's `style`, never from the transcript. Audio is cached by content
hash, so editing one line re-synthesises one scene.
"""
import argparse
import base64
import json
import os
import struct
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scriptlib import content_hash, line_say, load_script  # noqa: E402

API = "https://generativelanguage.googleapis.com/v1beta/interactions"


def build_request(script, scene):
    hosts = script["hosts"]
    voice = script.get("voice", {}) or {}
    lexicon = script.get("pronunciation", {}) or {}
    content = []
    for line in scene["lines"]:
        host = hosts[line["speaker"]]
        content.append({
            "type": "text",
            "text": line_say(line, lexicon),
            "annotations": [{
                "type": "speech_metadata",
                "speaker": host["name"],
                "style": line.get("style") or host.get("style", ""),
            }],
        })
    speakers = [{"speaker": h["name"], "voice": h["voice"].split(":", 1)[1]} for h in hosts.values()]
    return {
        "model": voice.get("model", "gemini-3.8-flash-tts"),
        "input": [{"type": "user_input", "content": content}],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": {"mode": voice.get("mode", "conversational"), "speakers": speakers}},
    }


def find_audio(o):
    """The audio block is wherever a large base64 `data` string sits in the response."""
    if isinstance(o, dict):
        if isinstance(o.get("data"), str) and len(o["data"]) > 1000:
            return o
        for v in o.values():
            r = find_audio(v)
            if r:
                return r
    if isinstance(o, list):
        for v in o:
            r = find_audio(v)
            if r:
                return r
    return None


def wav_wrap(pcm, rate=24000):
    """Gemini returns WAV for unary requests; wrap raw 16-bit mono PCM if it does not."""
    header = struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", 36 + len(pcm), b"WAVE", b"fmt ", 16, 1, 1,
                         rate, rate * 2, 2, 16, b"data", len(pcm))
    return header + pcm


def synthesise(req, key):
    r = urllib.request.Request(API, data=json.dumps(req).encode(),
                               headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini API error {e.code}: {e.read().decode()[:800]}")
    blob = find_audio(body)
    if not blob:
        raise SystemExit("no audio in response: " + json.dumps(body)[:800])
    raw = base64.b64decode(blob["data"])
    return raw if raw[:4] == b"RIFF" else wav_wrap(raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--scene", help="scene id; default: every scene")
    ap.add_argument("--out", default="out/audio")
    ap.add_argument("--dry-run", action="store_true", help="write the request JSON instead of calling the API")
    args = ap.parse_args()

    script = load_script(args.script)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scenes = [s for s in script["scenes"] if not args.scene or s["id"] == args.scene]
    if not scenes:
        raise SystemExit(f"no scene {args.scene!r}")

    key = os.environ.get("GEMINI_API_KEY")
    if not key and not args.dry_run:
        raise SystemExit("GEMINI_API_KEY is not set. Add it as an environment secret, or use --dry-run.")

    for scene in scenes:
        req = build_request(script, scene)
        h = content_hash(req)
        wav = out / f"{scene['id']}.wav"
        side = out / f"{scene['id']}.json"
        sidecar = {"scene": scene["id"], "hash": h, "model": req["model"],
                   "lines": [{"speaker": c["annotations"][0]["speaker"], "say": c["text"]}
                             for c in req["input"][0]["content"]]}
        if args.dry_run:
            reqdir = out / "requests"
            reqdir.mkdir(exist_ok=True)
            (reqdir / f"{scene['id']}.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            print(f"dry-run: wrote {reqdir / (scene['id'] + '.json')}")
            continue
        if wav.exists() and side.exists() and json.loads(side.read_text())["hash"] == h:
            print(f"cached: {wav}")
            continue
        wav.write_bytes(synthesise(req, key))
        side.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
        print(f"wrote {wav} ({wav.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
