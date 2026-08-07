import os
import shutil
import tempfile

import app.auth as auth
from app.main import create_app


_orig_users_file = auth.USERS_FILE
_orig_env = None
_test_dir = None


def setup_function():
    global _orig_env, _test_dir
    _orig_env = dict(os.environ)
    _test_dir = tempfile.mkdtemp()
    auth.USERS_FILE = os.path.join(_test_dir, "users.json")


def teardown_function():
    global _orig_env, _test_dir
    auth.USERS_FILE = _orig_users_file
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
