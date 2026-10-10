#!/usr/bin/env python3
"""Synthesise one WAV per scene with Gemini TTS, which reads the script verbatim.

  python3 pipeline/voice.py examples/chapter-example.script.yaml [--scene the-fix] [--out out/audio] [--dry-run]

The API key comes from one of two places, never from this file or from git:
  - GEMINI_API_KEY in the environment, sent as the x-goog-api-key header; or
  - the network: with GEMINI_API_KEY unset, requests go out without a key, so
    something on the path must add it, such as a Claude Code network secret that
    sends x-goog-api-key to generativelanguage.googleapis.com.
The text sent to the engine is each line's `say`; delivery comes from the host's
or the line's `style`, never from the transcript. Audio is cached by content
hash, so editing one line re-synthesises one scene.
"""
import argparse
import base64
import io
import json
import os
import struct
import sys
import wave
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


HINT_BEARER = (
    "\nHint: the key reached Google as an OAuth bearer token (Authorization: Bearer ...), which Google rejects"
    " before reading it. Gemini API keys must arrive in the x-goog-api-key header with no prefix. If a network"
    " secret adds the key, set its header name to x-goog-api-key, clear the Bearer prefix, and allow only"
    " generativelanguage.googleapis.com. See Troubleshooting in the README."
)
HINT_NO_KEY = (
    "\nHint: no API key reached Google. Set GEMINI_API_KEY, or add a network secret that sends the"
    " x-goog-api-key header to generativelanguage.googleapis.com."
)
HINT_BAD_KEY = "\nHint: Google rejected the key itself. Check it, or create a new one, in Google AI Studio."


def api_key():
    """The key from the environment, or None when the network is expected to add it."""
    key = os.environ.get("GEMINI_API_KEY") or None
    if key is None and not getattr(api_key, "_noted", False):
        api_key._noted = True
        print("GEMINI_API_KEY is not set: sending requests without a key, so the network must add one.",
              file=sys.stderr)
    return key


def headers(key, content_type="application/json"):
    h = {"Content-Type": content_type} if content_type else {}
    if key:
        h["x-goog-api-key"] = key
    return h


def api_error(e):
    detail = e.read().decode(errors="replace")[:800]
    hint = ""
    if e.code == 401 and "OAuth 2 access token" in detail:
        hint = HINT_BEARER
    elif "unregistered callers" in detail or "API key is missing" in detail or "CREDENTIALS_MISSING" in detail:
        hint = HINT_NO_KEY
    elif "API_KEY_INVALID" in detail or "API key not valid" in detail:
        hint = HINT_BAD_KEY
    return SystemExit(f"Gemini API error {e.code}: {detail}{hint}")


def collect_audio(o, found=None):
    """Every base64 audio block in the response, in document order (steps[].content[].data)."""
    if found is None:
        found = []
    if isinstance(o, dict):
        data, mime = o.get("data"), str(o.get("mime_type") or o.get("mimeType") or "")
        if isinstance(data, str) and (mime.startswith("audio") or len(data) > 1000):
            found.append(base64.b64decode(data))
            return found
        for v in o.values():
            collect_audio(v, found)
    elif isinstance(o, list):
        for v in o:
            collect_audio(v, found)
    return found


def pcm_of(blob):
    """(pcm, rate, channels, sample_width) for a WAV block, or for raw 24 kHz mono 16-bit PCM."""
    if blob[:4] != b"RIFF":
        return blob, 24000, 1, 2
    try:
        with wave.open(io.BytesIO(blob)) as w:
            return w.readframes(w.getnframes()), w.getframerate(), w.getnchannels(), w.getsampwidth()
    except wave.Error:  # unusual header: fall back to the fmt and data chunks
        fmt = blob.find(b"fmt ")
        channels, rate = struct.unpack_from("<HI", blob, fmt + 10)
        width = struct.unpack_from("<H", blob, fmt + 22)[0] // 8
        data = blob.find(b"data")
        size = struct.unpack_from("<I", blob, data + 4)[0]
        return blob[data + 8:data + 8 + size], rate, channels, width


def to_wav(blobs):
    parts = [pcm_of(b) for b in blobs]
    fmt = parts[0][1:]
    if any(p[1:] != fmt for p in parts):
        raise SystemExit(f"audio blocks differ in format: {[p[1:] for p in parts]}")
    rate, channels, width = fmt
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(b"".join(p[0] for p in parts))
    return buf.getvalue()


def synthesise(req, key):
    r = urllib.request.Request(API, data=json.dumps(req).encode(), headers=headers(key))
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise api_error(e)
    blobs = collect_audio(body)
    if not blobs:
        raise SystemExit("no audio in response: " + json.dumps(body)[:800])
    return to_wav(blobs)


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

    key = None if args.dry_run else api_key()

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
