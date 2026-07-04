"""Tests for cEMV (contactless payment) detection."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from scorecard_pipeline.cemv import detect_cemv


def _zip(tmp_path: Path, files: dict[str, str]) -> str:
    p = tmp_path / "feed.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, text in files.items():
            zf.writestr(name, text)
    p.write_bytes(buf.getvalue())
    return str(p)


def test_absent_column_reads_as_not_declared(tmp_path: Path) -> None:
    path = _zip(tmp_path, {"agency.txt": "agency_id,agency_name\nA,Alpha\n"})
    profile = detect_cemv(path)
    assert profile.declared is False
    assert profile.supported is False
    assert profile.to_details() == {"declared": False, "supported": False}


def test_declared_but_unsupported(tmp_path: Path) -> None:
    path = _zip(
        tmp_path,
        {"agency.txt": "agency_id,agency_name,cemv_support\nA,Alpha,2\n"},
    )
    profile = detect_cemv(path)
    assert profile.declared is True
    assert profile.supported is False


def test_supported_on_a_route(tmp_path: Path) -> None:
    path = _zip(
        tmp_path,
        {
            "agency.txt": "agency_id,agency_name\nA,Alpha\n",
            "routes.txt": "route_id,route_type,cemv_support\nR1,3,1\n",
        },
    )
    profile = detect_cemv(path)
    assert profile.declared is True
    assert profile.supported is True


def test_bad_zip_reads_as_not_declared(tmp_path: Path) -> None:
    p = tmp_path / "not-a-zip.zip"
    p.write_text("nope")
    assert detect_cemv(str(p)).declared is False
