# Explainer video generator: design

Status: proposal (October 2026). Nothing is implemented yet; this document is the
plan and the reasoning behind it.

## The problem with NotebookLM for book content

NotebookLM's Audio and Video Overviews are genuinely good at two things: the
two-host conversational delivery, and the clean, auto-generated visuals. But the
hosts decide what to say and what to show. For a book we authored, that is a
gamble on every generation: paraphrase drift, invented examples, dropped caveats,
wrong emphasis, and no way to fix a single sentence.

What NotebookLM gives you today, and what it does not:

| You can                                                | You cannot                                   |
|--------------------------------------------------------|----------------------------------------------|
| Write a steering prompt ("focus on the cost section")  | Supply or edit the script                    |
| Pick a format: Explainer or Brief                      | Pick or tune the voices                      |
| Pick a visual style (Classic plus six Nano Banana styles) | Edit the timeline or a single scene       |
| Choose the narration language                          | Run it from a pipeline: no public video API  |
| Regenerate from scratch                                | Get a per-sentence trail back to the page    |

The Enterprise edition has a preview REST API, but it covers notebooks and audio
overviews only; video overviews remain UI-only. So even with an Enterprise
licence you cannot put NotebookLM in a build.

## Principle: separate what is said from how it is performed

NotebookLM is one black box doing four jobs. The risk lives entirely in the first
two. The magic you want to keep lives in the last two, and those are now
commodity APIs that take *your* text as input and cannot add content.

| Job                   | NotebookLM        | This project                                            |
|-----------------------|-------------------|---------------------------------------------------------|
| Decide what is said   | the model         | authors: an LLM drafts, humans edit, a gate verifies    |
| Decide what is shown  | the model         | authors: diagrams as code, the book's own figures       |
| Perform the speech    | the model         | a TTS API reads the approved script verbatim            |
| Render the video      | the model         | Remotion renders deterministically from the script      |

So the design reduces to one rule: **the script and the diagrams are text files
in git, and everything downstream is a pure function of them.** Change one line,
re-render, and only that line's audio and that scene change.

## Pipeline

```
book/ch03.md ──► ingest ──► addressable spans (ch03#p12, ch03#fig-3-2)
                                   │
                                   ▼
                      draft (Claude + Citations API)
                                   │  every claim line carries the span it came from
                                   ▼
                        script.yaml  ◄──── authors edit (editor or PR)
                                   │
                                   ▼
                    gate: lint + cross-check + faithfulness judge     ──► FAIL = build stops
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
   diagrams/*.mmd|.excalidraw   TTS per scene        book figures
   rendered to SVG              (verbatim) + word       (as-is)
                                timestamps
            └──────────────────────┼──────────────────────┘
                                   ▼
                     Remotion composition (data-driven)
                                   │
                                   ▼
                        chapter.mp4 + captions.vtt + audit report
```

### 1. Ingest the source

Chapters are Markdown or AsciiDoc. The ingest step splits each chapter into
addressable spans: paragraphs, headings, figures, code blocks, tables. A
reference such as `ch03#p12` or `ch03#fig-3-2` resolves to exact text. Figures
in the book become reusable video assets as they are.

### 2. Draft the script (LLM, grounded)

Claude drafts a two-host dialogue from one chapter, using the Citations API so
that each factual line carries the span it was inferred from, rather than being
asked to cite after the fact. A style guide in the prompt encodes what makes
NotebookLM's format work: a hook, a naive question, an analogy, a clarification,
a recap, and two distinct personas (one asks what a reader would ask, one
explains and never speculates).

Rules given to the drafter:

- Every factual statement must come from the chapter. Prefer the book's own
  wording for definitions.
- Conversational glue (questions, reactions, bridges) is allowed and is marked
  `kind: bridge` or `kind: question`. It carries no facts.
- No new examples, numbers, names, or analogies that are not in the source. If
  the chapter has no analogy, ask for one in a `TODO` comment instead of
  inventing it.
- Output is the YAML schema below, not prose.

The output is a draft. Nothing is rendered from it until it passes review and
the gate.

### 3. Review (humans)

The script is a text file. Authors edit it in an editor or through a pull
request, exactly like a chapter. This is where "under our control" actually
happens, and it is cheap: editing a line and re-rendering costs seconds of TTS,
not a whole regeneration with a different random outcome.

### 4. Gate: automated faithfulness checks

This is the layer NotebookLM cannot give you: a per-sentence audit trail from the
video back to the page. Three checks, in increasing cost:

1. **Lint.** Every `kind: claim` line has a `source` that resolves. Every
   diagram, figure, and highlight id referenced exists. Scene and total durations
   are within bounds. Speaker alternation is sane.
