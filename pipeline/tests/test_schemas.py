"""Machine-enforcement of the published data contracts (web/schemas/).

Every published document type has a JSON Schema, the schemas themselves are
valid Draft 2020-12, and publish() refuses to write an artifact that violates
the per-agency contract — so a shape change must ship with a schema update,
never reach consumers as a surprise.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from scorecard_pipeline.config import Agency, artifacts_dir
from scorecard_pipeline.fetch import FetchResult
from scorecard_pipeline.metrics import CategoryResult, Finding
from scorecard_pipeline.publish import (
    RESERVED_ARTIFACT_DIRS,
    build_artifact,
    publish,
    validate_artifact,
)
from scorecard_pipeline.score import build_scorecard

# The source checkout, not the SCORECARD_ROOT tmp dir the autouse fixture sets:
# the schemas and the real published outputs live here.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "web" / "schemas"
SCHEMA_PATHS = sorted(SCHEMA_DIR.glob("*.schema.json"))

AGENCY = Agency(
    id="unitrans",
    name="Unitrans",
    static_gtfs_url="https://example.org/gtfs.zip",
    license_note="test",
)
GENERATED_AT = dt.datetime(2026, 6, 11, 12, 0, tzinfo=dt.UTC)


def _load(path: Path) -> dict:  # type: ignore[type-arg]
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(_load(SCHEMA_DIR / schema_name))


def make_artifact(date: dt.date, agency: Agency = AGENCY) -> dict:  # type: ignore[type-arg]
    fetch = FetchResult(
        agency_id=agency.id,
        path=Path("/tmp/gtfs.zip"),
        url=agency.static_gtfs_url,
        fetched_date=date,
        sha256="abc123",
        size_bytes=1024,
        reused=False,
    )
    finding = Finding(
        code="expired_calendar",
        severity="WARNING",
        count=3,
        what="w",
        why="y",
        fix="f",
        effort="e",
        deduction=4.0,
    )
    card = build_scorecard(
        [CategoryResult(name="correctness", score=88.0, summary="s", findings=[finding])]
    )
    return build_artifact(agency, fetch, card, GENERATED_AT)


# ---------------------------------------------------------------------------
# The schemas themselves


@pytest.mark.parametrize("schema_path", SCHEMA_PATHS, ids=lambda p: p.name)
def test_every_published_schema_is_valid_draft_2020_12(schema_path: Path) -> None:
    Draft202012Validator.check_schema(_load(schema_path))


def test_a_schema_exists_for_every_published_document_type() -> None:
    names = {p.name for p in SCHEMA_PATHS}
    assert {"artifact.schema.json", "catalog.schema.json", "directory.schema.json"} <= names


# ---------------------------------------------------------------------------
# The per-agency artifact contract (artifact.schema.json)


def test_build_artifact_output_conforms_to_the_artifact_schema() -> None:
    validate_artifact(make_artifact(dt.date(2026, 6, 11)))


def test_artifact_with_every_optional_agency_field_conforms() -> None:
    agency = Agency(
        id="barrie",
        name="Barrie Transit",
        static_gtfs_url="https://example.org/g.zip",
        country="CA",
        state="CA",
        operating_note="Confirmed operating.",
        ntd_note="Shared regional feed.",
    )
    validate_artifact(make_artifact(dt.date(2026, 6, 11), agency=agency))


def test_validate_artifact_rejects_an_unknown_grade() -> None:
    artifact = make_artifact(dt.date(2026, 6, 11))
    artifact["overall"]["grade"] = "E"
    with pytest.raises(ValidationError, match="'E' is not one of"):
        validate_artifact(artifact)


def test_publish_refuses_an_artifact_with_an_undeclared_top_level_key() -> None:
    # additionalProperties: false at the top level is the enforcement point: a
    # new block cannot reach production without a schema update.
    artifact = make_artifact(dt.date(2026, 6, 11))
    artifact["surprise_block"] = {"anything": True}
    with pytest.raises(ValidationError, match="surprise_block"):
        publish(artifact)
    # Nothing was written for the rejected artifact.
    assert not (artifacts_dir() / AGENCY.id).exists()


def test_publish_refuses_an_artifact_missing_feed_provenance() -> None:
    artifact = make_artifact(dt.date(2026, 6, 11))
    del artifact["feed"]["sha256"]
    with pytest.raises(ValidationError, match="sha256"):
        publish(artifact)


def test_a_measured_category_must_carry_score_findings_and_details() -> None:
    artifact = make_artifact(dt.date(2026, 6, 11))
    del artifact["categories"]["correctness"]["details"]
    with pytest.raises(ValidationError, match="details"):
        validate_artifact(artifact)


# ---------------------------------------------------------------------------
# Real published outputs validate against the published schemas


def _published_agency_artifacts() -> list[Path]:
    root = REPO_ROOT / "data" / "artifacts"
    if not root.exists():
        return []
    return [
        p for p in sorted(root.glob("*/latest.json")) if p.parent.name not in RESERVED_ARTIFACT_DIRS
    ]


def test_every_published_agency_artifact_conforms() -> None:
    paths = _published_agency_artifacts()
    if not paths:
        pytest.skip("no published artifacts in this checkout")
    validator = _validator("artifact.schema.json")
    bad: dict[str, str] = {}
    for path in paths:
        error = next(iter(validator.iter_errors(_load(path))), None)
        if error is not None:
            bad[path.parent.name] = f"{error.json_path}: {error.message}"
    assert not bad, f"{len(bad)} published artifacts violate the schema: {bad}"


def test_golden_site_agency_artifacts_conform() -> None:
    root = REPO_ROOT / "pipeline" / "tests" / "fixtures" / "golden_site" / "data" / "artifacts"
    validator = _validator("artifact.schema.json")
    paths = [
        p for p in sorted(root.glob("*/latest.json")) if p.parent.name not in RESERVED_ARTIFACT_DIRS
    ]
    assert paths, "golden_site fixture has no agency artifacts"
    for path in paths:
        validator.validate(_load(path))


@pytest.mark.parametrize(
    "relative",
    [
        "web/catalog.json",
        "pipeline/tests/goldens/catalog.json",
        "pipeline/tests/fixtures/golden_site/web/catalog.json",
    ],
)
def test_published_catalog_conforms_to_its_schema(relative: str) -> None:
    path = REPO_ROOT / relative
    if not path.exists():
        pytest.skip(f"{relative} not in this checkout")
    _validator("catalog.schema.json").validate(_load(path))


@pytest.mark.parametrize(
    "relative",
    [
        "data/artifacts/directory.json",
        "pipeline/tests/fixtures/golden_site/data/artifacts/directory.json",
    ],
)
def test_published_directory_conforms_to_its_schema(relative: str) -> None:
    path = REPO_ROOT / relative
    if not path.exists():
        pytest.skip(f"{relative} not in this checkout")
    _validator("directory.schema.json").validate(_load(path))
