# Working on explainer videos

Read [docs/agent-video-workflow.md](docs/agent-video-workflow.md) before generating
an authored explainer. It records the completed single-narrator workflow and
the quality corrections from the *Why we misinterpret people* video.

The supported production path is `examples/approved-narration/`: one narrator,
Edge neural speech, provider word timings, Pillow, and FFmpeg. `docs/design.md`
describes its current architecture and limits. Do not restore the retired
provider prototype or describe planned automation as implemented.

- The user's current script and visual brief control the result. Do not add a
  dramatic opening, new examples, a second host, or promises of improvement to
  an approved script merely to imitate a reference video.
- Preserve qualifications, complete definitions, and the distinction between
  observed words, suspected motives, and possible explanations.
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
- Use the existing authorization and repository workflow. Do not force-update
  a branch or overwrite unrelated work to save a video recipe.

