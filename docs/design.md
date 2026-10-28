# Authored explainer video design

Status: one supported production workflow, using Edge neural speech and
Pillow/FFmpeg. See [the agent workflow](agent-video-workflow.md) for operational
instructions and [the reference example](../examples/approved-narration/README.md)
for runnable commands.

## Content and artwork

The author controls the script, definitions, examples and visual brief. Read the
source before adapting a video. Record each scene's source idea, exact narration,
on-screen words, relevant illustration or diagram, and reveal cues. Review
whether the image could imply a claim or motive that the narration leaves open.

The scene plan is currently a human-reviewed document, not an enforced schema.
The narration format is an ordered JSON array of `{kind, text}` entries.
`project.json` supplies the voice, rate, pronunciation substitutions, duration
range, font directory, attribution and optional illustration sheet.

The renderer's `kind` handlers contain example-specific text and layouts. A new
chapter requires adapting those handlers, not just replacing `narration.json`.
Character sketches and objects should explain the new subject. Keep generated
art without text, put exact labels in the renderer, and inspect composed frames
for misleading expressions, cropped artwork and readability.

## Speech and timing

`synthesize.py` sends a complete scene passage to `edge-tts`, using
`en-GB-SoniaNeural` at the reference rate of `-2%`. The provider returns audio and
word-boundary metadata. Requests are cached using spoken text, voice, rate,
client version and boundary mode.

Display text remains separate from pronunciation text: for example, a displayed
`1998` is spoken as `nineteen ninety-eight`. The synthesizer checks normalized
provider text against the spoken input and maps character spans back to display
captions. This supports substitutions that change the number of spoken tokens.

Audio is decoded to 24 kHz mono PCM, padded with short leads/tails and deliberate
exercise holds, and rounded up to whole video frames. The outputs include the
combined narration, per-scene audio, cues, timings and SRT captions. The hosted
speech service is not deterministic or an offline dependency; preserve outputs
needed for exact revisions.

## Rendering

Pillow produces typography and diagram layers. FFmpeg composes those layers with
optional reviewed illustrations and timed fades. The reference exports 1280×720
at 24 fps, encoding each scene independently as H.264 video.

A full build concatenates video clips without re-encoding them, normalizes the
combined narration once, encodes AAC, and includes selectable MP4 captions.
Keep the separate caption file. For a browser embed, convert captions to WebVTT
and provide playback controls, a poster, transcript link and any contextual
caption the viewer needs.

For a visual-only revision, preserve the approved export, render the affected
scene, and copy the original compressed audio and captions into the new export.
Check payload hashes, timestamps and duration. The included tail-replacement
helper handles a same-length closing-card change. Narration edits require
updated speech, timing and captions; do not treat them as a visual-only remux.

## Verification and limits

- Boundary-text equality verifies the timing metadata against the submitted
  script, not what a human listener actually hears.
- The audit helper transcribes generated audio with faster-whisper. It can
  misrecognize names or hallucinate words in silence; investigate discrepancies
  and distinguish this check from listening.
- Review the narration and image together for every scene. A technically valid
  video can still teach the wrong thing through an expression, label or reveal.
- Inspect representative exported frames, caption timing, media streams and a
  full FFmpeg decode. Verify the published page and media paths when deploying.

There is no automated source-faithfulness judge, general chapter ingestion step
or universal scene-layout engine. Those capabilities must not be described as
implemented or used. The earlier provider-specific prototype is retired; git
history retains it. `mockups/` contains independent visual experiments, including
simulated timing, and is not integrated with the production JSON format.
