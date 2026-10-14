import json
import os
import tempfile
import shutil
import app.models as models
import app.snippets as snippets
from app.main import create_app
from app.models import Proposal


_orig_dir = models.PROPOSALS_DIR
_orig_snippets_dir = snippets.SNIPPETS_DIR
_test_dir = None


def setup_function():
    global _test_dir
    _test_dir = tempfile.mkdtemp()
    models.PROPOSALS_DIR = _test_dir
    snippets.SNIPPETS_DIR = os.path.join(_test_dir, "snippets")


def teardown_function():
    global _test_dir
    models.PROPOSALS_DIR = _orig_dir
    snippets.SNIPPETS_DIR = _orig_snippets_dir
    if _test_dir and os.path.exists(_test_dir):
        shutil.rmtree(_test_dir)


def test_index_page():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Propongo" in resp.data


def test_new_proposal():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/new", follow_redirects=True)
        assert resp.status_code == 200


def test_create_and_load_proposal():
    proposal = Proposal(title="Test Proposal", client_name="Test Client")
    proposal.save()

    loaded = Proposal.load(proposal.id)
    assert loaded is not None
    assert loaded.title == "Test Proposal"
    assert loaded.client_name == "Test Client"


def test_list_proposals():
    p1 = Proposal(title="First")
    p1.save()
    p2 = Proposal(title="Second")
    p2.save()

    proposals = Proposal.list_all()
    assert len(proposals) >= 2


def test_delete_proposal():
    p = Proposal(title="Delete Me")
    p.save()
    assert Proposal.load(p.id) is not None

    Proposal.delete(p.id)
    assert Proposal.load(p.id) is None


def test_api_get_proposal():
    p = Proposal(title="API Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/api/proposal/{p.id}")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "API Test"


def test_api_put_proposal():
    p = Proposal(title="Original")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/proposal/{p.id}",
            json={"title": "Updated"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Original"


def test_api_put_updates_data_fields():
    p = Proposal(title="Data Test")
    p.client_name = "Old Client"
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/proposal/{p.id}",
            json={"client_name": "New Client", "title": "Should Not Change"},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["client_name"] == "New Client"
        assert data["title"] == "Data Test"


def test_api_delete_proposal():
    p = Proposal(title="Delete via API")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.delete(f"/api/proposal/{p.id}")
        assert resp.status_code == 200
        assert Proposal.load(p.id) is None


def test_api_add_task():
    p = Proposal(title="Task Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/task/{p.id}",
            json={"name": "Field Survey"},
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["name"] == "Field Survey"

        loaded = Proposal.load(p.id)
        assert len(loaded.tasks) == 1


def test_api_add_budget_item():
    p = Proposal(title="Budget Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/budget/{p.id}",
            json={"task_id": "t1", "name": "Travel", "cost_per_unit": 150, "units": 4},
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["cost_per_unit"] == 150
        assert data["units"] == 4


def test_api_add_budget_item_with_timing():
    p = Proposal(title="Budget Timing Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/budget/{p.id}",
            json={
                "task_id": "t1",
                "name": "Travel",
                "cost_per_unit": 150,
                "units": 4,
                "start_month": 3,
                "start_year": 2027,
                "duration_months": 6,
            },
            content_type="application/json",
        )
        assert resp.status_code == 201
        item_id = json.loads(resp.data)["id"]

        loaded = Proposal.load(p.id)
        assert loaded.budget_item_timings[item_id] == {
            "start_month": 3,
            "start_year": 2027,
            "duration_months": 6,
        }

        resp = client.put(
            f"/api/budget/{p.id}/{item_id}",
            json={"start_month": "", "start_year": ""},
            content_type="application/json",
        )
        assert resp.status_code == 200
        loaded = Proposal.load(p.id)
        assert item_id not in loaded.budget_item_timings


def test_budget_page_shows_by_year_table():
    p = Proposal(title="By Year Test")
    p.tasks = [{"id": "t1", "name": "Phase 1"}]
    p.budget_items = [
        {"id": "b1", "task_id": "t1", "name": "Year One Item", "cost_per_unit": 12000, "units": 1},
        {"id": "b2", "task_id": "t1", "name": "Split Item", "cost_per_unit": 24000, "units": 1},
    ]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 12},
        "b2": {"start_month": 1, "start_year": 2026, "duration_months": 24},
    }
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/budget/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Budget by Year" in html
        # b1 all in 2026 (12000), b2 split 12000/2026 + 12000/2027
        assert "$24,000" in html
        assert "$12,000" in html


def test_budget_total():
    p = Proposal(title="Total Test")
    p.budget_items = [
        {"name": "Item A", "cost_per_unit": 100, "units": 2},
        {"name": "Item B", "cost_per_unit": 50, "units": 3},
    ]
    assert p.total_budget == 350


def test_editor_route():
    p = Proposal(title="Editor Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/editor/{p.id}")
        assert resp.status_code == 200
        assert b"Editor Test" in resp.data


def test_map_tab_renders_iframe():
    p = Proposal(title="Map Test")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "geolibre-embed" in html
        assert "web.geolibre.app" in html
        # Default context layer is basemap-only (no data/url params).
        assert "data=" not in html
        assert "url=" not in html


def test_map_tab_data_url():
    p = Proposal(title="Map Data URL")
    p.map_config = {"mode": "data_url", "url": "https://data.example.org/area.geojson"}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "data=https%3A%2F%2Fdata.example.org%2Farea.geojson" in html


def test_map_tab_project_url():
    p = Proposal(title="Map Project URL")
    p.map_config = {"mode": "project_url", "url": "https://share.geolibre.app/giswqs/demo.geolibre.json"}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "url=https%3A%2F%2Fshare.geolibre.app%2Fgiswqs%2Fdemo.geolibre.json" in html


def test_map_tab_project_url_without_extension():
    p = Proposal(title="Map Project URL No Ext")
    p.map_config = {"mode": "project_url", "url": "https://share.geolibre.app/giswqs/demo"}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        # Extension-less share link is normalized to the raw project file.
        assert "url=https%3A%2F%2Fshare.geolibre.app%2Fgiswqs%2Fdemo.geolibre.json" in html


def test_map_page_shows_geolibre_citation():
    p = Proposal(title="Map Citation")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "10.5281/zenodo.20785400" in html
        assert "Wu, Q." in html


def test_map_tab_missing_proposal():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/map/does-not-exist")
        assert resp.status_code == 404


def test_map_config_persists_via_put():
    p = Proposal(title="Map Persist")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/proposal/{p.id}",
            json={"map_config": {"mode": "data_url", "url": "https://data.example.org/x.pmtiles"}},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["map_config"]["mode"] == "data_url"

    loaded = Proposal.load(p.id)
    assert loaded.map_config["url"] == "https://data.example.org/x.pmtiles"


def test_map_config_show_in_preview_persists_via_put():
    p = Proposal(title="Map Persist Preview")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/proposal/{p.id}",
            json={"map_config": {"mode": "basemap", "show_in_preview": True, "image_url": "https://img.example.org/map.png"}},
            content_type="application/json",
        )
        assert resp.status_code == 200

    loaded = Proposal.load(p.id)
    assert loaded.map_config["show_in_preview"] is True
    assert loaded.map_config["image_url"] == "https://img.example.org/map.png"


