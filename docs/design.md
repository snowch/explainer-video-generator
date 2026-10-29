# Authored explainer video design

Status: a runnable Edge example and a documented local Qwen/Q1 production
recipe, sharing an authored single-narrator and Pillow/FFmpeg approach. See
[the agent workflow](agent-video-workflow.md) for operational instructions and [the reference example](../examples/approved-narration/README.md)
for runnable Edge commands. [Qwen speech](qwen-speech.md) records the pinned
models, exact Q1 voice reference and external production adapter; the Edge
example has no Qwen engine switch.

## Content and artwork

The author controls the script, definitions, examples and visual brief. Read the
source before adapting a video. Record each scene's source idea, exact narration,
on-screen words, relevant illustration or diagram, and reveal cues. Review
whether the image could imply a claim or motive that the narration leaves open.

For an embedded learning aid, record an observable objective, a prediction or
explanation opportunity and a return to the page exercise. Use the
[learning-aid rubric](learning-aid-criteria.md) to assess the result and distinguish
design judgments from measured recall or transfer.

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

### Runnable Edge example

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

### Local Qwen production recipe

Metadata systems uses pinned `Qwen/Qwen3-TTS-12Hz-1.7B-Base` with one reusable
full prompt built from the approved Q1 synthetic reference WAV and matching
transcript. VoiceDesign generated the original audition; it is not rerun for
each scene. Keep model revisions, exact reference hashes, spoken text,
generation parameters, batch membership and actual runtime versions in provenance.

Qwen provides audio without provider word boundaries. The production adapter
keeps unprompted full-scene ASR separately from estimated canonical alignment,
including numeric-spelling reconciliation, unmatched/interpolated positions,
matching coverage and padding offsets. These estimates drive captions and cues;
they cannot prove every submitted word was spoken or certify pronunciation.
Pronunciation excerpts receive separate screening before rendering. Preserve
original ASR and distinguish both checks from actual listening.

The adapter's `hold_seconds` field adds deliberate silence after question speech
and captions, before an answer scene. That field is not implemented by this
repository's Edge example; adapt its existing pause behaviour explicitly when
porting a learning aid. Complete setup, hashes, sample code and the pinned
external implementation are in [qwen-speech.md](qwen-speech.md).

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

- Edge boundary-text equality verifies the timing metadata against the submitted
  script, not what a human listener actually hears.
- The audit helper transcribes generated audio with faster-whisper. It can
  misrecognize names or hallucinate words in silence; investigate discrepancies
  and distinguish this check from listening.
- Qwen ASR/canonical alignment is estimated, not provider timing or forced
  alignment. A 100% character match is not proof of phonetics or natural delivery.
- Review the narration and image together for every scene. A technically valid
  video can still teach the wrong thing through an expression, label or reveal.
- Inspect representative exported frames, caption timing, media streams and a
  full FFmpeg decode. Verify the published page and media paths when deploying.

Review learning-aid holds, answer timing, page exercise links and the actual
player at desktop and phone widths. Reader recall and transfer require separate
observations; a valid media file does not establish learning effectiveness.

There is no automated source-faithfulness judge, general chapter ingestion step
or universal scene-layout engine. Those capabilities must not be described as
implemented or used. The earlier provider-specific prototype is retired; git
history retains it. `mockups/` contains independent visual experiments, including
simulated timing, and is not integrated with the production JSON format.
