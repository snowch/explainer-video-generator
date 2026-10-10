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


PROXY_401_HINT = (
    "\nHint: Google rejected a credential before reading the API key. If the same 401 comes back with no key,"
    " a bogus key, and from unrelated Google APIs, a Google credential is being added somewhere on the network"
    " path, for example by a proxy. See Troubleshooting in the README."
)


def api_error(e):
    detail = e.read().decode(errors="replace")[:800]
    hint = PROXY_401_HINT if e.code == 401 and "OAuth 2 access token" in detail else ""
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
    r = urllib.request.Request(API, data=json.dumps(req).encode(),
                               headers={"x-goog-api-key": key, "Content-Type": "application/json"})
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
