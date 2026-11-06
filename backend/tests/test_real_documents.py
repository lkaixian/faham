"""Batch regression: 8 statutory notices and 4 documented scam templates (tests/fixtures/real/suite.json).

Ground truth comes from the suite file. Notices must be read correctly and never flagged as scams;
scam templates must be flagged. Source citations: docs/OFFICIAL_SOURCES_AND_PDF_LINKS.md.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SUITE = json.loads((Path(__file__).parent / "fixtures" / "real" / "suite.json").read_text(encoding="utf-8"))
NOTICES = [d for d in SUITE if d["category"] == "genuine_statutory_notice"]
SCAMS = [d for d in SUITE if d["category"] == "documented_scam_template"]


def _run(doc):
    r = client.post("/api/analyze", json=doc["request_payload"])
    assert r.status_code == 200
    return r.json()


def test_suite_shape():
    assert len(NOTICES) == 8 and len(SCAMS) == 4


@pytest.mark.parametrize("doc", NOTICES, ids=lambda d: d["document_id"][:12])
def test_notice_fields_and_not_scam(doc):
    out, g = _run(doc), doc["ground_truth"]
    f = out["fields"]
    assert f["issuer"] == g["expected_issuer"]
    assert f["amount"] == g["expected_amount"]
    assert f["deadline"] == g["expected_deadline"]
    assert f["reference"] == g["expected_ref"]
    assert out["scam"]["verdict"] != "likely_scam"
    assert out["action"]["requires_approval"] is True


@pytest.mark.parametrize("doc", SCAMS, ids=lambda d: d["document_id"][:12])
def test_scam_template_flagged(doc):
    out = _run(doc)
    assert out["scam"]["verdict"] == "likely_scam"
    assert out["scam"]["genuine"] is False
