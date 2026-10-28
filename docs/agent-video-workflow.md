# Agent workflow: authored, narrated explainer videos

This is the production approach used for **Why we misinterpret people** on
28 October 2026. The final video was **5:29**, with the user's 775-word narration,
28 scene clips including the closing hold, optional captions, and a cream,
dark-green, and sage palette. The final requested polish was the book URL and
copyright on the closing card; only that five-second scene was re-rendered.

Use this as a repeatable reference, not a claim that a successful export has
NotebookLM's production quality. The first versions in this session were
rejected as rough. Improvement required a different speech engine, preserving
the authored brief, checking the generated audio, removing irrelevant artwork,
and adjusting the visuals to the speech.

## Choose the appropriate path

| Path | Purpose | Entry points |
| --- | --- | --- |
| Existing Gemini prototype | Two-host dialogue and the repository's YAML contract | `pipeline/voice.py`, `pipeline/align.py`, `mockups/render.mjs` |
| Completed reference approach | A supplied single-narrator script with controlled illustrated/diagram slides | [examples/approved-narration](../examples/approved-narration/README.md) |

The reference example is intentionally independent of the proposed Remotion
application and faithfulness gate. It does **not** implement that whole design,
nor silently replace the repository's Gemini provider decision. Its renderer
contains scene layouts for this particular example; adapting another book
requires editing those layouts as well as the narration.

## 1. Establish the content contract

Record the title, duration range, exact narration, audience, palette, things to
avoid, desired closing card, and source/attribution. If the user has supplied
the script, treat it as authoritative: do not summarize it again or add a hook.
Stage directions become visuals and holds, not spoken sentences.

In this case the requirements were:

- Title: *Why we misinterpret people*, approximately 5–6 minutes.
- Calm, conversational delivery; no dramatic introduction, speculative claims
  about brains, promises of improvement, or additional examples.
- Preserve words such as “may”, “could”, and “not necessarily”.
- Warm cream backgrounds, dark green text, muted sage accents; no bright pink,
  decorative brain illustrations, or crowded slides.
- Clearly separate what was heard, what was guessed, and possible explanations.
- Keep definitions complete; invite viewers to pause for the exercise; finish
  on the three specified questions.

A reference video is evidence about presentation, not permission to copy its
content or override the written brief. Here the NotebookLM reference itself
departed from the user's intended styling and narration.

Keep the exact display script in git. The reference uses `narration.json`, an
ordered list of `{kind, text}` scenes. Scene boundaries group complete thoughts.
The final `end` scene has empty text and a five-second visual hold.

If drafting from a chapter instead, read the chapter first, attribute it, keep
a claim-to-source trail, and distinguish the author's examples from new ones.
Do not claim the proposal's automated faithfulness gate ran unless it did.

## 2. Produce a pronunciation-aware speech track

The final successful configuration in this session was:

| Setting | Value |
| --- | --- |
| Client/provider path | `edge-tts` 7.3.1, Edge neural speech service |
| Voice | `en-GB-SoniaNeural` |
| Rate | `-2%` |
| Request unit | A complete scene passage, not a new request for every sentence |
| Boundary metadata | `WordBoundary`; offsets/durations in 100-nanosecond units |
| Working audio | 24 kHz, mono, signed 16-bit PCM WAV |
| Export audio | AAC, 160 kbit/s; FFmpeg loudnorm target −16 LUFS, −1.5 dBTP |

`edge-tts` is a third-party client for an online service, not a guaranteed
production API. Voice availability and access can change. A different configured
provider can supply the same audio/timing contract; document that substitution
and check its output. Do not silently fall back to a poor voice and describe the
result as polished. Honour the execution environment's proxy/network policy;
the reference passes `HTTPS_PROXY` to the client when set.

Maintain two representations:

| Display/captions | Speech input |
| --- | --- |
| `1998` | `nineteen ninety-eight` |
| `1995` | `nineteen ninety-five` |

Normalize typography for delivery where useful (for example em dashes to
commas) without changing the words or their meaning. Define pronunciation
overrides explicitly in project settings. Do not indiscriminately expand
numbers: dates, measurements, decimals, identifiers, and acronyms need context.
Research names in this example included Raymond Nickerson, Gilbert, and Malone.