2. **Deterministic cross-check.** Numbers, proper nouns, code identifiers, and
   quoted terms in a claim line must appear in its cited span (or in a small
   per-project allowlist). Cheap, and catches most invented specifics.
3. **Judge.** A second Claude call per claim line: given the cited span and the
   line, answer `SUPPORTED`, `UNSUPPORTED`, or `CONTRADICTED`, naming the
   offending phrase. The build fails on anything that is not `SUPPORTED`, and
   the report lists what to fix.

The gate output is kept as `audit.json` next to the video, so reviewers can see
which page each sentence came from.

### 5. Visuals: diagrams as code, figures as-is

Each scene declares one `visual`. Supported types:

| type           | source                                         | animation                                   |
|----------------|------------------------------------------------|---------------------------------------------|
| `title`        | text                                           | fade / type-on                              |
| `diagram`      | Mermaid, D2, or Excalidraw JSON, rendered to SVG at build time | draw-on, staged `reveal`, `highlight` of the element the current line refers to, pan and zoom |
| `figure`       | an image from the book                         | Ken Burns, callout box                      |
| `code`         | a code block from the book                     | typewriter reveal, line highlight           |
| `quote`        | a sentence from the book, cited                | pull-quote card                             |
| `terms`        | key terms with one-line definitions            | staged list                                 |
| `recap`        | bullet points                                  | staged list                                 |
| `illustration` | optional, decorative only, from a prompt an author wrote | still, slow zoom                    |

Authors own the diagram sources. The drafter may propose a Mermaid diagram, but
it is reviewed in the same PR as the script. Mermaid 11 renders the same source
in either a classic look or a hand-drawn look, so the clean-versus-sketch
decision is a theme setting rather than a choice of source format. Generated imagery is permitted only
in `illustration` scenes, is never used for anything that carries information,
and is labelled decorative in the audit report. If you want the hand-drawn charm
of NotebookLM's whiteboard style, Excalidraw sources plus a rough.js render give
you that without giving up control of what the diagram says.

Highlights are keyed to word timestamps: when host B says "the log", the `log`
node glows. That synchrony is most of what makes the visuals feel produced
rather than slide-like.

### 6. Voice: the TTS reads the script verbatim

Decision (October 2026): start with Gemini TTS. Whatever engine is used, the
only content it ever receives is the approved script, so this stage carries no
truthfulness risk; the choice is about delivery quality, cost, and timestamps.

**Gemini 3.8 TTS** is the current generation and fits this project unusually
well. Google's documentation states that it treats the text field strictly as a
verbatim transcript. Delivery is controlled outside the transcript:

- a `speech_metadata.style` per turn for sustained delivery, such as "warm and
  curious" or "measured, explaining";
- inline angle-bracket tags for point-in-time events, such as `<breath>`,
  `<chuckle>` or `<sigh>`, placed exactly where the sound occurs;
- CAPITALS for emphasis on a word;
- a conversational mode in the speech config for natural turn-taking cadence.

Nothing in the transcript is interpreted as an instruction, which is exactly
the property the gate relies on: what passed review is what gets spoken.

Mechanics that shape the pipeline:

| Topic | What the API gives us | Consequence for the design |
|-------|-----------------------|----------------------------|
| Models | `gemini-3.8-flash-tts` for maximum fidelity, nuanced acting and complex multi-speaker dialogue; `gemini-3.8-flash-lite-tts` as the cheaper bulk option. Same schema, one-parameter switch. | Start on Flash; measure; decide whether Lite is good enough for draft renders. |
| Speakers | Up to two speakers per request with prebuilt voices. Each turn is a separate text item carrying its `speaker` and `style`. | One scene is one request. Two hosts is the maximum, which the script schema already assumes. |
| Custom voices | Designed (`voice_...`) or replicated voices cannot share a multi-speaker request. | If we ever design bespoke host voices, synthesise per turn and concatenate the 24 kHz PCM ourselves. |
| Voices | 30 prebuilt studio voices, an extended library of hundreds, voice design from a natural-language persona, voice replication. | `hosts[].voice` becomes `gemini:<voice-name>`, for example `gemini:Kore`. |
| Output | 24 kHz mono 16-bit WAV per unary request; raw PCM when streaming. | Scene WAVs are concatenated at render time. |
| Timestamps | None. | Alignment is a separate step, below. |
| Access | Interactions API; plain REST from `pipeline/voice.py`, no SDK needed. The key goes in the `x-goog-api-key` header; a `Bearer` token is rejected. | In Claude Code cloud environments, a network secret adds the header, so the key never enters the container. Locally, `GEMINI_API_KEY`. Never in a chat, the repo, or a command line. |

**Alignment.** Highlights and captions need word timings, and Gemini TTS does
not return them. Because the transcript is known, a recognition error costs at
most one word's timing, never the alignment. Options, in order of preference:

