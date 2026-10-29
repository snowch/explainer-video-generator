# Qwen speech and the approved Q1 voice

The local Qwen workflow was used for the published Metadata systems chapter
videos on 29 October 2026. This guide records its model, voice and review
contract. The runnable example in this repository still uses Edge; this guide
provides a Qwen synthesis recipe and links to the complete production adapter.
It does not add a Qwen switch to the Edge example.

For a continuing project, preserve its approved voice. Q1 is available for work
using this approved synthetic narrator; establish the voice in the content
contract for a new project. Do not silently substitute another voice or engine.

## Model and voice identity

| Setting | Recorded production value |
| --- | --- |
| Production model | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` |
| Production revision | `fd4b254389122332181a7c3db7f27e918eec64e3` |
| Voice | **Q1**, original synthetic warm adult female, natural British English |
| Reference origin | User-approved Q1 audition, created with Qwen VoiceDesign |
| Design model | `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` |
| Design revision | `5ecdb67327fd37bb2e042aab12ff7391903235d3` |
| Reference WAV SHA-256 | `fcc306527e8923ad02fa751be3af11bd717add1b6160d19b0532014c722ee17a` |
| Reference transcript SHA-256 | `12b39d4fe2c7d4e665c17ebe9392e5ece740b15be779b1244486500333a646a2` |
| Reference audio | 32.48 seconds, 24 kHz mono PCM16 WAV |
| Production device / precision | CPU / `torch.bfloat16`, SDPA attention |
| Production threads / batch | Four Torch threads; up to six complete passages, grouped by length |
| Working / export audio | 24 kHz mono PCM16 / AAC 160 kbit/s; normalize once at final mux |
| Timing source | Independent unprompted ASR aligned to canonical spoken text; estimated |

Q1 is a reference asset, not a built-in Qwen speaker ID. Its design prompt was:

> A warm adult female narrator with a natural British English accent. Explain
> this clearly to a colleague: conversational, thoughtful, gently varied emphasis,
> natural pauses, moderate pace. Avoid a theatrical or promotional delivery.

Use Base with the exact approved WAV and matching spoken transcript to continue
that voice. Build one reusable full reference prompt and reuse it across scenes.
A new VoiceDesign request with the same description is a new audition; it does
not reproduce Q1. The reference is original synthetic speech, not a real
person's recording. Retain its origin and approval record with the project.

## Reproduce the reference and setup

The source below is pinned to the completed learning-aid revision. Download the
small reference into ignored `out/`; keep model weights and generated speech out
of Git. A project may deliberately retain its approved synthetic reference as a
source asset, as Metadata systems does; do not accidentally commit build audio.

Run from this repository's root:

```bash
python3.12 -m venv /tmp/qwen-venv
/tmp/qwen-venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu \
  torch==2.15.0+cpu torchaudio==2.11.1+cpu
/tmp/qwen-venv/bin/pip install qwen-tts==0.1.1 transformers==4.57.3 \
  faster-whisper==1.2.1 num2words==0.5.14 Pillow==12.3.0 \
  numpy==2.5.4 soundfile==0.14.0
/tmp/qwen-venv/bin/python -c \
  "import torch,torchaudio; print(torch.__version__,torchaudio.__version__); assert torch.version.cuda is None; assert torchaudio.__version__.endswith('+cpu')"
```

These are the recorded Python 3.12 production versions. Install a compatible
available CPU Torch/torchaudio pair first if your platform needs different
builds; record the actual versions and validate a sample. Avoid pulling a large
CUDA runtime into a CPU-only environment. FFmpeg/ffprobe and DejaVu fonts are
needed for the complete video workflow. Preserve the environment's proxy and CA
settings for downloads. Model download and first ASR use need network access;
synthesis can run locally once the required assets are present.

Fetch the exact voice and pinned model:

```bash
/tmp/qwen-venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json, urllib.request
from huggingface_hub import snapshot_download

root = Path('out/qwen').resolve()
reference = root / 'reference'
reference.mkdir(parents=True, exist_ok=True)
source = ('https://raw.githubusercontent.com/snowch/metadata-book/'
          'fac56101ce4f153f425d0150c302d1b5bb894910/video/qwen-production/reference/')