def test_map_page_renders_checkbox_checked_when_enabled():
    p = Proposal(title="Map Checkbox")
    p.map_config = {"mode": "basemap", "show_in_preview": True}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/map/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        input_line = [l for l in html.splitlines() if 'id="map-show-in-preview"' in l][0]
        assert 'checked' in input_line
        assert 'autosaveMapConfig' in input_line


def test_preview_omits_map_when_not_enabled():
    p = Proposal(title="Preview No Map")
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/preview/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "geolibre-embed" not in html
        assert "Project Map" not in html


def test_preview_shows_embed_when_enabled():
    p = Proposal(title="Preview Embed Map")
    p.map_config = {"mode": "project_url", "url": "https://share.geolibre.app/giswqs/demo", "show_in_preview": True}
    p.save()
    p.project_summary = "Summary text"
    p.scope = "Scope text"
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/preview/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "url=https%3A%2F%2Fshare.geolibre.app%2Fgiswqs%2Fdemo.geolibre.json" in html
        assert "preview-map-iframe" in html
        assert "preview-map-print" in html
        summary_idx = html.index("Project Summary")
        map_idx = html.index("Project Map")
        scope_idx = html.index("Scope")
        assert summary_idx < map_idx < scope_idx


def test_preview_prefers_image_url_when_set():
    p = Proposal(title="Preview Image Map")
    p.map_config = {"mode": "basemap", "show_in_preview": True, "image_url": "https://img.example.org/map.png"}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/preview/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert '<img src="https://img.example.org/map.png"' in html
        assert "geolibre-embed" not in html


def test_snippets_endpoint_starts_empty():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/snippets")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["organization"] == []
        assert data["deliverables"] == []
        assert data["custom"] == []


# --- budget item timing (stored on the item, migrated from budget_item_timings) ---


def test_legacy_budget_item_timings_migrate_into_items():
    p = Proposal(title="Legacy Shape")
    p.tasks = [{"id": "t1", "name": "Phase 1"}]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item", "cost_per_unit": 10, "units": 2}]
    p.save()

    # Write the old parallel-dict shape straight to disk, bypassing the model.
    path = os.path.join(models.PROPOSALS_DIR, f"{p.id}.json")
    raw = json.load(open(path))
    raw["budget_item_timings"] = {
        "b1": {"start_month": 4, "start_year": 2027, "duration_months": 5, "lead_entity": "Acme"}
    }
    with open(path, "w") as f:
        json.dump(raw, f)

    loaded = Proposal.load(p.id)
    item = loaded.budget_items[0]
    assert item["start_month"] == 4
    assert item["start_year"] == 2027
    assert item["duration_months"] == 5
    assert item["lead_entity"] == "Acme"
    # The compatibility view still reports the same timing.
    assert loaded.budget_item_timings["b1"]["start_month"] == 4

    # ...but the legacy key is no longer written back out.
    loaded.save()
    assert "budget_item_timings" not in json.load(open(path))


