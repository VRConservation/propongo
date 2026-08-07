"""Authentication for Propongo.

Single-user / small-team auth backed by a JSON users file under the data
root. Disabled by default for local use; set PROPONGO_AUTH_ENABLED=true
to turn it on (needed for any public deployment). The first admin account
is provisioned from PROPONGO_ADMIN_USER / PROPONGO_ADMIN_PASSWORD the
first time the app starts with auth enabled.
"""

import json
import logging
import os
import secrets
import threading
from typing import Optional

from flask import Blueprint, g, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from .i18n import DEFAULT_LANG, LANG_COOKIE, translate
from .models import DATA_ROOT

logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(DATA_ROOT, "users.json")

DEFAULT_PLAN = "free"

_lock = threading.Lock()


def auth_enabled() -> bool:
    """Return True if login is required for the app."""
    return os.environ.get("PROPONGO_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


class User(UserMixin):
    """A user account. `plan` is reserved for future paid tiers."""

    def __init__(self, username: str, email: str = "", password_hash: str = "", plan: str = DEFAULT_PLAN):
        self.id = username
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.plan = plan

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "plan": self.plan,
        }


def _load_users() -> dict:
    """Load all users from the JSON users file as {username: user_dict}."""
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {u["username"]: u for u in data}
        return data
    except (json.JSONDecodeError, OSError, KeyError):
        logger.warning("Could not read users file at %s", USERS_FILE)
        return {}


def _save_users(users: dict) -> None:
    """Persist all users to the JSON users file (atomic write)."""
    os.makedirs(os.path.dirname(USERS_FILE) or ".", exist_ok=True)
    tmp = USERS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(list(users.values()), f, indent=2)
        f.write("\n")
    os.replace(tmp, USERS_FILE)


def load_user(user_id: str) -> Optional["User"]:
    """Flask-Login user loader."""
    data = _load_users().get(user_id)
    if not data:
        return None
    return User(
        data.get("username", user_id),
        data.get("email", ""),
        data.get("password_hash", ""),
        data.get("plan", DEFAULT_PLAN),
    )


def get_user(username: str) -> Optional["User"]:
    """Return a user by username, or None."""
    return load_user(username)


def ensure_admin_user() -> None:
    """Provision the initial admin account from environment variables."""
    if not auth_enabled():
        return
    with _lock:
        users = _load_users()
        if users:
            return
        username = (os.environ.get("PROPONGO_ADMIN_USER") or "admin").strip()
        password = os.environ.get("PROPONGO_ADMIN_PASSWORD") or ""
        if not password:
            password = secrets.token_urlsafe(16)
            logger.warning(
                "PROPONGO_ADMIN_PASSWORD not set. Generated a temporary password for '%s': %s",
                username,
                password,
            )
        users[username] = {
            "username": username,
            "email": os.environ.get("PROPONGO_ADMIN_EMAIL", ""),
            "password_hash": generate_password_hash(password),
            "plan": DEFAULT_PLAN,
        }
        _save_users(users)
        logger.info("Created initial admin user '%s'", username)


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Render the login page and authenticate credentials."""
    if not auth_enabled():
        return redirect(url_for("index"))
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = load_user(username)
        if user and user.check_password(password):
            login_user(user)
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
        error = translate("Invalid username or password.", getattr(g, "lang", DEFAULT_LANG))

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    """Log out the current user."""
    logout_user()
    return redirect(url_for("auth.login"))


def init_login_manager(app) -> LoginManager:
    """Attach Flask-Login to the app."""
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.user_loader(load_user)
    return login_manager