for name in ('q1.wav', 'spoken.txt', 'q1.json'):
    urllib.request.urlretrieve(source + name, reference / name)
metadata = json.loads((reference / 'q1.json').read_text())
expected_audio = 'fcc306527e8923ad02fa751be3af11bd717add1b6160d19b0532014c722ee17a'
expected_text = '12b39d4fe2c7d4e665c17ebe9392e5ece740b15be779b1244486500333a646a2'
assert hashlib.sha256((reference / 'q1.wav').read_bytes()).hexdigest() == expected_audio
assert hashlib.sha256((reference / 'spoken.txt').read_bytes()).hexdigest() == expected_text
assert metadata['sha256'] == expected_audio
assert metadata['transcript_sha256'] == expected_text
snapshot_download(repo_id='Qwen/Qwen3-TTS-12Hz-1.7B-Base',
                  revision='fd4b254389122332181a7c3db7f27e918eec64e3',
                  local_dir=str(root / 'model'))
PY
```

The Base model and speech tokenizer occupy roughly 4.5 GB before caches and
runtime packages. CPU generation takes minutes; observed production memory was
roughly 5–10 GB, depending on batching. Start with one passage and a smaller
batch on constrained machines. These are observations, not performance promises.

## Generate a complete-passage sample

This is an audio-only recipe, not a replacement for the renderer's timing and
caption contract. Replace the sample with pronunciation-expanded speech input;
keep the display/caption text separately. Validate a short passage containing the
actual project's names, identifiers and numbers before generating the full track.

```bash
/tmp/qwen-venv/bin/python - <<'PY'
from pathlib import Path
import hashlib, json
from importlib.metadata import version
import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

root = Path('out/qwen').resolve()
reference = root / 'reference'
settings = dict(
    model='Qwen/Qwen3-TTS-12Hz-1.7B-Base',
    revision='fd4b254389122332181a7c3db7f27e918eec64e3',
    voice='Q1', seed=42, threads=4, device='cpu', dtype='bfloat16',
    max_new_tokens=1600,
    reference_sha256=hashlib.sha256((reference / 'q1.wav').read_bytes()).hexdigest(),
    reference_text_sha256=hashlib.sha256((reference / 'spoken.txt').read_bytes()).hexdigest(),
    spoken_text='Metadata describes data. Two on time out of three completed gives sixty six point seven percent.',
)
assert settings['reference_sha256'] == 'fcc306527e8923ad02fa751be3af11bd717add1b6160d19b0532014c722ee17a'
assert settings['reference_text_sha256'] == '12b39d4fe2c7d4e665c17ebe9392e5ece740b15be779b1244486500333a646a2'
torch.set_num_threads(settings['threads'])
torch.manual_seed(settings['seed'])
model = Qwen3TTSModel.from_pretrained(str(root / 'model'), device_map='cpu',
    dtype=torch.bfloat16, attn_implementation='sdpa')
prompt = model.create_voice_clone_prompt(
    ref_audio=str(reference / 'q1.wav'),
    ref_text=(reference / 'spoken.txt').read_text().strip(),
    x_vector_only_mode=False,
)
wavs, sr = model.generate_voice_clone(
    text=[settings['spoken_text']], language=['English'],
    voice_clone_prompt=prompt, max_new_tokens=settings['max_new_tokens'],
)
assert sr == 24000 and len(wavs) == 1
assert wavs[0].ndim == 1 and 0 < len(wavs[0]) / sr < 130
assert np.isfinite(wavs[0]).all() and np.max(np.abs(wavs[0])) < 1
sf.write(root / 'sample.wav', wavs[0], sr, subtype='PCM_16')
settings['audio_sha256'] = hashlib.sha256((root / 'sample.wav').read_bytes()).hexdigest()
settings['sdk_versions'] = {name: version(name) for name in
    ('qwen-tts', 'torch', 'torchaudio', 'transformers', 'numpy', 'soundfile')}
