import json
import os
import shutil
import tempfile

import app.models as models
import app.snippets as snippets
from app.main import create_app


_orig_proposals_dir = models.PROPOSALS_DIR
_orig_templates_dir = models.TEMPLATES_DIR
_orig_snippets_dir = snippets.SNIPPETS_DIR
_orig_env = None
_test_dir = None


def setup_function():
    global _orig_env, _test_dir
    _orig_env = dict(os.environ)
    _test_dir = tempfile.mkdtemp()
    models.PROPOSALS_DIR = os.path.join(_test_dir, "proposals")
    models.TEMPLATES_DIR = os.path.join(_test_dir, "templates")
    snippets.SNIPPETS_DIR = os.path.join(_test_dir, "snippets")


def teardown_function():
    global _orig_env, _test_dir
    models.PROPOSALS_DIR = _orig_proposals_dir
    models.TEMPLATES_DIR = _orig_templates_dir
    snippets.SNIPPETS_DIR = _orig_snippets_dir
    os.environ.clear()
    os.environ.update(_orig_env)
    _orig_env = None
    if _test_dir and os.path.exists(_test_dir):
        shutil.rmtree(_test_dir)
    _test_dir = None


def _client():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _custom_path(snippet_id):
    return os.path.join(snippets.SNIPPETS_DIR, "custom", f"{snippet_id}.json")


def test_get_snippets_tags_storage_source():
    client = _client()
    client.post("/snippets/organization", json={"title": "Org", "content": "..."} )
    client.post("/snippets/custom", json={"title": "Mine", "content": "..."})

    data = client.get("/snippets").get_json()
    assert [s["source"] for s in data["organization"]] == ["organization"]
    assert data["deliverables"] == []
    assert [s["source"] for s in data["custom"]] == ["custom"]


def test_add_custom_snippet_with_explicit_category():
    client = _client()
    resp = client.post(
        "/snippets/custom",
        json={"title": "Team CV", "content": "Our team...", "category": "Team"},
    )
    assert resp.status_code == 201
    snippet = resp.get_json()
    assert snippet["category"] == "Team"

    with open(_custom_path(snippet["id"])) as f:
        assert json.load(f)["category"] == "Team"


def test_add_custom_snippet_defaults_to_custom_category():
    client = _client()
    resp = client.post("/snippets/custom", json={"title": "T", "content": "C"})
    assert resp.status_code == 201
    assert resp.get_json()["category"] == "custom"


def test_add_snippet_to_arbitrary_category_stores_in_custom():
    client = _client()
    resp = client.post(
        "/snippets/reports",
        json={"title": "Report Intro", "content": "Intro text"},
    )
    assert resp.status_code == 201
    snippet = resp.get_json()
    assert snippet["category"] == "reports"
    assert os.path.exists(_custom_path(snippet["id"]))

    data = client.get("/snippets").get_json()
    titles = [s["title"] for s in data["custom"]]
    assert "Report Intro" in titles


def test_legacy_stock_category_post_still_appends_to_file():
    client = _client()
    resp = client.post(
        "/snippets/deliverables",
        json={"title": "New Deliverable", "content": "..."},
    )
    assert resp.status_code == 201

    with open(os.path.join(snippets.SNIPPETS_DIR, "deliverables.json")) as f:
        stored = json.load(f)
    assert any(s["title"] == "New Deliverable" for s in stored)


def test_update_custom_snippet_fields():
    client = _client()
    created = client.post(
        "/snippets/custom", json={"title": "Old", "content": "Old body"}
    ).get_json()

    resp = client.put(
        f"/snippets/custom/{created['id']}",
        json={"title": "New Title", "content": "New body", "category": "Budget"},
    )
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["title"] == "New Title"
    assert updated["content"] == "New body"
    assert updated["category"] == "Budget"

    with open(_custom_path(created["id"])) as f:
        assert json.load(f)["category"] == "Budget"


def test_update_list_file_snippet_updates_in_place():
    client = _client()
    created = client.post(
        "/snippets/deliverables",
        json={"title": "Survey", "content": "Survey body", "id": "del-survey"},
    ).get_json()

    org_file = os.path.join(snippets.SNIPPETS_DIR, "deliverables.json")
    resp = client.put(
        f"/snippets/deliverables/{created['id']}",
        json={"title": "Survey (edited)", "category": "Fieldwork"},
    )
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["title"] == "Survey (edited)"
    assert updated["category"] == "Fieldwork"
    assert updated["content"] == "Survey body"  # untouched field preserved

    with open(org_file) as f:
        stored = json.load(f)
    match = [s for s in stored if s["id"] == created["id"]]
    assert len(match) == 1
    assert match[0]["title"] == "Survey (edited)"
    assert match[0]["category"] == "Fieldwork"
    assert "source" not in match[0]  # storage annotation never persisted


def test_update_missing_snippet_returns_404():
    client = _client()
    assert client.put(
        "/snippets/custom/doesnotexist", json={"title": "X"}
    ).status_code == 404
    assert client.put(
        "/snippets/organization/doesnotexist", json={"title": "X"}
    ).status_code == 404


def test_delete_uses_storage_source_not_display_category():
    client = _client()
    client.post(
        "/snippets/deliverables",
        json={"title": "GIS", "content": "...", "id": "del-gis"},
    )
    client.put(
        "/snippets/deliverables/del-gis",
        json={"category": "Relocated"},
    )

    data = client.get("/snippets").get_json()
    relocated = [s for s in data["custom"] if s.get("category") == "Relocated"]
    assert not relocated  # still lives in the deliverables file

    resp = client.delete("/snippets/deliverables/del-gis")
    assert resp.status_code == 200

    with open(os.path.join(snippets.SNIPPETS_DIR, "deliverables.json")) as f:
        stored = json.load(f)
    assert not any(s["id"] == "del-gis" for s in stored)


def test_empty_update_payload_rejected():
    client = _client()
    resp = client.put("/snippets/organization/org-about", json={})
    assert resp.status_code == 400
