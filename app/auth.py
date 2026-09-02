"""Authentication for Propongo.

Single-user / small-team auth backed by a JSON users file under the data
root. Disabled by default for local use; set PROPONGO_AUTH_ENABLED=true
to turn it on (needed for any public deployment). The first admin account
is provisioned from PROPONGO_ADMIN_USER / PROPONGO_ADMIN_PASSWORD the
first time the app starts with auth enabled.
"""

import hashlib
import json
import logging
import os
import re
import secrets
import smtplib
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from flask import Blueprint, g, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from .i18n import DEFAULT_LANG, LANG_COOKIE, translate
from .models import DATA_ROOT

logger = logging.getLogger(__name__)

USERS_FILE = os.path.join(DATA_ROOT, "users.json")

DEFAULT_PLAN = "free"
RESET_TOKEN_TTL = 3600  # 1 hour

_lock = threading.Lock()


def auth_enabled() -> bool:
    """Return True if login is required for the app."""
    return os.environ.get("PROPONGO_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


def allow_registration() -> bool:
    """Return True if new users may self-register."""
    return os.environ.get("PROPONGO_ALLOW_REGISTRATION", "true").lower() in ("true", "1", "yes")


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


def _find_user_by_email(email: str) -> Optional["User"]:
    """Return the first user matching the given email, or None."""
    email_lower = email.lower().strip()
    for data in _load_users().values():
        if data.get("email", "").lower() == email_lower:
            return User(
                data.get("username", ""),
                data.get("email", ""),
                data.get("password_hash", ""),
                data.get("plan", DEFAULT_PLAN),
            )
    return None


def _send_reset_email(to_email: str, username: str, reset_url: str) -> bool:
    """Send a password-reset email via SMTP. Returns True on success."""
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASS", "")
    from_addr = os.environ.get("SMTP_FROM", "") or user

    if not host:
        logger.warning("SMTP_HOST not configured — cannot send reset email")
        return False

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = "Propongo – Password Reset"
    msg.attach(MIMEText(
        f"Hello {username},\n\n"
        f"You requested a password reset for your Propongo account.\n\n"
        f"Click the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour. If you did not request this, "
        f"you can safely ignore this email.\n",
        "plain",
    ))

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            if port != 25:
                smtp.starttls()
                smtp.ehlo()
            if user and password:
                smtp.login(user, password)
            smtp.sendmail(from_addr, [to_email], msg.as_string())
        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send reset email to %s", to_email)
        return False


def generate_reset_token(username: str) -> str:
    """Generate a password-reset token, store its hash on the user, return the raw token."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    with _lock:
        users = _load_users()
        if username not in users:
            return ""
        users[username]["reset_token_hash"] = token_hash
        users[username]["reset_token_expires"] = time.time() + RESET_TOKEN_TTL
        _save_users(users)
    return raw_token


def _validate_reset_token(token: str) -> Optional[str]:
    """Validate a reset token. Returns the username if valid, else None."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = time.time()
    for username, data in _load_users().items():
        stored_hash = data.get("reset_token_hash", "")
        expires = data.get("reset_token_expires", 0)
        if stored_hash and stored_hash == token_hash and expires > now:
            return username
    return None


def _clear_reset_token(username: str) -> None:
    """Remove the reset token from a user record."""
    with _lock:
        users = _load_users()
        if username in users:
            users[username].pop("reset_token_hash", None)
            users[username].pop("reset_token_expires", None)
            _save_users(users)


def ensure_admin_user() -> None:
    """Provision (or reset) the admin account from environment variables.

    When PROPONGO_ADMIN_USER and PROPONGO_ADMIN_PASSWORD are both set, that
    account is created on first boot and its password is re-applied on every
    subsequent boot, so operators control credentials via the environment.
    If no users exist and the password is missing, a temporary password is
    generated and logged.
    """
    if not auth_enabled():
        return
    with _lock:
        users = _load_users()
        username = (os.environ.get("PROPONGO_ADMIN_USER") or "").strip()
        password = os.environ.get("PROPONGO_ADMIN_PASSWORD") or ""
        if not username or not password:
            if users:
                return
            username = username or "admin"
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
        logger.info("Admin user '%s' provisioned from environment", username)


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


def _validate_signup(username: str, email: str, password: str, confirm: str) -> Optional[str]:
    """Validate registration input, returning an error message or None."""
    lang = getattr(g, "lang", DEFAULT_LANG)
    if not re.match(r"^[A-Za-z0-9_.-]{3,32}$", username):
        return translate(
            "Usernames must be 3-32 characters using letters, numbers, dots, dashes, or underscores.",
            lang,
        )
    if len(password) < 8:
        return translate("Password must be at least 8 characters.", lang)
    if password != confirm:
        return translate("Passwords do not match.", lang)
    return None


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Render the registration page and create new accounts."""
    if not auth_enabled() or not allow_registration():
        return redirect(url_for("index"))
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        error = _validate_signup(username, email, password, confirm)
        if error is None:
            with _lock:
                users = _load_users()
                if username in users:
                    error = translate("That username is already taken.", getattr(g, "lang", DEFAULT_LANG))
                else:
                    users[username] = {
                        "username": username,
                        "email": email,
                        "password_hash": generate_password_hash(password),
                        "plan": DEFAULT_PLAN,
                    }
                    _save_users(users)
        if error is None:
            login_user(load_user(username))
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Render the forgot-password form and send a reset link."""
    if not auth_enabled():
        return redirect(url_for("index"))
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    lang = getattr(g, "lang", DEFAULT_LANG)
    error = None
    message = None
    email_value = ""

    if request.method == "POST":
        email_value = request.form.get("email", "").strip()
        if not email_value:
            error = translate("Email address is required.", lang)
        else:
            user = _find_user_by_email(email_value)
            if user:
                raw_token = generate_reset_token(user.username)
                if raw_token:
                    reset_url = url_for("auth.reset_password", token=raw_token, _external=True)
                    _send_reset_email(user.email, user.username, reset_url)
            # Always show the same message regardless of whether the email exists
            message = translate("Check your inbox for a password reset link.", lang)

    return render_template("forgot_password.html", error=error, message=message, email=email_value)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Render the reset-password form and apply the new password."""
    if not auth_enabled():
        return redirect(url_for("index"))

    lang = getattr(g, "lang", DEFAULT_LANG)
    token = request.args.get("token", "") or request.form.get("token", "")
    error = None
    message = None

    # Validate token on every request
    username = _validate_reset_token(token) if token else None
    if not token:
        error = translate("This reset link is invalid or has expired.", lang)
    elif not username:
        error = translate("This reset link is invalid or has expired.", lang)

    if request.method == "POST" and not error:
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(password) < 8:
            error = translate("Password must be at least 8 characters.", lang)
        elif password != confirm:
            error = translate("Passwords do not match.", lang)
        else:
            with _lock:
                users = _load_users()
                if username in users:
                    users[username]["password_hash"] = generate_password_hash(password)
                    users[username].pop("reset_token_hash", None)
                    users[username].pop("reset_token_expires", None)
                    _save_users(users)
            message = translate("Password reset successfully.", lang)

    return render_template("reset_password.html", error=error, message=message, token=token, valid=username is not None)


def init_login_manager(app) -> LoginManager:
    """Attach Flask-Login to the app."""
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.user_loader(load_user)
    return login_manager