1. **Gemini 3.5 Transcribe with word-level timestamps, on the same key.**
   `pipeline/align.py` sends the scene WAV to `gemini-3.5-transcribe` with
   `timestamp_granularities: ["word"]` and the scene's own vocabulary as custom
   vocabulary, then matches the transcript to the script tokens with a diff and
   interpolates any gap. One vendor, one key, no local models. Default.
2. **WhisperX, locally.** Open source forced alignment against the known
   transcript, free, CPU-fast for scene-length clips. The offline fallback.
3. **ElevenLabs Forced Alignment.** Audio plus transcript in, word timings out;
   the simplest API, but a second vendor.

**Pronunciation.** Gemini 3.8 has no lexicon of its own, and the transcript is
read as written. So a line has two texts: `text`, which reviewers approve, the
gate checks, and captions display; and `say`, what the engine receives, which
is `text` with the project lexicon applied (for example "fsync" to "F-sync").
Alignment runs against `say`, and timings are mapped back to `text` by token
position, which the lexicon keeps one-to-one.

**Script to request mapping**, one scene per request:

```json
{
  "model": "gemini-3.8-flash-tts",
  "input": [{ "type": "user_input", "content": [
    { "type": "text", "text": "Isn't that just doing the slow thing twice?",
      "annotations": [{ "type": "speech_metadata", "speaker": "Maya", "style": "curious, a little sceptical" }] },
    { "type": "text", "text": "Appending to one sequential file is far cheaper than updating scattered pages.",
      "annotations": [{ "type": "speech_metadata", "speaker": "Sam", "style": "measured, explaining" }] }
  ]}],
  "response_format": { "type": "audio" },
  "generation_config": { "speech_config": { "mode": "conversational",
    "speakers": [ { "speaker": "Maya", "voice": "Kore" }, { "speaker": "Sam", "voice": "Puck" } ] } }
}
```

**Fallbacks kept behind the provider interface:** ElevenLabs Eleven v3 Text to
Dialogue (multi-speaker, audio tags, timestamps in the same call) and OpenAI
`gpt-4o-mini-tts` with an `instructions` field (one voice per request, stitched
per line). Switching engines must never touch the script.

Supporting mechanics, engine-independent:

- **Caching.** Audio is cached by hash of (`say`, voice, style, model). Editing
  one line re-synthesises one line.
- **Localisation for free.** Because the script is the source of truth, a
  translated script through the same pipeline yields the same video in another
  language, with the same diagrams and the same audit trail. Gemini 3.8 TTS
  auto-detects the language of the transcript across 130 or more languages.

### 7. Render: Remotion

Remotion turns a React component tree into a video, frame by frame, from data.
A composition takes `script.yaml`, the alignment JSON, and the rendered SVGs;
one component per visual type; captions from the word timestamps; a speaker
indicator (name card or waveform) keeps the podcast feel. Same inputs, same
MP4. Render locally with the CLI, or on Remotion Lambda for batches.

Why Remotion over the alternatives:

- Diagrams are SVG, and React plus `interpolate()` animates SVG paths and
  attributes directly, which is exactly what draw-on and highlight need.
- Remotion publishes official agent skills (`npx skills add remotion-dev/skills`)
  so Claude Code can build and debug compositions reliably.
- Licence: free for individuals and for companies of up to three people;
  companies of four or more need a company licence. Check the current terms
  before a team adopts it.

Alternatives if Remotion does not fit: Motion Canvas (TypeScript, timeline
oriented), Manim (Python, strongest for maths), or a zero-dependency MVP of
Marp slides to PNG plus ffmpeg concat.

### 8. Optional: presenters with faces

NotebookLM does not use faces, so none are needed for parity. If a visible
presenter is wanted later, HeyGen and Synthesia both expose APIs that render an
avatar from your audio or script, and they slot in after the voice stage without
touching the content path.

## The script schema: the contract between authoring and production

See `examples/chapter-example.script.yaml` for a complete example. The
essentials:

```yaml
version: 1
id: ch03-write-ahead-log
source: { document: book/ch03-durability.md }
hosts:
  A: { name: Maya, role: "asks what a reader would ask", voice: "elevenlabs:<voice-id>" }
  B: { name: Sam,  role: "explains, never speculates",   voice: "elevenlabs:<voice-id>" }
scenes:
  - id: the-fix
    visual: { type: diagram, src: diagrams/ch03/wal-flow.mmd, reveal: [write, log, ack] }
    lines:
      - { speaker: A, kind: question, text: "Isn't that just doing the slow thing twice?" }
      - speaker: B
        kind: claim
        source: ch03-durability#p9
        highlight: log
        text: "Appending to one sequential file is far cheaper than updating scattered pages."
```

Invariants the gate enforces:

