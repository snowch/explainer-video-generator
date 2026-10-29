# Working on explainer videos

Read [docs/agent-video-workflow.md](docs/agent-video-workflow.md) before generating
an authored explainer. It records the completed single-narrator workflow and
the quality corrections from the *Why we misinterpret people* video.

The runnable Edge production example is `examples/approved-narration/`: one
narrator, provider word timings, Pillow and FFmpeg. For local Qwen speech and the
approved original synthetic Q1 voice, also read [docs/qwen-speech.md](docs/qwen-speech.md).
It records the pinned Base/VoiceDesign revisions, reference hashes and production
adapter in Metadata systems. Qwen supplies no provider word boundaries: use fresh
independent ASR alignment estimates, preserve original recognition and flag
unmatched words. Do not label these estimates as provider timestamps or listening
approval. Preserve the project's approved voice and exact reference; regenerating
a similar VoiceDesign prompt does not reproduce Q1.

For page videos, read [docs/learning-aid-criteria.md](docs/learning-aid-criteria.md).
State the learning objective, demonstrate a relevant relationship, invite a
prediction/explanation before revealing its answer, and connect to the page's
practice activity. Review clarity, memorability, application, cognitive load,
engagement, accuracy, accessibility and series progression. Record actual review
evidence; retention and transfer outcomes remain unassessed without reader
observations. Keep complete definitions on the page when appropriate, clearly
labelling video excerpts and preserving necessary qualifications.

`docs/design.md` describes current architecture and limits. The Qwen recipe does
not add an engine switch to the Edge example. Do not restore the retired provider
prototype or describe planned automation as implemented.

- The user's current script and visual brief control the result. Do not add a
  dramatic opening, new examples, a second host, or promises of improvement to
  an approved script merely to imitate a reference video.
- Preserve qualifications, complete definitions, and the distinction between
  observed words, suspected motives, and possible explanations.
- Cache speech by its content and engine settings; for Qwen include model and
  reference WAV/transcript hashes, generation settings and actual SDK versions.
  Preserve reviewed audio and validate cache hashes when resuming interrupted work.
- Keep display text separate from pronunciation text. Check the actual audio,
  especially dates, names, acronyms, negations, and qualifications.
- Read the runbook's quality-review section. Never claim to have listened when
  the only check was transcription or a successful video export.
- Plan each scene against the source idea and narration before generating art.
  Keep characters and objects specific to the topic, and check that expressions,
  labels and reveals do not establish claims the narration leaves uncertain.
- Every visual element should serve the explanation. Remove irrelevant
  decoration rather than accepting it because an image generator included it.
- Keep scene audio, word timings, and individually encoded video clips. For a
  visual-only correction, render the affected scene and copy the original
  audio/caption streams; verify that unrelated video packets did not change.
- Keep generated audio, videos, model downloads, and caches under ignored
  `out/` directories. Commit source scripts, diagram definitions, project
  settings, and documentation. Review any generated artwork before committing
  it as a deliberate project asset.
- For a series, finish and validate each chapter before moving on. If the agreed
  workflow requires a separate commit and merge per chapter, complete that merge
  before starting the next; do not introduce another confirmation step.
- Use the existing authorization and repository workflow. Do not force-update
  a branch or overwrite unrelated work to save a video recipe.

