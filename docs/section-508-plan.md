# Plan: full Section 508 conformance

Working plan to take the GTFS Scorecard to a defensible **Section 508** conformance
claim. Section 508 (the Revised 508 Standards, 36 CFR Part 1194) adopts **WCAG 2.0
Level AA** as the technical standard for web and non-web electronic content, and adds
requirements WCAG itself does not cover. This plan tracks all of it.

## What 508 requires beyond "passes WCAG"

- **Ch. 5 — Software**: the single-page app and the CLI / GitHub Action.
- **Ch. 3 — Functional Performance Criteria**: usable without vision, without
  hearing, with limited reach or strength, etc. Verified by human/assistive-tech
  testing, not automation.
- **Ch. 6 — Support Documentation & Services**: accessible docs plus a way for
  users to report accessibility barriers.
- **A conformance report**: a VPAT / Accessibility Conformance Report mapping every
  applicable criterion to Supports / Partially Supports / Does Not Support.

The site already targets **WCAG 2.2 AAA** (`docs/accessibility.md`), exceeding the
508 web bar, and has a merge-blocking contrast gate. The remaining work is proof,
automation, the non-web surfaces, and the formal paperwork — not a redesign.

## Surfaces in scope (Phase 0 inventory)

| Surface | 508 chapter | Source |
| --- | --- | --- |
| Landing | Web (Ch. 5 / WCAG) | `web/index.html` |
| Single-page app | Web + Software | `web/app/`, `web/src/app.js` |
| Prerendered agency/section pages | Web | `render_site.py` |
| Printable call brief | Electronic document | `/agency/<id>/brief/` |
| National map (MapLibre) | Web (third-party) | `/map/` |
| Self-serve forms | Web (forms) | `web/submit.html`, `web/subscribe.html` |
| Score badges | Electronic content | SVG badges |
| CI Action HTML scorecard | Software output | `action.yml` `--html` |
| Data downloads | Electronic content | `/data/`, CSV/Parquet/JSON |
| Email digest | Electronic content | `notify.py` — plain text ✅ |
| Docs & README | Ch. 6 | `docs/`, `README.md` |

## Phases

- **Phase 0 — Scope & inventory.** The table above; becomes the VPAT scope statement.
- **Phase 1 — Automated gate.** axe-core (0 violations at WCAG 2.0 AA) + Lighthouse
  a11y (>= 95) in CI across representative rendered routes, including error / empty /
  loading / form states. Merge-blocking. *(Done — `.github/workflows/a11y.yml`; it caught and fixed real aria-prohibited-attr issues on the way in.)*
- **Phase 2 — Manual & AT verification.** A dated test log: NVDA+Firefox and
  VoiceOver+Safari walkthroughs of the core tasks, keyboard-only pass, 200% / 400%
  zoom + reflow, `forced-colors` / Windows High Contrast, reduced motion, target size.
  This is the functional-performance proof automation cannot give. *(Script ready —
  [accessibility-testing.md](accessibility-testing.md); awaiting a human AT pass to fill
  the results log.)*
- **Phase 3 — Close residuals to the AA bar.** Map canvas label + verified non-visual
  alternative; badge SVG accessible names; brief and data-download pages AT pass;
  form labels / instructions / error identification; confirm the Action's `--html`
  output meets AA.
- **Phase 4 — Conformance docs & statement.** `docs/vpat.md` (VPAT 2.5 Rev, 508
  edition); an on-site `/accessibility/` statement with target, date, scope, known
  limitations, and a feedback path; an accessibility issue template. *(Done — `docs/vpat.md`, the `/accessibility/` statement, and the issue template.)*
- **Phase 5 — Governance.** Gates blocking; PR/CONTRIBUTING a11y checklist; quarterly
  AT re-test; dated, versioned ACR/VPAT. *(Done — PR-template a11y checklist, the CONTRIBUTING accessibility rule, and the quarterly cadence + results log in docs/accessibility-testing.md.)*

## Definition of done

Every inventoried surface passes axe at AA and the manual matrix; a published
VPAT/ACR and accessibility statement with a feedback path; CI blocks a11y
regressions; known exceptions documented with rationale.

## Honest caveats

- 508's web bar is AA; the 2.2 AAA target exceeds it, so most Phase 3 items are
  verification, not new work.
- "Fully compliant" is a maintained claim, not a one-time state (Phase 5).
- The screen-reader functional-performance pass is best run by a human/AT user; this
  repo can script it and record results but cannot substitute for a real AT session.
- This is an engineering conformance plan, not a legal certification.