- `kind: claim` requires `source`; `bridge` and `question` forbid new facts.
- `source` must resolve to a span in the named document.
- `highlight` and `reveal` ids must exist in the diagram source.
- Inline vocal tags in angle brackets, such as `<chuckle>`, and the per-line
  `style` field are stripped before the faithfulness check, the cross-check and
  the captions, so they never count as content.

## What to still use NotebookLM for

Ideation on your own book. Generate an Audio Overview, listen for which
analogies and which ordering land, then write those choices into the script
deliberately. Treat it as a reader reacting to the chapter, not as a producer.
Nothing it generates is shipped.

## Build order

1. **MVP, one chapter end to end.** Ingest, script schema and lint, Gemini
   multi-speaker synthesis per scene (`pipeline/voice.py`), word alignment
   (`pipeline/align.py`), Remotion with three scene types (`title`, `diagram`
   from Mermaid, `recap`), captions. Hand-write the first script to
   prove the production half before automating the drafting half.
2. **Grounded drafting and the gate.** Claude draft with Citations; the
   deterministic cross-check; the judge; the audit report.
3. **Visual depth.** Highlight keyed to word timestamps, Excalidraw and rough.js
   style, `figure`, `code`, `quote` scenes, theme and transitions, music bed,
   intro and outro.
4. **Scale and options.** Provider abstraction with ElevenLabs as the second
   engine, audio caching, batch rendering, localisation, optional avatars.

## Decisions for the team

| # | Decision | Status |
|---|----------|--------|
| 1 | Voice engine | **Decided: Gemini TTS first** (`gemini-3.8-flash-tts`), with Gemini 3.5 Transcribe word timestamps for alignment on the same key. ElevenLabs and OpenAI stay behind the provider interface. |
| 2 | Visual identity: clean or hand-drawn diagrams | Open. Both looks are rendered from the same Mermaid source in `mockups/out/`, so the choice is a theme switch, not a source-format choice. Excalidraw remains available for freeform diagrams Mermaid cannot lay out. |
| 3 | Where the book sources live | TBD. |
| 4 | Whether decorative generated illustrations are allowed | Open. `mockups/out/scene-illustration-*.png` shows the scene type beside the no-illustration alternative, `scene-title-*.png`. |

## Sources

NotebookLM capabilities and limits:

- Google, "Video Overviews on NotebookLM get a major upgrade with Nano Banana": https://blog.google/technology/google-labs/video-overviews-nano-banana/
- 9to5Google on Video Overview formats and styles: https://9to5google.com/2025/10/13/notebooklm-video-overviews-styles/
- Google Workspace Updates, March 2026, customization options: https://workspaceupdates.googleblog.com/2026/03/new-ways-to-customize-and-interact-with-your-content-in-NotebookLM.html
- Sprep, no editing after generation: https://sprep.ch/blog/posts/can-you-edit-notebooklm-audio-output-and-the-workaround/
- Jellypod, no script editor or voice selection: https://www.jellypod.com/blog/notebooklm-video-overview-vs-explainer-video
- API status (consumer): https://autocontentapi.com/blog/does-notebooklm-have-an-api
- Enterprise API reference, audio overview service: https://docs.cloud.google.com/gemini/enterprise/docs/reference/rpc/google.cloud.notebooklm.v1alpha
- nblm-cli notes on which Enterprise features have endpoints: https://docs.rs/nblm-cli/0.1.4/nblm

Text to speech and alignment:

- Gemini API speech generation: https://ai.google.dev/gemini-api/docs/speech-generation
- Gemini-TTS on Google Cloud: https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
- Gemini 3.1 Flash TTS announcement: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-tts/
- LiveKit prompting guide for Gemini 3.1 Flash TTS: https://livekit.com/blog/gemini-3.1-flash-tts-prompting-guide
- ElevenLabs Text to Dialogue quickstart: https://elevenlabs.io/docs/eleven-api/guides/cookbooks/text-to-dialogue
- ElevenLabs dialogue with timestamps: https://elevenlabs.io/docs/api-reference/text-to-dialogue/convert-with-timestamps
- ElevenLabs Forced Alignment: https://elevenlabs.io/docs/capabilities/forced-alignment
- OpenAI cookbook, steering TTS: https://developers.openai.com/cookbook/examples/voice_solutions/steering_tts

Rendering and diagrams:

- Remotion licence: https://www.remotion.dev/docs/license
- Remotion agent skills: https://www.remotion.dev/docs/ai/skills
- rough-remotion, sketch-style SVG draw-on: https://github.com/eccentricnode/rough-remotion
- remotion-excalidraw-tts community skill: https://mcp.directory/skills/remotion-excalidraw-tts

Grounding:

- Anthropic, Citations API: https://anthropic.com/news/introducing-citations-api
