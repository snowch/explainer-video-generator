# explainer-video-generator

Create illustrated chapter videos from an authored script. The supported
workflow uses one narrator and Pillow/FFmpeg visuals. Speech can use the runnable
Edge example with provider word timings, or the documented local Qwen/Q1 recipe
with independently checked ASR alignment. Keep narration, on-screen wording and
artwork tied to the chapter's meaning.

Start with [the agent workflow](docs/agent-video-workflow.md), then follow
[the runnable example](examples/approved-narration/README.md).
[AGENTS.md](AGENTS.md) gives agents their working instructions. Read the
[Qwen model and Q1 voice guide](docs/qwen-speech.md) for that production path,
and the [page learning-aid criteria](docs/learning-aid-criteria.md) when a video
should reinforce its accompanying page.

## Production workflow

1. Read the chapter and establish the exact narration, audience, visual brief,
   and whether the video stands alone or reinforces a page. For a learning aid,
   state one observable learning objective and a memorable takeaway.
2. Map each scene's source idea, narration, on-screen wording and relevant
   illustration or diagram. Check what a viewer could wrongly infer. For a page
   learning aid, plan a prediction/explanation question, thinking time, a later
   answer and a specific return to the page exercise.
3. Generate complete-passage speech. Use provider boundaries for Edge, or fresh
   independent ASR alignment estimates for Qwen; label the timing source and
   review discrepancies. Keep display text separate from pronunciation text.
4. Render scenes independently with consistent characters, readable definitions,
   and topic-specific sketches and diagrams.
5. Review exported frames and actual audio. Check the meaning across speech and
   images, not just whether the MP4 plays. State whether audio review was by
   listening or automated transcription.

The reference example contains the original 775-word, approximately 5:29
*Why we misinterpret people* script. Its renderer is specific to that example;
other chapters need their own wording, situations, illustrations and layouts.
It runs without generated artwork for portability. For an illustrated brief,
that fallback is a technical baseline; supply reviewed artwork as described in
its README and the workflow.

## Build the Edge reference

Install FFmpeg and DejaVu fonts, then run from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/approved-narration/requirements.txt
python examples/approved-narration/synthesize.py
python examples/approved-narration/render.py
```

Outputs go to `out/approved-narration/`. The speech service requires network
access and honors `HTTPS_PROXY` when set. The client does not require a project
API key. Hosted speech can change independently of the client: retain rendered
audio and its content cache rather than assuming a later request is identical.

For automated speech review:

```bash
python -m pip install -r examples/approved-narration/requirements-audit.txt
python examples/approved-narration/audit_audio.py
```

The first audit downloads a Whisper model. Automated recognition supplements
review; it is not proof of exact pronunciation or a human listening pass.

For the approved original synthetic Q1 voice, use the pinned model, reference
hashes and sample recipe in [the Qwen guide](docs/qwen-speech.md). The Edge
commands above do not automatically select Qwen. Preserve an existing project
voice; model choice and reference identity belong in the content contract.

## Repository layout

| Location | Purpose |
| --- | --- |
| `docs/agent-video-workflow.md` | Authoring, artwork, synthesis, review and handoff instructions |
| `docs/design.md` | Current architecture and its limits |
| `docs/qwen-speech.md` | Pinned Qwen models, approved Q1 reference, setup, synthesis and timing review |
| `docs/learning-aid-criteria.md` | Page alignment, clarity, recall, application, accessibility and review evidence |
| `examples/approved-narration/` | Script, voice settings, renderer and audit/remux helpers |
| `diagrams/` | Editable diagram examples |
| `mockups/` | Earlier visual experiments; separate from the production renderer |
| `out/` | Ignored audio, clips, captions and review reports |

The earlier provider-specific voice/alignment prototype and its two-host YAML
example have been removed. Historical versions remain in git. The visual
mock-ups are retained for reference; their sample dialogue and simulated timings
are not the production script or alignment format.

## Status and limits

The single-narrator example renders a complete video and supports partial visual
updates that preserve the original compressed audio. Source-grounding and checks
that images match the narration remain manual. There is no automated
faithfulness gate or general-purpose chapter-to-video engine. Keep the script,
intentional artwork, scene plan and build settings in git; commit final videos
only when requested, and keep drafts and build caches out of the repository.
