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

## Voice and alignment (needs `GEMINI_API_KEY`)

Two small, dependency-free Python steps turn a scene of the script into audio
with word timings. The key is read from the environment only. In a Claude Code
cloud session it goes in the environment's secrets; locally, export it in your
shell. Never paste it into a chat or a file in this repo.

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

Design stage with visual mock-ups. Nothing in the pipeline runs yet. First
milestone is one chapter end to end with a hand-written script, Gemini
multi-speaker audio, WhisperX alignment, and a Remotion composition with three
scene types.
