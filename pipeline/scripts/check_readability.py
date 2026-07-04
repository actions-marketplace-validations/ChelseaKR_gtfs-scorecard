#!/usr/bin/env python3
"""Plain-language readability gate for the curated notice translations.

The product's promise is that every curated finding reads as plain language a
non-developer transit manager can act on. This asserts that promise mechanically
for every ``what``/``why``/``fix`` string in ``notices.TRANSLATIONS``, the same
shape as the contrast gate: average sentence length must stay under
MAX_AVG_SENTENCE_WORDS, and a syllable-based Flesch reading-ease estimate must
stay above MIN_FLESCH. Pure Python, no dependencies. Run from pipeline/:

    uv run python scripts/check_readability.py

Effort hints are excluded: they are fragments ("One setting."), not prose. The
thresholds gate regressions in curated text; they do not measure the generic
fallback, which the coverage metric on /problems/ tracks instead.
"""

from __future__ import annotations

import re
import sys

from scorecard_pipeline.notices import TRANSLATIONS

# Plain-language bars. 22 words/sentence is the upper edge of "easy to follow"
# in most plain-writing guidance; Flesch 50 is the floor of "fairly difficult"
# (10th-12th grade), a lenient floor that still catches dense, clause-stacked
# rewrites. Tighten these as the corpus improves; never loosen them to admit
# one hard string — rewrite the string.
MAX_AVG_SENTENCE_WORDS = 22.0
MIN_FLESCH = 50.0

_WORD_RE = re.compile(r"[A-Za-z]+")
# Sentence breaks: terminal punctuation followed by whitespace or end-of-text.
# "feed_info.txt" never splits (no space after the dot); "e.g. ..." does, which
# only shortens the measured sentences — an acceptable, conservative error.
_SENTENCE_RE = re.compile(r"[.!?]+(?:\s+|$)")


def words(text: str) -> list[str]:
    """Alphabetic word tokens; identifiers like feed_info.txt split into parts."""
    return _WORD_RE.findall(text)


def sentences(text: str) -> list[str]:
    """Non-empty sentences, split on terminal punctuation before whitespace."""
    return [s for s in (p.strip() for p in _SENTENCE_RE.split(text)) if s]


def syllables(word: str) -> int:
    """Heuristic syllable count: vowel groups, minus a common silent final e."""
    w = word.lower()
    groups = len(re.findall(r"[aeiouy]+", w))
    if groups > 1 and w.endswith("e") and not w.endswith(("le", "ee", "ye")):
        groups -= 1
    return max(1, groups)


def avg_sentence_words(text: str) -> float:
    """Mean words per sentence; 0.0 for empty text."""
    sents = sentences(text)
    if not sents:
        return 0.0
    return sum(len(words(s)) for s in sents) / len(sents)


def flesch(text: str) -> float:
    """Flesch reading-ease estimate from the heuristic syllable counts.

    Higher is easier; 100.0 for empty text so a blank string never fails the
    floor (emptiness is a curation problem, not a readability one).
    """
    ws = words(text)
    if not ws:
        return 100.0
    sents = sentences(text) or [text]
    syl = sum(syllables(w) for w in ws)
    return 206.835 - 1.015 * (len(ws) / len(sents)) - 84.6 * (syl / len(ws))


def check_text(label: str, text: str) -> list[str]:
    """Per-string diagnostics for any threshold the text misses; empty = pass."""
    fails: list[str] = []
    avg = avg_sentence_words(text)
    if avg > MAX_AVG_SENTENCE_WORDS:
        fails.append(
            f"{label}: average sentence length {avg:.1f} words "
            f"(cap {MAX_AVG_SENTENCE_WORDS:.0f}) — split or shorten the sentences"
        )
    ease = flesch(text)
    if ease < MIN_FLESCH:
        fails.append(
            f"{label}: Flesch reading ease {ease:.1f} "
            f"(floor {MIN_FLESCH:.0f}) — use shorter, more common words"
        )
    return fails


def main() -> int:
    fails: list[str] = []
    for code in sorted(TRANSLATIONS):
        tr = TRANSLATIONS[code]
        for field in ("what", "why", "fix"):
            text: str = getattr(tr, field)
            label = f"{code}.{field}"
            string_fails = check_text(label, text)
            ok = not string_fails
            print(
                f"{'OK ' if ok else 'FAIL'} flesch {flesch(text):6.1f}  "
                f"avg-words {avg_sentence_words(text):5.1f}  {label}"
            )
            fails.extend(string_fails)
    print()
    if fails:
        print(f"{len(fails)} FAILURES:")
        for f in fails:
            print("  -", f)
        return 1
    print(
        f"All {len(TRANSLATIONS)} curated translations clear the plain-language "
        f"bars (avg sentence <= {MAX_AVG_SENTENCE_WORDS:.0f} words, "
        f"Flesch >= {MIN_FLESCH:.0f})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
