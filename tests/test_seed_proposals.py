import os
import tempfile
import shutil
import app.models as models
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


def test_seed_demo_proposals_for_admin(monkeypatch):
    monkeypatch.setenv("PROPONGO_ADMIN_USER", "admin")
    os.makedirs(models.PROPOSALS_DIR, exist_ok=True)
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")

    files = sorted(os.listdir(models.PROPOSALS_DIR))
    assert files == ["jt_institute_08_03_2026.json", "sample.json"]

    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")
    assert sorted(os.listdir(models.PROPOSALS_DIR)) == files


def test_seed_demo_proposals_skips_non_admin(monkeypatch):
    monkeypatch.setenv("PROPONGO_ADMIN_USER", "admin")
    os.makedirs(models.PROPOSALS_DIR, exist_ok=True)
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="other")
    assert os.listdir(models.PROPOSALS_DIR) == []


def test_seed_demo_proposals_adds_to_nonempty_dir(monkeypatch):
    monkeypatch.setenv("PROPONGO_ADMIN_USER", "admin")
    p = Proposal(title="Existing")
    p.save()
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")
    files = sorted(os.listdir(models.PROPOSALS_DIR))
    assert files == [f"{p.id}.json", "jt_institute_08_03_2026.json", "sample.json"]


def test_seed_demo_proposals_never_overwrites(monkeypatch):
    monkeypatch.setenv("PROPONGO_ADMIN_USER", "admin")
    os.makedirs(models.PROPOSALS_DIR, exist_ok=True)
    dest = os.path.join(models.PROPOSALS_DIR, "sample.json")
    with open(dest, "w") as f:
        f.write("user data")
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")
    with open(dest) as f:
        assert f.read() == "user data"


def test_seed_demo_proposals_skips_when_admin_unset():
    os.makedirs(models.PROPOSALS_DIR, exist_ok=True)
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")
    assert os.listdir(models.PROPOSALS_DIR) == []


def test_seeded_proposals_appear_in_gallery(monkeypatch):
    monkeypatch.setenv("PROPONGO_ADMIN_USER", "admin")
    os.makedirs(models.PROPOSALS_DIR, exist_ok=True)
    models._seed_demo_proposals(models.PROPOSALS_DIR, owner="admin")

    proposals = Proposal.list_all()
    ids = {p["id"] for p in proposals}
    assert "sample" in ids
    assert "jt_institute_08_03_2026" in ids
