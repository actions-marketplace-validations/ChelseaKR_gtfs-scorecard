# Mutation testing (advisory)

Line and branch coverage prove a line ran. They do not prove a test would notice
if that line were wrong. Mutation testing checks the second thing: it changes the
code in small ways (a `>` becomes `>=`, a returned value becomes `None`, a string
literal is altered) and reruns the tests. A mutant that the tests still pass is
said to have "survived", and it marks an assertion the suite is missing.

This repo applies mutation testing to the scoring math in
`pipeline/src/scorecard_pipeline/`: `score.py` (the grade ladder and the
fix-priority tiers), `metrics.py` (the correctness deduction arithmetic and the
freshness slope), and `rt.py` (the realtime component weighting). A silent bug
in any of them mis-grades an agency or reorders the "top 3 things to fix".
Coverage of these modules is already high, which makes mutation score the
useful next signal. The invariant properties in `tests/test_properties.py` and
the frozen corpus in `tests/test_score_corpus.py` are part of the kill signal,
so a mutant has to get past the invariants as well as the examples.

Per [CODE-QUALITY-STANDARD.md](standards/CODE-QUALITY-STANDARD.md) §10 this is a
**REVIEW-GATE, not a merge gate**: run time makes it a poor per-PR blocker, and a
surviving mutant is often an equivalent one that needs a human to judge. It runs
weekly and on demand, never on a pull request, and it never blocks a merge.

## How to run it

```
make mutation            # run mutmut on the scoring modules, then print the results
make mutation-results    # reprint the last run without rerunning
```

Both run inside `pipeline/`. The scope and test command live in
`pipeline/pyproject.toml` under `[tool.mutmut]`: it mutates `score.py`,
`metrics.py`, and `rt.py`, and uses the unit tests for those modules plus the
property and corpus tests as the kill signal. A full run takes about a minute.

For a clean-cache baseline, delete the working copy first:

```
cd pipeline && rm -rf mutants && uv run mutmut run
```

`mutmut show <mutant-id>` prints the diff for one mutant, for example
`uv run mutmut show scorecard_pipeline.score.x__fix_tier__mutmut_7`.

The `mutants/` working copy, the caches, and the per-run report files are all
gitignored. The committed artifact is this document.

## Baseline

Measured on 106 mutants of `score.py`, using `tests/test_score.py`.

| Run | Killed | Survived | Score |
|-----|--------|----------|-------|
| Initial (the pre-existing suite) | 62 | 44 | 58.5% |
| After adding four assertion tests | 70 | 36 | 66.0% |

The target for a core safety module is 70% killed. The four tests below closed
the highest-value gaps; the remaining survivors are triaged as accepted (see
"Remaining survivors").

### Widened scope (2026-07-02)

The scope now also covers `metrics.py` and `rt.py`. First measurement: 1484
mutants across the three modules, 824 killed, 660 survived (55.5%). The new
survivors concentrate in two places that were expected and are acceptable for
an advisory gate: the impure fetch plumbing in `rt.py` (`fetch_sample`,
`capture_window`, protobuf parsing) that no unit test exercises end to end,
and the prose of summaries, `what`/`why`/`fix` strings, and details dicts in
both modules, which the tests deliberately do not pin word for word. The
arithmetic itself (deduction constants, tier thresholds, the freshness slope,
the realtime component weights) is guarded by the invariant and corpus tests.
Triage new survivors outside those two groups when the weekly run flags them.

## Notable survivors the coverage tests missed

These mutants survived the original 100%-coverage suite. Each is a real gap: the
line ran in a test, but no assertion pinned its behaviour. Tests added in
`tests/test_score.py` now kill them.

1. **The letter grade was never asserted end to end.** Mutating
   `grade=letter_grade(overall)` to `grade=None` in `build_scorecard` survived.
   `letter_grade()` was tested in isolation and `overall_score` was checked, but
   nothing asserted that a built `Scorecard` carries the grade for its own score.
   Killed by `test_build_scorecard_sets_the_letter_grade`.

2. **A zero-point note could have been offered as a fix.** Mutating the top-fix
   filter `f.deduction > 0` to `f.deduction >= 0` survived. The code comment
   promises a zero-deduction note is never surfaced as something to fix first, but
   no test mixed one in to confirm it. Killed by
   `test_zero_deduction_finding_is_never_a_top_fix`.

3. **The severity tiers rode on point ordering, not the severity check.**
   Mutating the `"ERROR"` literal in `_fix_tier`, and mutating the WARNING branch
   (`==` to `!=`, and its tier value), all survived. The existing tier tests used
   findings whose point deductions already matched the intended order, so a
   severity that was not recognized still sorted correctly by points. Killed by
   `test_error_severity_outranks_a_heavier_lower_tier_fix` and
   `test_warning_outranks_a_heavier_informational_fix`, which give the
   higher-tier finding a smaller deduction so only the tier can explain the order.

## Remaining survivors (accepted)

36 mutants survive the current suite. They are left surviving on purpose.

- **`methodology()` metadata (29).** These mutate dict keys and prose strings in
  the published `scoring.json` description. The load-bearing values there (weights,
  grade bands, severity deductions, count-multiplier tiers) are pinned by
  `test_methodology_exposes_weights_bands_and_deductions`. Asserting every key and
  sentence would test documentation text, which is brittle and low value.

- **`ValueError` message text in `build_scorecard` (6).** These mutate the wording
  of the two input-validation errors. The tests assert that the error is raised
  under the right condition, not its exact wording. The wording is an internal
  diagnostic, not user-facing copy.

- **One equivalent mutant in `_fix_tier` (1).** Changing the lowest tier's
  `return 2` to `return 3` survives because nothing compares a tier to a literal
  and it is already the least-urgent bucket, so every ordering is preserved. There
  is no behaviour to assert.

Re-triage this list when `score.py` changes. A new survivor outside these three
groups is a missing assertion, not noise.
