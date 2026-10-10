"""Shared helpers for the script contract: loading, lexicon, tokenisation.

A line has two texts. `text` is what reviewers approve, the gate checks and the
captions display. `say` is `text` with the project lexicon applied, and is what
the voice engine receives. The lexicon is applied token for token, so word
positions stay one-to-one and timings found against `say` map back to `text`.
"""
import hashlib
import json
import re

import yaml

TAG_RE = re.compile(r"<[^<>\n]{1,40}>")  # inline vocal tags such as <chuckle>
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-\.]*[A-Za-z0-9]|[A-Za-z0-9]")


def load_script(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def scene_by_id(script, scene_id):
    for scene in script["scenes"]:
        if scene["id"] == scene_id:
            return scene
    raise SystemExit(f"no scene with id {scene_id!r}")


def strip_tags(text):
    return re.sub(r"\s{2,}", " ", TAG_RE.sub("", text)).strip()


def apply_lexicon(text, lexicon):
    """Replace whole tokens that appear in the lexicon; keep everything else."""
    return WORD_RE.sub(lambda m: lexicon.get(m.group(0), m.group(0)), text)


def display_text(text, lexicon):
    """Caption text: tags removed, shouted emphasis normalised, lexicon keys kept."""
    t = strip_tags(text)
    out, last = [], 0
    for m in WORD_RE.finditer(t):
        w = m.group(0)
        if w in lexicon or len(w) < 2 or not w.isalpha() or not w.isupper():
            continue
        before = t[:m.start()].rstrip()
        sentence_start = not before or before[-1] in ".!?"
        repl = w.capitalize() if sentence_start else w.lower()
        out.append(t[last:m.start()] + repl)
        last = m.end()
    out.append(t[last:])
    return "".join(out)


def tokens(text):
    return WORD_RE.findall(text)


def norm(tok):
    return re.sub(r"[^a-z0-9]", "", tok.lower())


def line_say(line, lexicon):
    return apply_lexicon(line["text"], lexicon)


def line_display(line, lexicon):
    return display_text(line["text"], lexicon)


def content_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:10]
