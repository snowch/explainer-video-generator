#!/usr/bin/env python3
"""Word timings for a scene's audio, so captions and highlights follow the voice.

  python3 pipeline/align.py examples/chapter-example.script.yaml --scene the-fix [--audio out/audio/the-fix.wav] [--out out/align]
  python3 pipeline/align.py examples/chapter-example.script.yaml --scene the-fix --simulate   # uniform timings, no API call

Uses Gemini 3.5 Transcribe with word-level timestamps on the same GEMINI_API_KEY,
then matches the transcript against the known script tokens. The script is the
source of truth, so a recognition error costs at most one word's timing; the
missing timing is interpolated from its neighbours.
"""
import argparse
import base64
import difflib
import json
import os
import re
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scriptlib import line_display, line_say, load_script, norm, scene_by_id, tokens  # noqa: E402

API = "https://generativelanguage.googleapis.com/v1beta/interactions"
UPLOAD = "https://generativelanguage.googleapis.com/upload/v1beta/files"


def wav_duration(path):
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _post_json(url, body, key):
    r = urllib.request.Request(url, data=json.dumps(body).encode(),
                               headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=300) as resp:
        return json.loads(resp.read())


def upload_file(path, key, mime="audio/wav"):
    """Files API resumable upload: start, then upload+finalize. Returns the file URI."""
    data = Path(path).read_bytes()
    start = urllib.request.Request(UPLOAD, data=json.dumps({"file": {"display_name": Path(path).name}}).encode(), headers={
        "x-goog-api-key": key, "Content-Type": "application/json",
        "X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(len(data)), "X-Goog-Upload-Header-Content-Type": mime,
    })
    with urllib.request.urlopen(start, timeout=120) as resp:
        upload_url = resp.headers["X-Goog-Upload-URL"]
    up = urllib.request.Request(upload_url, data=data, headers={
        "Content-Length": str(len(data)), "X-Goog-Upload-Offset": "0", "X-Goog-Upload-Command": "upload, finalize",
    })
    with urllib.request.urlopen(up, timeout=300) as resp:
        info = json.loads(resp.read())
    return info["file"]["uri"]


def transcribe(audio_path, key, vocabulary, debug=False):
    config = {"transcription_config": {
        "mode": {"type": "verbatim", "timestamp_granularities": ["word"]},
        "custom_vocabulary": vocabulary[:1000],
    }}
    inline = {"type": "audio", "data": base64.b64encode(Path(audio_path).read_bytes()).decode(), "mime_type": "audio/wav"}
    try:
        body = _post_json(API, {"model": "gemini-3.5-transcribe", "input": [inline], "generation_config": config}, key)
    except urllib.error.HTTPError as e:
        if e.code not in (400, 413):
            raise SystemExit(f"Gemini API error {e.code}: {e.read().decode()[:800]}")
        uri = upload_file(audio_path, key)  # inline audio refused: go through the Files API
        try:
            body = _post_json(API, {"model": "gemini-3.5-transcribe",
                                    "input": [{"type": "audio", "uri": uri, "mime_type": "audio/wav"}],
                                    "generation_config": config}, key)
        except urllib.error.HTTPError as e2:
            raise SystemExit(f"Gemini API error {e2.code}: {e2.read().decode()[:800]}")
    if debug:
        print(json.dumps(body, indent=1)[:3000], file=sys.stderr)
    words = extract_words(body)
    if not words:
        raise SystemExit("no word timestamps found in response; re-run with --debug to see its shape")
    return words


