## What and why

<!-- A sentence or two on the change and the motivation. Link any issue. -->

## Checks

- [ ] Pipeline gates pass: `cd pipeline && uv run pytest && uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src`
- [ ] Findings and UI copy frame issues as fixes, in plain language
- [ ] Accessibility (any web/HTML change): the `Accessibility` axe gate and the contrast gate pass; a new page/route is added to `.pa11yci.json`; keyboard-operable with visible focus, correct labels/roles, no colour-only meaning, respects reduced motion
- [ ] If a primary task changed (nav, forms, scorecard, map, theme): the manual AT pass in [docs/accessibility-testing.md](docs/accessibility-testing.md) was re-run and its log updated
