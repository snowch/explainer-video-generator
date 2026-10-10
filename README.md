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
```

## Status

Design stage. Nothing runs yet. First milestone is one chapter end to end with a
hand-written script, ElevenLabs dialogue audio with timestamps, and a Remotion
composition with three scene types.