def _seconds(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*([0-9.]+)\s*s?\s*", v)
        if m:
            return float(m.group(1))
    if isinstance(v, dict):  # {"seconds": 1, "nanos": 500000000}
        return float(v.get("seconds", 0)) + float(v.get("nanos", 0)) / 1e9
    raise ValueError(f"unrecognised time value {v!r}")


def extract_words(o, found=None):
    """Collect every dict that looks like a timed word, whatever the surrounding shape."""
    if found is None:
        found = []
    if isinstance(o, dict):
        text_key = next((k for k in ("word", "text", "token") if isinstance(o.get(k), str)), None)
        start_key = next((k for k in ("start", "start_time", "start_offset", "startTime", "start_s") if k in o), None)
        end_key = next((k for k in ("end", "end_time", "end_offset", "endTime", "end_s") if k in o), None)
        if text_key and start_key and end_key and not any(isinstance(v, (list, dict)) for v in (o[start_key], o[end_key])) \
                or (text_key and start_key and end_key and isinstance(o[start_key], dict)):
            try:
                found.append({"text": o[text_key], "start": _seconds(o[start_key]), "end": _seconds(o[end_key])})
                return found
            except ValueError:
                pass
        for v in o.values():
            extract_words(v, found)
    elif isinstance(o, list):
        for v in o:
            extract_words(v, found)
    return found


def match(script_tokens, heard):
    """Map each script token to a (start, end); unmatched tokens are interpolated."""
    a = [norm(t) for t in script_tokens]
    b = [norm(w["text"]) for w in heard]
    timing = [None] * len(a)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                timing[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
        elif tag == "replace" and (i2 - i1) == (j2 - j1):  # same count: trust positions
            for k in range(i2 - i1):
                timing[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
    matched = sum(1 for t in timing if t)
    # interpolate gaps between known neighbours
    i = 0
    while i < len(timing):
        if timing[i] is not None:
            i += 1
            continue
        j = i
        while j < len(timing) and timing[j] is None:
            j += 1
        left = timing[i - 1][1] if i > 0 else (heard[0]["start"] if heard else 0.0)
        right = timing[j][0] if j < len(timing) else (heard[-1]["end"] if heard else left + 0.4 * (j - i))
        n = j - i
        for k in range(n):
            s = left + (right - left) * k / n
            e = left + (right - left) * (k + 1) / n
            timing[i + k] = (s, e)
        i = j
    return timing, matched


def chunk_words(display, token_timing):
    """Caption words are whitespace chunks of the display text, punctuation included.
    Each chunk takes the timing of the script tokens inside it; a chunk with no token
    (a lone dash, say) joins the chunk before it."""
    words, k = [], 0
    for chunk in display.split():
        n = len(tokens(chunk))
        if n == 0:
            if words:
                words[-1]["text"] += " " + chunk
            continue
        ts = token_timing[k:k + n]
        k += n
        if not ts:
            break
        words.append({"text": chunk, "start": round(ts[0][0], 3), "end": round(ts[-1][1], 3)})
    return words


def build_alignment(script, scene, timing_per_token, duration, source):
    lexicon = script.get("pronunciation", {}) or {}
    hosts = script["hosts"]
    lines, pos = [], 0
    for idx, line in enumerate(scene["lines"]):
        disp = line_display(line, lexicon)
        n = len(tokens(line_say(line, lexicon)))
        ts = timing_per_token[pos:pos + n]
        pos += n
        ws = chunk_words(disp, ts)
        lines.append({"index": idx, "speaker": hosts[line["speaker"]]["name"], "kind": line.get("kind"),
                      "highlight": line.get("highlight"), "text": disp,
                      "start": ws[0]["start"] if ws else None, "end": ws[-1]["end"] if ws else None, "words": ws})
    return {"scene": scene["id"], "duration": round(duration, 3), "source": source, "lines": lines}


def simulate(script, scene, wps=2.6, gap=0.5):
    lexicon = script.get("pronunciation", {}) or {}
    timing, t = [], 0.4
    for line in scene["lines"]:
        n = len(tokens(line_say(line, lexicon)))
        for _ in range(n):
            timing.append((t, t + 1 / wps))
            t += 1 / wps
        t += gap
    return timing, t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--scene", required=True)
    ap.add_argument("--audio", help="scene WAV; default out/audio/<scene>.wav")
    ap.add_argument("--out", default="out/align")
    ap.add_argument("--simulate", action="store_true", help="uniform timings without calling the API")
    ap.add_argument("--debug", action="store_true", help="print the raw transcription response to stderr")
    args = ap.parse_args()

    script = load_script(args.script)
    scene = scene_by_id(script, args.scene)
    lexicon = script.get("pronunciation", {}) or {}
    say_tokens = [t for line in scene["lines"] for t in tokens(line_say(line, lexicon))]
    audio = Path(args.audio or f"out/audio/{scene['id']}.wav")

    if args.simulate:
        timing, duration = simulate(script, scene)
        if audio.exists():
            duration = wav_duration(audio)
        result = build_alignment(script, scene, timing, duration, "simulated")
    else:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY is not set. Add it as an environment secret, or use --simulate.")
        if not audio.exists():
            raise SystemExit(f"{audio} not found; run pipeline/voice.py first")
        heard = transcribe(audio, key, sorted({t for t in say_tokens if len(t) > 3}), debug=args.debug)
        timing, matched = match(say_tokens, heard)
        result = build_alignment(script, scene, timing, wav_duration(audio), "gemini-3.5-transcribe")
        result["matched_tokens"] = f"{matched}/{len(say_tokens)}"
        print(f"matched {matched}/{len(say_tokens)} script tokens to transcript words")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{scene['id']}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {path} ({result['source']}, {result['duration']} s, {len(result['lines'])} lines)")


if __name__ == "__main__":
    main()