(root / 'sample.metadata.json').write_text(json.dumps(settings, indent=2) + '\n')
PY
```

Preserve generated audio after review. A seed and matching prompt are useful
provenance, not a guarantee of identical audio across environments or batches.
For full production, include spoken text, model revision, reference WAV/transcript
hashes, delivery settings, precision, threads, generation parameters and actual
SDK versions in cache/provenance records. Record seed and batch membership;
validate the cached audio's own hash before reuse. Resume from valid cached
passages after an interruption rather than regenerating the approved voice.

## Timing and pronunciation review

**Qwen supplies no provider word boundaries.** Do not reuse Edge boundaries or
label interpolated word positions as real provider timestamps or forced
alignment. Before rendering:

1. Transcribe each generated passage independently with Whisper `small.en` on
   CPU/int8, without a vocabulary prompt or digit suppression. Retain original
   text, word timestamps and probabilities separately from the intended script.
2. Inspect omissions, negations, names, numbers and identifiers in full-scene
   context. Reconcile number spellings only for alignment; never overwrite the
   original recognition. Matching submitted words to an intended script cannot
   prove they were all spoken.
3. Align ASR timing anchors to the pronunciation-expanded canonical text. Record
   matching coverage, differences and which words use interpolation. Rebuild
   captions and sentence cues against the new speech. Map expanded speech back
   to unchanged display text.
4. Record padding offsets explicitly, such as `audio_time_offset_seconds`, so
   pronunciation excerpts and reveals refer to the actual padded scene audio.
5. Extract contextual clips for every pronunciation override and listed review
   term. Transcribe them without hints, inspect differences and consult the full
   passage when short excerpts cut words or hallucinate extra speech. Run a
   freshness/hash check after corrections and before encoding.
6. Listen where available and record the method and unresolved terms in
   `review.md`. An ASR spelling match, even at 100% character coverage, cannot
   certify phonetics, naturalness or expressive delivery. If only recognition
   was available, say **no human listening review** and provide the audio preview.

Do not trim generated words to make a duration target pass. Round padded scene
lengths up to video frames. Explicit thinking holds follow question speech and
captions, with the answer in a later scene; see the
[learning-aid criteria](learning-aid-criteria.md).

## Assess the voice as well as the words

Listen for intelligibility and accurate terms/numbers, natural pauses and
emphasis, a manageable pace while inspecting diagrams, and a consistent voice
across passages. Check clipped words, abrupt joins, excessive silence, uneven
levels and distracting artifacts. Q1's intended tone is conversational and
thoughtful, with gently varied emphasis and a natural British accent. Preserve
that brief rather than making the delivery theatrical to increase engagement.

Approval of the reference voice is not listening approval of every new passage.
Record which passages were listened to, which only received recognition checks,
and which pronunciation or delivery questions remain unresolved.

## Complete adapter and production evidence

These pinned Metadata systems sources implement the full Qwen workflow:

- [Production setup and limitations](https://github.com/snowch/metadata-book/blob/fac56101ce4f153f425d0150c302d1b5bb894910/video/qwen-production/README.md)
- [Generation, caching, unprompted ASR and estimated canonical alignment](https://github.com/snowch/metadata-book/blob/fac56101ce4f153f425d0150c302d1b5bb894910/video/qwen-production/synthesize.py)
- [Pronunciation excerpts and freshness check](https://github.com/snowch/metadata-book/blob/fac56101ce4f153f425d0150c302d1b5bb894910/video/audit_pronunciation.py)
- [Learning-aid rendering and explicit export/browser checks](https://github.com/snowch/metadata-book/tree/fac56101ce4f153f425d0150c302d1b5bb894910/video)
- [Model, reference and per-scene provenance](https://github.com/snowch/metadata-book/blob/fac56101ce4f153f425d0150c302d1b5bb894910/video/qwen-production/production-manifest.json)

They are chapter-specific reference implementations. Adapt the source, paths,
scene handlers and learning task for the new project; do not run all three book
chapters as though that produced a new video's content. This repository's Edge
example and its provider-boundary checks remain unchanged.
