# Fix: trips don't say where they're headed

Code: `scorecard_missing_headsigns`

## What this means

A trip's destination comes from `trip_headsign` in `trips.txt` (or
`stop_headsign` in `stop_times.txt` for parts of a trip). Many of your trips
leave it blank, so the feed says which route a bus is on but not where it is
going.

## Why it matters

The headsign is the "to Downtown" or "to Transit Center" a rider reads on the
front of the bus and in the app. Without it, a trip planner shows "Route 5" with
no direction, and a rider at a stop served in both directions cannot tell which
bus is theirs. It is one of the most visible gaps in an otherwise working feed.

## How to fix it

- **Set `trip_headsign` on every trip** to the public destination, the same text
  riders see on the bus head sign (for example "Downtown via Main St").
- **In most scheduling tools** this is a field on the trip or the route pattern;
  set it once per pattern and every trip on that pattern inherits it.
- **Use `stop_headsign`** only where the destination changes partway through a
  trip (a branch or a short-turn); otherwise `trip_headsign` is enough.

## How long it usually takes

Usually one value per route pattern, so a short pass even for a large system.
