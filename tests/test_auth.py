import os
import shutil
import tempfile
import time

import app.auth as auth
import app.models as models
import app.results as results
import app.snippets as snippets
from app.main import create_app


_orig_users_file = auth.USERS_FILE
_orig_proposals_dir = models.PROPOSALS_DIR
_orig_templates_dir = models.TEMPLATES_DIR
_orig_snippets_dir = snippets.SNIPPETS_DIR
_orig_results_dir = results.RESULTS_DIR
_orig_env = None
_test_dir = None


def setup_function():
    global _orig_env, _test_dir
    _orig_env = dict(os.environ)
    _test_dir = tempfile.mkdtemp()
    auth.USERS_FILE = os.path.join(_test_dir, "users.json")
    models.PROPOSALS_DIR = os.path.join(_test_dir, "proposals")
    models.TEMPLATES_DIR = os.path.join(_test_dir, "templates")
    snippets.SNIPPETS_DIR = os.path.join(_test_dir, "snippets")
    results.RESULTS_DIR = os.path.join(_test_dir, "results")


def teardown_function():
    global _orig_env, _test_dir
    auth.USERS_FILE = _orig_users_file
    models.PROPOSALS_DIR = _orig_proposals_dir
    models.TEMPLATES_DIR = _orig_templates_dir
    snippets.SNIPPETS_DIR = _orig_snippets_dir
    results.RESULTS_DIR = _orig_results_dir
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


def test_login_accepts_email_instead_of_username():
    _enable_auth()
    client = _client()
    _register(client, "alice", "password123", email="alice@example.org")
    client.get("/logout")

    resp = client.post("/login", data={"username": "alice@example.org", "password": "password123"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Propongo" in resp.data


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
            "email": "alice@example.org",
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
            "email": "alice2@example.org",
            "password": "password456",
            "confirm_password": "password456",
        },
        follow_redirects=True,
    )
    assert b"already taken" in resp.data