Generate a short voice sample containing the difficult terms before spending
time on the complete render. Longer passages allow continuity of intonation;
sentence-by-sentence stitching contributed to the early version's roughness.

Cache audio by a hash of **spoken text, voice, rate/delivery settings, provider
version, and boundary mode**. A cache keyed only by scene number is unsafe after
edits. The reference example includes content-based invalidation. Hosted speech
is not guaranteed to be bit-for-bit repeatable, so preserve approved audio.

## 3. Align against the audio, including expanded pronunciation

Save provider word boundaries with each audio file. Divide the Edge offsets by
10,000,000 to obtain seconds. Decode the audio with FFmpeg, retain a small safety
margin around the first/last timed word, add intentional scene padding, and
round each scene duration **up** to a whole number of video frames. Pad with
silence rather than cutting speech to fit the nearest frame.

The reference synthesizer adds roughly 0.25 seconds of lead, 0.45 seconds of
tail, a longer exercise hold, and the final five-second card. The engine itself
supplies within-passage phrasing. Measure the total; do not estimate duration
from word count and declare it compliant. Adjust delivery or meaningful holds
if necessary, preserving the approved text.

Match the normalized provider words to the normalized **spoken** script. The
reference checks equality and maps character spans back to the display text,
so one displayed `1998` can cover both `nineteen` and `ninety-eight`. It then
builds sentence cues and caption chunks from the first/last matching word times.
Do not substitute proportional word-count timing for real boundaries silently.

**Integration caution:** `pipeline/scriptlib.py` and the existing alignment
proposal assume token-for-token pronunciation mapping. A replacement such as
`1998 → nineteen ninety-eight` expands the token count. The standalone example
handles this; do not insert its multi-token mappings into the old alignment
path without adapting and testing that mapping too.

Keep canonical narration, speech text, boundaries, padded scene audio, and final
timings. Rebuilding visuals should not require synthesizing the voice again.

## 4. Make each visual element explain something

The final palette was cream `#F5F0E6`, dark green `#213E34`, sage `#A6B59C`, pale
sage `#E0E6D6`, and secondary green `#526858`. DejaVu Serif and DejaVu Sans were
available locally. Fonts, palette, artwork, and text layout should be fixed
inputs to rendering, not re-generated on each export.

Use a variety of restrained layouts: paired statements, a short timeline,
complete definitions, a question, a diagram, a practice card, and a closing
recap. Use staged reveals where narration introduces alternatives. Keep a
complete definition visible while it is explained; reveal emphasis, not a
fragment that could be mistaken for the whole definition.

The key comparison was explicitly labelled:

- **What you heard:** “I don’t think it’s ready yet.”
- **What you guessed:** “Rowan wants to embarrass me.”

Labels and wording carry the factual distinction. An expressive character
illustration must not imply that the guessed malicious motive is established.

Generated images can provide restrained fictional workplace illustrations.
Use consistent characters and review every asset before placing it. Generate
art without words; place accurate labels and quotations with code. An optional
transparent sheet can be framed into independent video views using FFmpeg crop
and overlay filters. Preserve alpha and keep the source asset intact.

**A concrete failure to avoid:** the generated phone illustration acquired an
unrequested decorative branch. The user correctly challenged it. The final
version replaced the phone with a simple coded diagram: a message and a
two-day indicator. Decorative foliage around the notebook was removed too.
Do not add plants, brains, mascots, cups, flourishes, or animations merely to
fill empty space. A diagram should make a relationship easier to understand.

The repository example does not depend on a session-specific generated image.
It renders without illustrations by default; its phone and notebook are drawn
in code. Optional artwork setup is described in its README.

## 5. Render scenes independently

The tested export used **1280×720, 24 fps, H.264/yuv420p video, AAC audio, optional
MP4 mov_text captions, and faststart**. These settings support ordinary playback
without a custom web player. Preserve the SRT as a separate deliverable too.

