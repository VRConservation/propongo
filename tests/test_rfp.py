import json
import os
import tempfile
import shutil
import app.models as models
from app.main import create_app
from app.models import Proposal
from app import rfp


_orig_dir = models.PROPOSALS_DIR
_test_dir = None


def setup_function():
    global _test_dir
    _test_dir = tempfile.mkdtemp()
    models.PROPOSALS_DIR = _test_dir


def teardown_function():
    global _test_dir
    models.PROPOSALS_DIR = _orig_dir
    if _test_dir and os.path.exists(_test_dir):
        shutil.rmtree(_test_dir)


def _make_proposal():
    p = Proposal(title="RFP Test Proposal")
    p.save()
    return p


def test_load_cal_fire_template():
    template = rfp.load_template("cal-fire-wpb-2025")
    assert template is not None
    assert len(template["sections"]) == 13


def test_list_rfp_templates():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/api/rfp/templates")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        ids = [t["id"] for t in data]
        assert "cal-fire-wpb-2025" in ids
        tmpl = data[ids.index("cal-fire-wpb-2025")]
        assert tmpl["section_count"] == 13
        assert set(tmpl["tracks"]) == {"Business Development", "Workforce Development"}


def test_import_rfp_template_all():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/proposal/{p.id}/import-rfp",
            json={"template_id": "cal-fire-wpb-2025"},
        )
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result["added"] == 10  # shared titles across tracks are deduped
        assert result["skipped"] == 3

    loaded = Proposal.load(p.id)
    titles = {s["title"] for s in loaded.custom_sections}
    assert "Business Plan (15 pts)" in titles
    assert "Readiness (25 pts)" in titles
    assert "Project Background (10 pts)" in titles
    assert len(loaded.custom_sections) == 10
    assert [s["order"] for s in loaded.custom_sections] == list(range(10))

    bg = next(s for s in loaded.custom_sections if s["title"] == "Project Background (10 pts)")
    assert "RFP scoring criterion — 10 points" in bg["content"]
    assert "AB 32" in bg["content"]


def test_import_rfp_track_filter():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/proposal/{p.id}/import-rfp",
            json={"template_id": "cal-fire-wpb-2025", "track": "Business Development"},
        )
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result["added"] == 7

    loaded = Proposal.load(p.id)
    titles = {s["title"] for s in loaded.custom_sections}
    assert "Business Plan (15 pts)" in titles
    assert "Job Creation (15 pts)" not in titles


def test_import_rfp_idempotent():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/proposal/{p.id}/import-rfp",
            json={"template_id": "cal-fire-wpb-2025"},
        )
        assert json.loads(resp.data)["added"] == 10
        resp = client.post(
            f"/api/proposal/{p.id}/import-rfp",
            json={"template_id": "cal-fire-wpb-2025"},
        )
        result = json.loads(resp.data)
        assert result["added"] == 0
        assert result["skipped"] == 13

    loaded = Proposal.load(p.id)
    assert len(loaded.custom_sections) == 10


def test_import_rfp_tags_sections_with_rfp_source():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        client.post(
            f"/api/proposal/{p.id}/import-rfp",
            json={"template_id": "cal-fire-wpb-2025"},
        )

    loaded = Proposal.load(p.id)
    assert loaded.custom_sections
    for section in loaded.custom_sections:
        assert section["rfp_template_id"] == "cal-fire-wpb-2025"
        assert section["rfp_section_id"]


def test_apply_sections_skips_existing():
    p = _make_proposal()
    p.custom_sections = [
        {"id": "existing", "title": "Project Background (10 pts)", "content": "", "order": 0}
    ]
    p.save()
    sections = rfp.load_template("cal-fire-wpb-2025")["sections"]
    result = rfp.apply_sections(p, sections)
    assert result["added"] == 9
    assert result["skipped"] == 4  # 1 already present + 3 cross-track duplicates


def test_build_section_content_with_headers():
    content = rfp.build_section_content({
        "title": "Narrative",
        "points": 10,
        "requirements": [
            {"header": "Deliverables", "text": "List and describe deliverables."},
            {"header": "Goals", "text": "Project goals align with the program goals."},
            "A plain requirement",
        ],
    })
    assert "- **Deliverables:** List and describe deliverables." in content
    assert "- **Goals:** Project goals align with the program goals." in content
    assert "- A plain requirement" in content


def test_import_rfp_raw_sections():
    p = _make_proposal()
    payload = {
        "sections": [
            {
                "title": "Custom Criterion",
                "points": 5,
                "attachment": "Narrative attachment",
                "requirements": ["First requirement", "Second requirement"],
            }
        ]
    }
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(f"/api/proposal/{p.id}/import-rfp", json=payload)
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result["added"] == 1

    loaded = Proposal.load(p.id)
    assert loaded.custom_sections[0]["title"] == "Custom Criterion (5 pts)"
    assert "- First requirement" in loaded.custom_sections[0]["content"]
    assert "Narrative attachment" in loaded.custom_sections[0]["content"]


def test_import_rfp_invalid_template():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(f"/api/proposal/{p.id}/import-rfp", json={"template_id": "nope"})
        assert resp.status_code == 404


def test_import_rfp_proposal_not_found():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            "/api/proposal/does-not-exist/import-rfp",
            json={"template_id": "cal-fire-wpb-2025"},
        )
        assert resp.status_code == 404


def test_import_rfp_invalid_sections_payload():
    p = _make_proposal()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(f"/api/proposal/{p.id}/import-rfp", json={"sections": []})
        assert resp.status_code == 400
        resp = client.post(
            f"/api/proposal/{p.id}/import-rfp", json={"sections": [{"no_title": True}]}
        )
        assert resp.status_code == 400
