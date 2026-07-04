# Security policy

## Reporting a vulnerability

Please report security issues privately rather than in a public issue. Use
GitHub's [private vulnerability reporting](https://github.com/ChelseaKR/gtfs-scorecard/security/advisories/new)
on this repository. You will get an acknowledgement within a few days.

## Scope notes

- The CI action (`action.yml`) fetches and scores a GTFS feed from a URL you
  provide. It runs the MobilityData validator and the scorer over the
  downloaded data; it does not execute feed contents. Treat feed URLs in a
  workflow as you would any external input.
- The pipeline fetches agency feeds over HTTP with conservative connect/read
  timeouts and a download size cap, and guards against fetching internal or
  non-public addresses (see `pipeline/src/scorecard_pipeline/net.py`).
- The frontend reads only published JSON artifacts and escapes feed-sourced
  strings and URLs before rendering them.
