import os
import shutil
import tempfile

import app.auth as auth
import app.models as models
from app.main import create_app


_orig_users_file = auth.USERS_FILE
_orig_proposals_dir = models.PROPOSALS_DIR
_orig_templates_dir = models.TEMPLATES_DIR
_orig_env = None
_test_dir = None


def setup_function():
    global _orig_env, _test_dir
    _orig_env = dict(os.environ)
    _test_dir = tempfile.mkdtemp()
    auth.USERS_FILE = os.path.join(_test_dir, "users.json")
    models.PROPOSALS_DIR = os.path.join(_test_dir, "proposals")
    models.TEMPLATES_DIR = os.path.join(_test_dir, "templates")


def teardown_function():
    global _orig_env, _test_dir
    auth.USERS_FILE = _orig_users_file
    models.PROPOSALS_DIR = _orig_proposals_dir
    models.TEMPLATES_DIR = _orig_templates_dir
    os.environ.clear()
    os.environ.update(_orig_env)
    _orig_env = None
    if _test_dir and os.path.exists(_test_dir):
        shutil.rmtree(_test_dir)
    _test_dir = None


def _enable_auth():
    os.environ["PROPONGO_AUTH_ENABLED"] = "true"
    os.environ["PROPONGO_ADMIN_USER"] = "admin"
    os.environ["PROPONGO_ADMIN_PASSWORD"] = "testpass123"


def _client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_auth_disabled_by_default():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    client = _client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Propongo" in resp.data


def test_login_page_redirects_to_index_when_disabled():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    client = _client()
    resp = client.get("/login")
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]


def test_requires_login_when_enabled():
    _enable_auth()
    client = _client()
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_healthz_is_public_when_enabled():
    _enable_auth()
    client = _client()
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_admin_account_is_provisioned_from_env():
    _enable_auth()
    _client()
    assert os.path.exists(auth.USERS_FILE)
    assert auth.load_user("admin") is not None


def test_admin_password_is_reset_from_env_on_boot():
    _enable_auth()
    os.environ["PROPONGO_ADMIN_PASSWORD"] = "firstpass"
    _client()
    assert auth.load_user("admin").check_password("firstpass")

    os.environ["PROPONGO_ADMIN_PASSWORD"] = "secondpass"
    _client()
    user = auth.load_user("admin")
    assert user.check_password("secondpass")
    assert not user.check_password("firstpass")


def test_login_flow():
    _enable_auth()
    client = _client()
    resp = client.get("/login")
    assert resp.status_code == 200

    resp = client.post("/login", data={"username": "admin", "password": "testpass123"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Propongo" in resp.data


def test_login_rejects_bad_credentials():
    _enable_auth()
    client = _client()
    resp = client.post("/login", data={"username": "admin", "password": "wrong"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_logout():
    _enable_auth()
    client = _client()
    client.post("/login", data={"username": "admin", "password": "testpass123"})
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_registration_flow():
    _enable_auth()
    client = _client()
    resp = client.get("/register")
    assert resp.status_code == 200

    resp = client.post(
        "/register",
        data={
            "username": "alice",
            "email": "alice@example.org",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert auth.load_user("alice") is not None
    assert client.get("/", follow_redirects=False).status_code == 200


def test_registration_rejects_mismatched_passwords():
    _enable_auth()
    client = _client()
    resp = client.post(
        "/register",
        data={
            "username": "alice",
            "password": "password123",
            "confirm_password": "different123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Passwords do not match" in resp.data
    assert auth.load_user("alice") is None


def test_registration_rejects_duplicate_username():
    _enable_auth()
    _register(_client(), "alice", "password123")
    other = _client()
    resp = other.post(
        "/register",
        data={
            "username": "alice",
            "password": "password456",
            "confirm_password": "password456",
        },
        follow_redirects=True,
    )
    assert b"already taken" in resp.data


def _register(client, username, password):
    return client.post(
        "/register",
        data={
            "username": username,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def test_new_proposal_requires_title():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    client = _client()
    resp = client.post("/new", json={}, content_type="application/json")
    assert resp.status_code == 400


def test_new_proposal_creates_with_title():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    client = _client()
    resp = client.post("/new", json={"title": "My First Proposal"}, content_type="application/json")
    assert resp.status_code == 201
    pid = resp.get_json()["id"]
    loaded = models.Proposal.load(pid)
    assert loaded.title == "My First Proposal"


def test_per_user_proposal_isolation():
    _enable_auth()
    admin = _client()
    admin.post("/login", data={"username": "admin", "password": "testpass123"})
    admin_id = admin.post("/new", json={"title": "Admin Secret"}, content_type="application/json").get_json()["id"]

    alice = _client()
    _register(alice, "alice", "password123")
    assert alice.get(f"/api/proposal/{admin_id}").status_code == 404
    assert admin_id not in [p["id"] for p in alice.get("/api/proposals").get_json()]

    alice_id = alice.post("/new", json={"title": "Alice Proposal"}, content_type="application/json").get_json()["id"]
    assert alice_id in [p["id"] for p in alice.get("/api/proposals").get_json()]
    assert alice_id not in [p["id"] for p in admin.get("/api/proposals").get_json()]
    assert admin.get(f"/api/proposal/{alice_id}").status_code == 404
