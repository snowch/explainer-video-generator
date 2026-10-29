# Criteria for a video that reinforces a page

A page video should help its readers understand, remember and apply the page's
central lesson. Record the audience, source page/version and one observable
learning objective before writing the script: **after watching, what should a
reader be able to explain or do?** Establish whether the video supplements the
page or must stand alone. The user's approved script and brief remain controlling.

For an embedded learning aid, the page can carry reference material, full SQL,
complete definitions and detailed records. Use video to demonstrate a difficult
relationship or decision. Label excerpts or brief terminology reminders clearly;
do not present a partial definition as complete or remove a necessary caveat.

## Review rubric

Assess these against the intended readers, with a specific scene, timestamp or
artifact as evidence. Record **meets / revise / not assessed** with a short
reason; an unexplained numerical score is not evidence.

| Criterion | What to assess | Useful evidence |
| --- | --- | --- |
| Alignment and relevance | Does the video reinforce the page's main objective with consistent examples and terminology? | Scene-to-source plan; every scene has a learning purpose |
| Clarity | Can readers explain the central distinction in their own words? | A concise explanation question and its accurate answer |
| Added visual understanding | Do diagrams, movement and narration clarify a relationship that is harder to follow on the page? | Counting groups, a changing timeline or an investigation trail, rather than paragraphs read aloud |
| Focus and memorability | Is there one takeaway anchored to a distinctive example or image? Is reinforcement purposeful rather than repetitive? | One concrete takeaway; recurrence that adds a new inference |
| Active recall | Do readers predict, choose, trace or explain before the answer appears? | A question, silent response time and a later explanation; no answer leaked in captions or graphics |
| Application and page connection | Can readers use the lesson in the page's exercise and eventually on an unfamiliar example? | A specific return to the relevant record, query or exercise, with feedback after an attempted answer |
| Cognitive load and pacing | Can readers follow narration while inspecting the figure? Are new terms and identifiers introduced at a manageable pace? | Larger relevant excerpts, progressive reveals, an orientation trail and time to inspect evidence |
| Engagement | Does the example give readers a relevant reason to keep watching and a clear sense of progress? | A meaningful question and visible discoveries; calm delivery can suit the task |
| Accuracy and interpretation | Are claims, calculations, qualifications, definitions and visual implications faithful to the source? | Checked examples and a manual scene review, including what viewers could wrongly infer |
| Accessibility and control | Can readers follow on a phone, with captions, without colour alone, and with pause/replay? | Encoded frames at viewing size, labels, transcript and browser playback/caption checks |
| Series progression | Does each video add a new capability and connect to previous lessons without assuming the wrong example state? | Explicit continuity and differences; a useful next step |

A valid export, an appealing voice or a reassuring transcript cannot establish
these criteria by themselves. Treat learning design, speech quality, source
accuracy and technical integrity as distinct review questions.

## Build a short learning sequence

1. **Establish a relevant question.** Begin with the page's concrete example or
   problem and show what readers are trying to work out. Preserve an approved
   script; do not add a dramatic hook to material the user supplied verbatim.
2. **Invite a prediction.** Ask readers to count, choose a filter, trace a
   reference or explain a distinction using the visible evidence.
3. **Leave thinking time.** Metadata systems used four- to five-second silent
   holds after complete questions; invite pausing for more time. Choose holds
   for the task and audience rather than applying a universal duration rule.
4. **Demonstrate and explain.** Show what changes and why. Reveal the answer
   after the response opportunity, at an appropriate speech cue. Movement must
   explain inclusion, sequence or a relationship, not just decorate the frame.
5. **Return to the page for practice.** Name the actual exercise, record or query
   and what the reader should do. Give feedback after the attempted explanation,
   such as the page's existing “Check your answer”.

The Metadata systems adapter uses `hold_seconds` on narrated question scenes to
add silence after speech. The Edge example in this repository has its own
`pause` scene behaviour; it does **not** implement that JSON field automatically.
When adapting a synthesizer, implement and verify the hold explicitly. Captions
should follow the actual speech and end before silent thinking time; the next
scene should contain the answer.

Keep important text readable at the actual embedded width. For example, 24-pixel
text on a 1280-pixel frame becomes roughly 7 pixels at a 390-pixel playback
width. A full SQL listing may belong on the page while the video enlarges the
relevant filter. Test the actual player, including caption and control overlays
when paused. Provide a transcript and retain ordinary playback controls.

## Concrete reference examples

The completed Metadata systems learning aids illustrate these choices:

| Chapter | Memorable anchor | Reader task |
| --- | --- | --- |
| 1: metric meaning | Same four parcels; unfinished parcel changes the denominator | Predict 2/3 versus 2/4, then check a calculation against the recorded rule |
| 2: database metadata | One 12:20 arrival is late against noon and on time against 12:30 | Distinguish permitted structure, value meaning and the rows a filter counts |
| 3: lineage and provenance | Follow a displayed 100% back through matching records | Trace refresh → output → run → retained input and code; distinguish explanation from currency |

These illustrate the method, not a requirement to reuse parcels or the book's
palette in another subject. See the
[pinned chapter scene plans and reviews](https://github.com/snowch/metadata-book/tree/fac56101ce4f153f425d0150c302d1b5bb894910/video).

## Verify the exported learning aid

In addition to the runbook's source, speech and media checks:

- Inspect frames from each actual encoded scene, staged reveal and response hold.
  A static mock-up alone does not establish that the correct timing was encoded.
- Check that no answer appears during the response hold, in captions or graphics.
  Verify silence after the final question words and aligned audio/video durations.
- Compare emitted captions with canonical display narration, preserving numbers,
  qualifications and pronunciation substitutions separately.
- Exercise playback, seeking and caption loading at desktop and phone widths;
  check page overflow, paused-state overlays and the linked page activity.
- Confirm the published page references the new media/caption versions, and verify
  the deployed files when publication is part of the task.
- Record what was actually reviewed, the evidence locations and remaining limits.
  Do not infer a human listening review from ASR or a memory benefit from layout.

For several chapters, finish and validate one at a time. When the agreed workflow
includes committing and merging each chapter, complete that merge before starting
the next. Use the existing publication authorization and repository workflow;
these criteria do not add a separate approval requirement.

## Check whether learning lasts

Clear presentation and engaging viewing are useful design judgments. To assess
learning, ask representative readers for:

- **Immediate understanding:** explain the main lesson in their own words.
- **Delayed recall:** explain it again the following day without replaying.
- **Transfer:** apply it to a different dashboard, dataset or situation.

Record the questions, audience, timing and actual responses. Without such
observations, mark retention and transfer outcomes **not assessed**. A video can
feel clear while playing and still leave readers unable to use the lesson.
A small reader review is useful evidence; do not describe it as a controlled
study or promise a measured learning gain it did not establish.

## Review record

Keep a short record with each chapter:

```text
Source/version and intended readers:
Learning objective and one takeaway:
Scene-to-source plan:
Prediction/explanation question, hold and later answer:
Return-to-page activity and feedback:
Rubric findings with scene/timestamp evidence:
Speech review method, discrepancies and unresolved terms:
Encoded-frame, caption, playback and publication checks:
Reader understanding/recall/transfer observations, or not assessed:
Remaining limitations:
```
