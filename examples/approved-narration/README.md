# Approved-narration reference example

This is a portable version of the single-narrator workflow used for *Why we
misinterpret people*. Read [the agent runbook](../../docs/agent-video-workflow.md)
first. This is the repository's supported production workflow.

The renderer contains the layouts and wording for **this example**. It is not
a universal JSON-to-video engine. For another script, adapt the `kind` handlers,
on-screen wording, attribution, vocabulary hints in the audit script, and
duration settings. The speech, alignment, audit, and remux patterns are reusable.

## Files

| File | Purpose |
| --- | --- |
| `narration.json` | The full approved 775-word narration, divided into scenes |
| `project.json` | Voice, rate, pronunciation map, duration range, fonts, attribution |
| `synthesize.py` | Complete-passage neural speech, content cache, real word timings, WAV/SRT/cues |
| `render.py` | Scene layouts, coded diagrams, optional illustrations, video clips and mux |
| `audit_audio.py` | Recognize the actual audio, with optional isolated-scene rechecks |
| `replace_tail.py` | Copy original audio/captions, replace the ending, verify packet preservation |

Run commands from the repository root. Outputs default to
`out/approved-narration/`, which the root `.gitignore` already excludes.
Set `EXPLAINER_OUT` to an absolute path to use a separate build directory; use
the same value for synthesis and rendering. Do not point it at a source folder.

## Setup

The original environment used Python 3.12, FFmpeg/ffprobe 7.1.5, and DejaVu fonts.
Install FFmpeg and DejaVu through your system package manager if missing. Edit
`font_dir` in `project.json` for a different font installation.

```bash
python3 -m venv /tmp/explainer-venv
source /tmp/explainer-venv/bin/activate
python -m pip install -r examples/approved-narration/requirements.txt
```

The pinned Python versions were installed in the original environment. The
Edge service requires network access; this is not an offline speech engine.
It may change independently of the client. `HTTPS_PROXY` is used when set.
Do not embed credentials in source code or bypass network restrictions.

## Full build

```bash
python examples/approved-narration/synthesize.py
python examples/approved-narration/render.py
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,duration \
  -of json out/approved-narration/why-we-misinterpret-people.mp4
ffmpeg -hide_banner -loglevel error \
  -i out/approved-narration/why-we-misinterpret-people.mp4 -f null -
```

Inspect the actual exported frames and listen to the audio if possible. The
synthesizer verifies that provider boundary text matches pronunciation-expanded
input and that the measured duration is 5–6 minutes. These are useful checks,
not evidence of good prosody. A failed duration check means you should adjust
the rate or deliberate holds and rebuild; do not truncate the narration.

The final example in the original session measured about 329 seconds. Hosted
speech may differ on a future run. The preserved display script and target
range remain authoritative.

Generated outputs include `narration.wav`, `captions.srt`, `transcript.txt`,
`timings.json`, `audio-NN.wav`, provider word metadata, and `clip-NN.mp4`.
Retain them for corrections. Cache signatures prevent changed speech settings
or text from silently reusing the previous audio. `render.py` likewise checks
render inputs before reusing a clip.

## Optional illustrations

No generated image or session-specific path is required. With
`illustration_sheet: null`, the example renders text and coded diagrams.

To add the workplace illustrations, generate or supply a reviewed transparent
PNG asset and set `illustration_sheet` to its path relative to this folder.
The layout expects a 2×2 equal-quadrant sheet: top-left is the private workplace
conversation and top-right is the meeting. The bottom half is unused. The code
frames quadrants with FFmpeg rather than modifying the source image. The phone
and notebook remain coded diagrams.

An asset brief for the two used views:

> Restrained editorial illustration in dark green linework, sage and cream
> washes, natural muted skin tones, transparent background. Consistent fictional
> colleagues: Rowan with short curly hair and sage clothing; the protagonist
> with chin-length hair, glasses, and cream clothing. Private conversation: they
> calmly discuss a proposal. Meeting: Rowan points at the proposal while the
> protagonist listens, with one other colleague. No sinister expressions or
> dramatic gestures. No words, logos, foliage, brain imagery, mascots, or
> unrelated props. Keep each composition inside its quadrant with padding.

Review the actual image. Prompts do not guarantee compliance, and facial
expressions must not establish a motive the narration says is unknown. Keep
all factual labels in the renderer. Commit an approved asset deliberately if
exact illustrated rebuilds are wanted; generated images are not deterministic.

## Audit the actual speech

```bash
python -m pip install -r examples/approved-narration/requirements-audit.txt
python examples/approved-narration/audit_audio.py
python examples/approved-narration/audit_audio.py --scenes 7,9,11,13
```

The first use downloads a Whisper model. Reports are written under the build
directory. The isolated scenes cover alternatives, confirmation bias, and the
two research dates. Read the reports and investigate discrepancies; recognize
that ASR can hallucinate repeated words at segment boundaries. An ASR report
must not be described as a human listening review.

For a preview, export a short audio excerpt containing the difficult terms and
inspect it before the complete video render. Keep the numeric years in captions;
the configured speech substitutions are `nineteen ninety-eight` and
`nineteen ninety-five`.

## Closing-card-only edit

Preserve the current approved MP4 **before** changing anything. Change `book_url`
or `copyright` in `project.json`, or edit the `end` layout. These commands render
only scene 27 and preserve the original compressed audio/captions:

```bash
cp out/approved-narration/why-we-misinterpret-people.mp4 \
  out/approved-narration/approved-before-card-edit.mp4
python examples/approved-narration/render.py --only 27 --force --no-mux
python - <<'PY'
import json
from pathlib import Path
p = Path('out/approved-narration/timings.json')
print('Closing scene starts at:', json.loads(p.read_text())[-1]['start'])
PY
```

Use that measured start time, not a guessed or hardcoded timestamp:

```bash
python examples/approved-narration/replace_tail.py \
  --build out/approved-narration \
  --original out/approved-narration/approved-before-card-edit.mp4 \
  --output out/approved-narration/why-we-misinterpret-people-final.mp4 \
  --changed-from 323.9583333333333
```

The timestamp above is the original session's value; substitute your measured
value. The helper expects this example's stream order (video, audio, optional
captions), unchanged preceding clips, and a same-duration replacement ending.
It verifies payload hashes, timestamps, and total duration. An error means the
output needs investigation, not that the change has been successfully preserved.

`--only` never automatically muxes the full video. This is intentional: a
partial visual render should not re-encode audio or silently combine stale
unrelated clips. Use `replace_tail.py` for this card edit. For narration or
duration changes, rebuild and audit the affected timeline normally.

## Validation recorded with this reference

The portable scripts were checked in Python 3.12 on 28 October 2026:

- Python syntax and JSON parsing passed; the committed narration matched the
  production script exactly.
- One fresh neural-speech request plus the remaining cached passages rebuilt
  the full timing/caption track at 328.958 seconds of video.
- The phone and closing scenes rendered without optional artwork. A second
  render reused their content cache.
- The audit helper produced actual-audio reports for both research passages.
  ASR sometimes repeats words or hallucinates a word in a silent tail; its
  output still requires review, as described in the runbook.
- The closing-card helper ran against the original production files and
  preserved 7,775 earlier video packets, all audio/caption packets and their
  timestamps, and the 329-second container duration.

The original full illustrated video was produced before this portability pass.
The portable example defaults to text/diagrams and does not bundle that artwork
or claim a pixel-identical recreation without it.
