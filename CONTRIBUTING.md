# Contributing

Thanks for helping improve the GTFS Scorecard.

## Add or fix an agency's feed

The most common contribution is adding an agency or correcting a feed URL. That
path is documented end to end in [docs/add-your-agency.md](docs/add-your-agency.md):
add an entry to `agencies.yaml` and open a pull request. You can also use the
self-serve form at [gtfsscorecard.org](https://gtfsscorecard.org/submit.html).

## Develop on the pipeline

The scorer lives in `pipeline/` (Python 3.11+, [uv](https://docs.astral.sh/uv/),
and Java 17 for the validator). Before opening a pull request, run the same
checks CI runs:

```sh
cd pipeline
uv run pytest && uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src
```

The frontend is in `web/` (vanilla JS, no build step) and reads the published
JSON artifacts. Keep scoring and other logic in the pipeline so the frontend
stays a thin renderer of precomputed JSON.

## Conventions

- Conventional commits, small and focused.
- Findings are framed as fixes, never as failures; plain practitioner language.
- Accessibility is non-negotiable: the site targets WCAG 2.2 AAA and meets Section 508.
  The `Accessibility` axe gate and the contrast gate are merge-blocking; see the
  [conformance report](docs/accessibility.md), the [VPAT](docs/vpat.md), and the manual
  [test script](docs/accessibility-testing.md).

The full project guide is in [CLAUDE.md](CLAUDE.md), and design decisions are
recorded as ADRs under [docs/decisions/](docs/decisions/).
