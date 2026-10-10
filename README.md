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
pipeline/      ingest, draft, gate, voice, align
video/         Remotion project: one component per scene type
out/           rendered mp4, captions, audit report (not committed)
examples/      chapter-example.script.yaml shows the schema
mockups/       frame renderer and rendered comparison frames and clips
```

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

The clips are silent: the container has no Gemini API key. Caption pacing and
the highlight timing are simulated at a uniform words-per-second; in the
pipeline they come from word timestamps.

## Decisions so far

1. **Voice:** Gemini TTS first (`gemini-3.8-flash-tts`), WhisperX for word
   timings. Other engines stay behind the provider interface.
2. **Diagram look:** open; compare the two `scene-diagram-*` renders.
3. **Where the book sources live:** to be decided.
4. **Decorative illustrations:** open; compare `scene-illustration-*` with
   `scene-title-*`.

## Status

Design stage with visual mock-ups. Nothing in the pipeline runs yet. First
milestone is one chapter end to end with a hand-written script, Gemini
multi-speaker audio, WhisperX alignment, and a Remotion composition with three
scene types.
