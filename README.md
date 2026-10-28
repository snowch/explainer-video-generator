# explainer-video-generator

Turn chapters we wrote into NotebookLM-style explainer videos (two engaging
hosts, clean animated diagrams) without handing the narrative or the visuals to
a model.

The one rule: **the script and the diagrams are text files in git, and
everything downstream is a pure function of them.** An LLM may draft the script,
but humans edit it, an automated gate verifies every factual line against the
cited passage of the book, a TTS engine reads the approved text verbatim, and
Remotion renders the result deterministically.

Read [docs/design.md](docs/design.md) for the full design: why NotebookLM cannot
be steered enough for authored books, the pipeline, the script schema, the
faithfulness gate, engine choices, and the build order.

## Completed single-narrator workflow

For a supplied script and a reproducible scene-by-scene build, start with
[the agent video workflow](docs/agent-video-workflow.md) and
[the runnable approved-narration example](examples/approved-narration/README.md).
They record the **5:29 “Why we misinterpret people”** production: preserving the
script, pronunciation-aware Edge neural speech, audio-derived timing, controlled
Pillow/FFmpeg visuals, actual-audio checks, and closing-card edits that preserve
the original compressed audio and earlier video.

This is an alternative reference path, not an integration into the Gemini/
Remotion prototype below. [AGENTS.md](AGENTS.md) gives the starting instructions
for agents working on a video.

## Planned layout

```
book/          chapter sources (Markdown/AsciiDoc) and figures
scripts/       one script.yaml per video: the reviewed, cited narrative
diagrams/      Mermaid / D2 / Excalidraw sources referenced by scripts
pipeline/      voice.py and align.py exist; ingest, draft and gate are next
video/         Remotion project: one component per scene type
out/           rendered mp4, captions, audit report (not committed)
examples/      chapter-example.script.yaml shows the schema
mockups/       frame renderer and rendered comparison frames and clips
```

## Voice and alignment (needs a Gemini API key)

Two small Python steps turn a scene of the script into audio with word timings.
Never paste the key into a chat or a file in this repo. Supply it one of two ways:

- **Claude Code cloud environment:** add a network secret, so the key never
  enters the container. Header name `x-goog-api-key`, no prefix, the key as the
  value, and `generativelanguage.googleapis.com` as the only allowed website.
  Do not use the Bearer type: Google reads `Authorization: Bearer` as an OAuth
  token and rejects the key with a 401. Leave `GEMINI_API_KEY` unset.
- **Your own machine:** `export GEMINI_API_KEY=...` in your shell.

```
python3 pipeline/voice.py examples/chapter-example.script.yaml --scene the-fix     # -> out/audio/the-fix.wav
python3 pipeline/align.py examples/chapter-example.script.yaml --scene the-fix     # -> out/align/the-fix.json
cd mockups && node render.mjs --video --only=diagram \
  --align=../out/align/the-fix.json --audio=../out/audio/the-fix.wav              # -> out/scene-diagram-*-voiced.mp4
```

`voice.py` sends each line verbatim as its own turn with the host's voice and
style, two speakers per request, and caches by content hash. `align.py` gets
word-level timestamps from Gemini 3.5 Transcribe on the same key and matches
them to the script, so captions, speaker switches and the diagram highlight
follow the real audio. Both have offline modes (`--dry-run`, `--simulate`).

### Troubleshooting

**HTTP 401 "Request had invalid authentication credentials. Expected OAuth 2
access token", reason `API_KEY_SERVICE_BLOCKED`.** The key reached Google as
`Authorization: Bearer <key>`, which Google treats as an OAuth token and rejects
before reading it. This is what a network secret of the Bearer type does. Change
the secret's header to `x-goog-api-key` with no prefix. If it applies to
`*.googleapis.com`, narrow it to `generativelanguage.googleapis.com`, because a
Bearer secret on every Google host breaks every Google API, not just Gemini.

**HTTP 403 "Method doesn't allow unregistered callers".** No key reached Google:
set `GEMINI_API_KEY` or add the network secret.

The steps need only Python 3 and PyYAML (`pip install pyyaml`), so they also run
on any machine with the key; the WAV and alignment JSON they write are all the
renderer needs.

## Mock-ups

`mockups/` renders real frames and short silent clips of the scene types so the
visual decisions can be made by looking rather than imagining. Both diagram looks
come from the same Mermaid source; only the theme differs.

```
cd mockups && npm install && node render.mjs --video
```

Outputs in `mockups/out/`:

| File | What it shows |
|------|---------------|
| `scene-diagram-clean.png` / `.mp4` | the write-ahead-log scene, classic look, with the spoken node highlighted |
| `scene-diagram-sketch.png` / `.mp4` | the same scene and source, hand-drawn look |
| `scene-title-*.png` | the chapter hook as a typographic card (no imagery) |
| `scene-illustration-*.png` | the same hook as a decorative `illustration` scene, with a hand-made vector stand-in where a generated image would go |

Without `--align` and `--audio` the clips are silent and caption pacing is
simulated at a uniform words-per-second; with them, timing and sound come from
the pipeline.

## Decisions so far

1. **Voice:** Gemini TTS first (`gemini-3.8-flash-tts`), Gemini 3.5 Transcribe
   for word timings. Other engines stay behind the provider interface.
2. **Diagram look:** open; compare the two `scene-diagram-*` renders.
3. **Where the book sources live:** to be decided.
4. **Decorative illustrations:** open; compare `scene-illustration-*` with
   `scene-title-*`.

## Status

The Gemini path has voice/alignment scripts and visual mock-ups; the full
Remotion application and authored-content gate remain planned. The separate
[approved-narration reference](examples/approved-narration/README.md) captures an
end-to-end single-narrator production using Edge speech and FFmpeg. It includes
an example-specific renderer, audio review helper, and verified partial-update
workflow.

