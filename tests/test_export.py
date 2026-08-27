import os
import tempfile
import shutil
import app.models as models
from app.main import create_app
from app.models import Proposal


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


def test_export_html():
    p = Proposal(title="Export Test", client_name="Client Co")
    p.tasks = [{"name": "Task 1", "description": "Do stuff"}]
    p.budget_items = [{"name": "Item 1", "cost_per_unit": 100, "units": 2}]
    p.qualifications = "We are qualified."
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/html/{p.id}")
        assert resp.status_code == 200


def test_export_pdf():
    p = Proposal(title="PDF Export Test")
    p.tasks = [{"name": "Task A", "description": "Description A"}]
    p.budget_items = [{"name": "Budget A", "cost_per_unit": 200, "units": 1}]
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/pdf/{p.id}")
        assert resp.status_code == 200


def test_export_timeline_png():
    import io
    from PIL import Image

    p = Proposal(title="Timeline PNG Test")
    p.tasks = [
        {"id": "t1", "name": "Phase 1", "start_month": 1, "start_year": 2026, "duration_months": 3},
    ]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item A", "cost_per_unit": 100, "units": 2}]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 3},
    }
    p.start_date = "2026-01-01"
    p.end_date = "2026-03-31"
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/timeline/png/{p.id}")
        assert resp.status_code == 200
        assert resp.mimetype == "image/png"

        img = Image.open(io.BytesIO(resp.data))
        assert img.format == "PNG"
        assert img.width > 0 and img.height > 0


def test_export_markdown():
    p = Proposal(title="Markdown Export Test")
    p.project_summary = "Strong summary."
    p.map_config = {
        "mode": "project_url",
        "url": "https://share.geolibre.app/vinny-raster/sample-11",
        "show_in_preview": True,
        "caption": "Sample project map",
    }
    p.tasks = [
        {"id": "t1", "name": "Phase 1", "start_month": 1, "start_year": 2026, "duration_months": 3},
    ]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item A", "cost_per_unit": 100, "units": 2}]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 3},
    }
    p.start_date = "2026-01-01"
    p.end_date = "2026-03-31"
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/markdown/{p.id}")
        assert resp.status_code == 200
        assert resp.mimetype == "text/markdown"
        body = resp.data.decode()
        assert "Markdown Export Test" in body
        assert "Project Summary" in body
        assert "Strong summary." in body
        assert "share.geolibre.app/vinny-raster/sample-11" in body


def test_export_markdown_share_link_extension_stripped():
    p = Proposal(title="Share Link Test")
    p.map_config = {
        "mode": "project_url",
        "url": "https://share.geolibre.app/vinny-raster/sample-11.geolibre.json",
        "show_in_preview": True,
    }
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/markdown/{p.id}")
        body = resp.data.decode()
        assert "share.geolibre.app/vinny-raster/sample-11" in body
        assert ".geolibre.json" not in body


def test_export_tracker_markdown():
    p = Proposal(title="Tracker Markdown Export Test")
    p.tasks = [{"id": "t1", "name": "Fieldwork", "status": "in_progress", "progress_pct": 40}]
    p.budget_items = [{"id": "b1", "task_id": "t1", "name": "Item A", "cost_per_unit": 100, "units": 1}]
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/export/tracker/markdown/{p.id}")
        assert resp.status_code == 200
        assert resp.mimetype == "text/markdown"
        assert "Tracker Markdown Export Test" in resp.data.decode()


def test_export_markdown_missing_proposal():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/export/markdown/nonexistent")
        assert resp.status_code == 404


def test_export_missing_proposal():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get("/export/pdf/nonexistent")
        assert resp.status_code == 404

        resp = client.get("/export/html/nonexistent")
        assert resp.status_code == 404


def test_preview_route():
    p = Proposal(title="Preview Test")
    p.tasks = [{"name": "Review", "description": "Review deliverables"}]
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/preview/{p.id}")
        assert resp.status_code == 200
        assert b"Proposal Preview" in resp.data


def test_build_budget_by_year_single_year():
    from app.utils import build_budget_by_year

    p = Proposal()
    p.budget_items = [{"id": "b1", "name": "Item", "cost_per_unit": 12000, "units": 1}]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 12},
    }

    result = build_budget_by_year(p)
    assert result["years"] == [{"year": 2026, "amount": 12000.0}]
    assert result["total_scheduled"] == 12000.0
    assert result["unscheduled"] == []


def test_build_budget_by_year_spans_years():
    from app.utils import build_budget_by_year

    p = Proposal()
    p.budget_items = [{"id": "b1", "name": "Item", "cost_per_unit": 24000, "units": 1}]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 24},
    }

    result = build_budget_by_year(p)
    assert result["years"] == [
        {"year": 2026, "amount": 12000.0},
        {"year": 2027, "amount": 12000.0},
    ]


def test_build_budget_by_year_unscheduled():
    from app.utils import build_budget_by_year

    p = Proposal()
    p.budget_items = [
        {"id": "b1", "name": "Scheduled", "cost_per_unit": 1000, "units": 1},
        {"id": "b2", "name": "No Dates", "cost_per_unit": 500, "units": 2},
    ]
    p.budget_item_timings = {
        "b1": {"start_month": 6, "start_year": 2026, "duration_months": 1},
    }

    result = build_budget_by_year(p)
    assert result["years"] == [{"year": 2026, "amount": 1000.0}]
    assert result["unscheduled"] == [{"name": "No Dates", "amount": 1000.0}]
    assert result["total_unscheduled"] == 1000.0



def test_preview_timeline_expands_task_bars():
    import re
    p = Proposal(title="Timeline Expand Test")
    p.tasks = [
        {"id": "t1", "name": "Phase 1", "start_month": 1, "start_year": 2026, "duration_months": 3},
    ]
    p.budget_items = [
        {"id": "b1", "task_id": "t1", "name": "Early Item", "cost_per_unit": 100, "units": 1},
        {"id": "b2", "task_id": "t1", "name": "Late Item", "cost_per_unit": 200, "units": 1},
    ]
    p.budget_item_timings = {
        "b1": {"start_month": 1, "start_year": 2026, "duration_months": 1},
        "b2": {"start_month": 5, "start_year": 2026, "duration_months": 1},
    }
    p.save()

    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        resp = client.get(f"/preview/{p.id}")
        assert resp.status_code == 200
        html = resp.data.decode()
        bars = re.findall(r'preview-timeline-bar(?:-indent)?"[^>]*style="([^"]+)"', html)
        task_bar = bars[0]
        assert "left" in task_bar
        task_bar_items = re.findall(r'([\w-]+):([^;]+)', task_bar)
        styles = {k: v.strip() for k, v in task_bar_items}
        width_val = float(styles['width'].rstrip('%'))
        assert width_val > 25.0, f"Task bar width {width_val}% should span beyond original 25% (3 months)"
