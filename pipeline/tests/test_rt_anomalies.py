"""Tests for realtime anomaly checks: ping-stop deviation and TripUpdate
timestamp anomalies (Mineta/Newmark GTFS-RT accuracy methodology)."""

from __future__ import annotations

from scorecard_pipeline.rt_drift import (
    PING_STOP_DEVIATION_METERS,
    StopPrediction,
    find_timestamp_anomalies,
    ping_stop_deviation_exceeded,
    ping_stop_deviation_meters,
)

# A stop near downtown Davis, CA.
STOP_LAT = 38.5449
STOP_LON = -121.7405


def _offset_lon(lat: float, meters: float) -> float:
    """East offset in degrees longitude for a given meters at this latitude."""
    import math

    return meters / (111_320.0 * math.cos(math.radians(lat)))


def test_vehicle_within_30m_is_ok() -> None:
    # About 15 m east of the stop.
    lon = STOP_LON + _offset_lon(STOP_LAT, 15.0)
    assert not ping_stop_deviation_exceeded(STOP_LAT, lon, STOP_LAT, STOP_LON)
    assert (
        ping_stop_deviation_meters(STOP_LAT, lon, STOP_LAT, STOP_LON) < PING_STOP_DEVIATION_METERS
    )


def test_vehicle_beyond_30m_is_flagged() -> None:
    # About 60 m east of the stop.
    lon = STOP_LON + _offset_lon(STOP_LAT, 60.0)
    assert ping_stop_deviation_exceeded(STOP_LAT, lon, STOP_LAT, STOP_LON)
    assert (
        ping_stop_deviation_meters(STOP_LAT, lon, STOP_LAT, STOP_LON) > PING_STOP_DEVIATION_METERS
    )


def test_exact_position_is_zero_meters() -> None:
    assert ping_stop_deviation_meters(STOP_LAT, STOP_LON, STOP_LAT, STOP_LON) == 0.0
    assert not ping_stop_deviation_exceeded(STOP_LAT, STOP_LON, STOP_LAT, STOP_LON)


def test_duplicate_timestamp_predictions_flagged() -> None:
    preds = [
        StopPrediction("S1", 1_000),
        StopPrediction("S1", 1_000),  # same stop, same time
        StopPrediction("S2", 1_200),
    ]
    result = find_timestamp_anomalies(preds, message_epoch=900)
    assert result.duplicate_timestamp_stops == 1
    assert result.past_dated_predictions == 0
    assert result.total == 1


def test_past_dated_prediction_flagged() -> None:
    preds = [
        StopPrediction("S1", 1_500),
        StopPrediction("S2", 800),  # before "now"
    ]
    result = find_timestamp_anomalies(preds, message_epoch=1_000)
    assert result.past_dated_predictions == 1
    assert result.duplicate_timestamp_stops == 0
    assert result.total == 1


def test_tuple_input_accepted() -> None:
    preds = [("S1", 1_200), ("S2", 1_300)]
    result = find_timestamp_anomalies(preds, message_epoch=1_000)
    assert result.total == 0


def test_clean_input_produces_no_anomalies() -> None:
    preds = [
        StopPrediction("S1", 1_100),
        StopPrediction("S2", 1_200),
        StopPrediction("S3", 1_300),
    ]
    result = find_timestamp_anomalies(preds, message_epoch=1_000)
    assert result.duplicate_timestamp_stops == 0
    assert result.past_dated_predictions == 0
    assert result.total == 0


def test_distinct_times_at_same_stop_not_flagged() -> None:
    # Two predictions for one stop with different times is not a duplicate.
    preds = [StopPrediction("S1", 1_100), StopPrediction("S1", 1_160)]
    result = find_timestamp_anomalies(preds, message_epoch=1_000)
    assert result.duplicate_timestamp_stops == 0