def test_registration_requires_email():
    _enable_auth()
    client = _client()
    resp = client.post(
        "/register",
        data={
            "username": "nobody",
            "email": "",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"email" in resp.data.lower()
    assert auth.load_user("nobody") is None


def test_registration_rejects_invalid_email():
    _enable_auth()
    client = _client()
    resp = client.post(
        "/register",
        data={
            "username": "nobody",
            "email": "not-an-email",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"email" in resp.data.lower()
    assert auth.load_user("nobody") is None


def _register(client, username, password, email=None):
    if email is None:
        email = f"{username}@example.org"
    return client.post(
        "/register",
        data={
            "username": username,
            "email": email,
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


def test_snippets_are_per_user():
    _enable_auth()
    admin = _client()
    admin.post("/login", data={"username": "admin", "password": "testpass123"})
    resp = admin.post("/snippets/custom", json={"title": "Admin Snippet", "content": "Admin only"}, content_type="application/json")
    assert resp.status_code == 201
    admin_custom = admin.get("/snippets").get_json()["custom"]
    assert any(s["title"] == "Admin Snippet" for s in admin_custom)

    alice = _client()
    _register(alice, "alice", "password123")
    alice_snippets = alice.get("/snippets").get_json()
    assert alice_snippets["custom"] == []

    resp = alice.post("/snippets/custom", json={"title": "Alice Snippet", "content": "Alice only"}, content_type="application/json")
    assert resp.status_code == 201

    admin_custom = admin.get("/snippets").get_json()["custom"]
    assert any(s["title"] == "Admin Snippet" for s in admin_custom)
    assert not any(s["title"] == "Alice Snippet" for s in admin_custom)


def test_results_library_is_per_user():
    _enable_auth()
    admin = _client()
    admin.post("/login", data={"username": "admin", "password": "testpass123"})
    resp = admin.post("/api/results", json={"title": "Admin Finding", "evidence": "data"}, content_type="application/json")
    assert resp.status_code == 201
    assert any(r["title"] == "Admin Finding" for r in admin.get("/api/results").get_json())
    assert admin.get("/api/results").get_json()

    alice = _client()
    _register(alice, "alice", "password123")
    alice_results = alice.get("/api/results").get_json()
    assert not any(r["title"] == "Admin Finding" for r in alice_results)
    assert alice_results

    resp = alice.post("/api/results", json={"title": "Alice Finding", "evidence": "data"}, content_type="application/json")
    assert resp.status_code == 201
    assert not any(r["title"] == "Alice Finding" for r in admin.get("/api/results").get_json())


def test_forgot_password_page_renders():
    _enable_auth()
    client = _client()
    resp = client.get("/forgot-password")
    assert resp.status_code == 200
    assert b"forgot" in resp.data.lower() or b"password" in resp.data.lower()


def test_forgot_password_shows_confirmation_even_if_unknown_email():
    _enable_auth()
    client = _client()
    resp = client.post("/forgot-password", data={"email": "nobody@example.org"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Check your inbox" in resp.data


def test_forgot_password_requires_email():
    _enable_auth()
    client = _client()
    resp = client.post("/forgot-password", data={"email": ""}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"required" in resp.data.lower() or b"Email address" in resp.data


def test_reset_password_flow():
    _enable_auth()
    client = _client()
    # Register a user with an email
    client.post(
        "/register",
        data={
            "username": "bob",
            "email": "bob@example.org",
            "password": "oldpass123",
            "confirm_password": "oldpass123",
        },
        follow_redirects=True,
    )
    client.get("/logout")

    # Request a reset
    resp = client.post("/forgot-password", data={"email": "bob@example.org"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Check your inbox" in resp.data

    # Extract token from user data
    user_data = auth._load_users().get("bob", {})
    token = auth.generate_reset_token("bob")
    assert token

    # Reset password
    resp = client.post(
        "/reset-password",
        data={"token": token, "password": "newpass456", "confirm_password": "newpass456"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"successfully" in resp.data.lower() or b"reset" in resp.data.lower()

    # Login with new password
    resp = client.post("/login", data={"username": "bob", "password": "newpass456"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Propongo" in resp.data

    # Old password should not work
    client.get("/logout")
    resp = client.post("/login", data={"username": "bob", "password": "oldpass123"}, follow_redirects=True)
    assert b"Invalid username or password" in resp.data


def test_reset_password_rejects_invalid_token():
    _enable_auth()
    client = _client()
    resp = client.get("/reset-password?token=garbage", follow_redirects=True)
    assert resp.status_code == 200
    assert b"invalid" in resp.data.lower() or b"expired" in resp.data.lower()


def test_reset_password_rejects_expired_token():
    _enable_auth()
    client = _client()
    # Register a user
    client.post(
        "/register",
        data={
            "username": "carol",
            "email": "carol@example.org",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )

    # Generate token then manually expire it
    token = auth.generate_reset_token("carol")
    with auth._lock:
        users = auth._load_users()
        users["carol"]["reset_token_expires"] = time.time() - 100
        auth._save_users(users)

    resp = client.get(f"/reset-password?token={token}", follow_redirects=True)
    assert resp.status_code == 200
    assert b"invalid" in resp.data.lower() or b"expired" in resp.data.lower()


def test_forgot_password_page_visible_when_auth_disabled():
    os.environ.pop("PROPONGO_AUTH_ENABLED", None)
    client = _client()
    resp = client.get("/forgot-password")
    # When auth is disabled, should redirect to index
    assert resp.status_code == 302


def test_registration_blocked_by_honeypot():
    _enable_auth()
    client = _client()
    resp = client.post(
        "/register",
        data={
            "username": "botuser",
            "email": "bot@example.org",
            "password": "password123",
            "confirm_password": "password123",
            "website": "http://spam.example.com",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert auth.load_user("botuser") is None


def test_registration_rate_limited():
    _enable_auth()
    with auth._rate_lock:
        auth._rate_events.clear()
    # A fresh client per attempt simulates anonymous bot traffic (separate
    # sessions, so the post-signup auto-login guard doesn't short-circuit).
    for i in range(auth._RATE_MAX):
        fresh = _client()
        fresh.post(
            "/register",
            data={
                "username": f"user{i}",
                "email": f"user{i}@example.org",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
    resp = _client().post(
        "/register",
        data={
            "username": "blocked",
            "email": "blocked@example.org",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Too many signup attempts" in resp.data
    assert auth.load_user("blocked") is None