def test_budget_item_update_accepts_schedule_fields():
    p = Proposal(title="Schedule Fields")
    p.tasks = [{"id": "t1", "name": "Phase 1"}]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item", "cost_per_unit": 10, "units": 2}]
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/budget/{p.id}/b1",
            json={
                "start_month": 2,
                "start_year": 2028,
                "duration_months": 9,
                "recurring": True,
                "recurring_interval": 6,
                "lead_entity": "Acme",
            },
            content_type="application/json",
        )
        assert resp.status_code == 200

    item = Proposal.load(p.id).budget_items[0]
    assert item["start_month"] == 2
    assert item["duration_months"] == 9
    assert item["recurring"] is True
    assert item["recurring_interval"] == 6
    assert item["lead_entity"] == "Acme"


def test_clearing_timing_leaves_item_unscheduled():
    from app.models import item_is_scheduled

    p = Proposal(title="Clearing")
    p.tasks = [{"id": "t1", "name": "Phase 1"}]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item", "cost_per_unit": 10, "units": 2}]
    p.budget_item_timings = {"b1": {"start_month": 3, "start_year": 2027, "duration_months": 4}}
    p.save()
    assert item_is_scheduled(Proposal.load(p.id).budget_items[0])

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.put(
            f"/api/budget/{p.id}/b1",
            json={"start_month": "", "start_year": ""},
            content_type="application/json",
        )
        assert resp.status_code == 200

    item = Proposal.load(p.id).budget_items[0]
    assert item_is_scheduled(item) is False
    assert "duration_months" not in item


def test_timeline_save_preserves_unsent_timing_and_actual_cost():
    """A timeline-tab save posts only the budget items it rendered.

    It must not wipe the scheduling of items it left out, nor the tracker's
    actual_cost figures.
    """
    p = Proposal(title="Partial Timeline Save")
    p.tasks = [{"id": "t1", "name": "Phase 1"}, {"id": "t2", "name": "Phase 2"}]
    p.budget_items = [
        {"id": "b1", "task_id": "t1", "name": "Shown", "cost_per_unit": 10, "units": 2},
        {"id": "b2", "task_id": "t2", "name": "Not shown", "cost_per_unit": 20, "units": 3},
    ]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2027, "duration_months": 3},
        "b2": {"start_month": 5, "start_year": 2027, "duration_months": 6},
    }
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        # The tracker records an actual cost against b2.
        resp = client.put(
            f"/api/tracker/{p.id}/budget/b2",
            json={"actual_cost": 55.0},
            content_type="application/json",
        )
        assert resp.status_code == 200

        # The timeline tab then saves, sending a timing entry for b1 only.
        resp = client.put(
            f"/api/proposal/{p.id}",
            json={
                "tasks": p.tasks,
                "budget_item_timings": {
                    "b1": {
                        "start_month": 1,
                        "start_year": 2027,
                        "duration_months": 3,
                        "recurring": True,
                        "recurring_interval": 4,
                    }
                },
            },
            content_type="application/json",
        )
        assert resp.status_code == 200

    items = {i["id"]: i for i in Proposal.load(p.id).budget_items}
    # b1 was updated, including the recurring fields.
    assert items["b1"]["recurring"] is True
    assert items["b1"]["recurring_interval"] == 4
    # b2's schedule survived even though the payload omitted it...
    assert items["b2"]["start_month"] == 5
    assert items["b2"]["duration_months"] == 6
    # ...as did the tracker's actual_cost.
    assert items["b2"]["actual_cost"] == 55.0


def test_save_as_does_not_share_budget_item_dicts():
    p = Proposal(title="Original")
    p.tasks = [{"id": "t1", "name": "Phase 1"}]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item", "cost_per_unit": 10, "units": 2}]
    p.budget_item_timings = {"b1": {"start_month": 1, "start_year": 2027, "duration_months": 3}}
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.post(
            f"/api/proposal/{p.id}/save-as",
            json={"title": "Copy"},
            content_type="application/json",
        )
        assert resp.status_code == 201
        copy_id = json.loads(resp.data)["id"]

    copy_item = Proposal.load(copy_id).budget_items[0]
    assert copy_item["start_month"] == 1

    # Rescheduling the copy must not reach back into the original.
    app = create_app()
    with app.test_client() as client:
        client.put(
            f"/api/budget/{copy_id}/b1",
            json={"start_month": 7, "start_year": 2029, "duration_months": 2},
            content_type="application/json",
        )

    assert Proposal.load(p.id).budget_items[0]["start_month"] == 1