Pillow renders transparent typography/diagram layers. FFmpeg composites those
layers over the cream background and any approved illustrations, with gentle
fades at audio-derived cue times. It encodes each scene as its own video-only
clip using identical settings. Avoid an obligatory permanent subtitle band;
optional subtitles allow the slides to remain spacious.

Create a concat manifest of scene clips. For the first full export, stream-copy
the video clips, attach the concatenated narration, apply loudness normalization
once, encode AAC, and attach the SRT as mov_text. Source files and timings remain
available for corrections.

The example's renderer caches clips using the renderer source, scene timings,
project configuration, font files, and optional art hash. Changing a rendering
input invalidates the cache. `--only` is an explicit partial rebuild and does
not automatically remux a complete video with possibly stale other clips.

## 6. Review the result honestly

A valid MP4 is not a quality assessment. Perform distinct checks:

1. **Text integrity:** compare the canonical narration with all emitted cues;
   confirm no sentence or qualification was dropped. Do not speak stage
   directions. Keep displayed definitions and quotations complete.
2. **Actual speech:** listen if the environment permits it. Review dates, names,
   acronyms, pauses, stress, negations, and qualifications. A provider's submitted
   text or boundary metadata alone does not prove what a listener hears.
3. **Automated audio review:** transcribe the generated audio as another check.
   In this session, faster-whisper `base.en` on CPU/int8 confirmed the date
   phrases and names. Suppressing digit tokens encourages dates to appear as
   words, but ASR is not a phonetic certificate or a substitute for listening.
4. **Investigate discrepancies:** ASR repeated or misrecognized words at long
   segment boundaries. Re-transcribing the isolated scenes resolved the
   apparent errors. Do not change correct audio just to satisfy an ASR mistake.
5. **Visual review:** extract actual exported frames, especially the opening,
   definitions, long quotes, exercise, and closing card. Check wrapping,
   contrast, clipping, irrelevant details, and whether reveals follow speech.
6. **Technical review:** inspect duration and streams with ffprobe; decode the
   video with FFmpeg; confirm audio/video durations and end holds agree.

`audit_audio.py` decodes with FFmpeg to a NumPy float array before recognition.
This avoids the observed PyAV `metadata_errors` compatibility error. Its reports
explicitly identify themselves as automated checks. If you cannot listen, say
that, provide a voice preview, and do not claim you performed a listening review
or that the video matches NotebookLM's polish.

## 7. Make a closing-card correction without regenerating the video

The final requested edit was:

```text
https://snowch.github.io/understanding-people/
© 2026 Christopher Snow
```

The URL and copyright were verified against the book; they are project settings,
not values to copy into every future book. The closing questions remained intact.

For this kind of edit:

1. Preserve the approved MP4 and all scene clips.
2. Change only the closing layout/credit settings. Render that same-duration
   video clip. Do not regenerate narration or normalize audio again.
3. Concatenate the existing video clips with the replacement final clip.
4. Take audio and captions directly from the approved MP4 with `-c copy`.
5. Verify packet payload hashes and timestamps: all audio and captions, and all
   video before the edited scene, should be identical. Confirm total duration.

The actual edit preserved **7,775 preceding video packets**, every audio and
caption packet, and the **329-second** total duration. Only the final five
seconds were rendered. The included `replace_tail.py` performs this remux and
verification; follow the commands in the example README.

## 8. Handoff to the next agent

Commit the approved narration, pronunciation map, settings, scene layouts,
diagram sources, intentional assets or reproducible asset instructions, and
the commands needed to rebuild. Keep large rendered files, model weights,
downloaded reference videos, and caches out of git unless specifically wanted.

Record what was actually tested and the remaining limitations. In this case:

- Piper and the initial sentence-by-sentence Kokoro attempt did not meet the
  user's quality expectations; do not present them as equivalent alternatives.
- The later single-narrator Edge voice and complete-passage generation improved
  the delivery; dates were explicitly spelled out for speech.
- Automated transcription checked the full track and isolated uncertain
  passages. No claim of a human listening review was made for that final audit.
- The book's supplied narration and restrained visual brief mattered more than
  reproducing the reference video's decorative style.
- Small visual corrections were cheap because frozen audio and independent
  scene clips were retained.

