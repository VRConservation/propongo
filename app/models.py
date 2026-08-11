"""Data models for Propongo.

Tasks and budget items are stored as dictionaries with the following structure:

Task dict:
    {
        'id': str,                # UUID
        'name': str,              # Task name
        'description': str,       # Task description
        'lead_entity': str,       # Organization responsible
        'start_month': int,       # Start month (1-12)
        'start_year': int,        # Start year
        'duration_months': int,   # Duration in months
    }

BudgetItem dict:
    {
        'id': str,                # UUID
        'task_id': str,           # Associated task UUID
        'name': str,              # Item name
        'cost_per_unit': float,   # Unit cost
        'units': float,           # Number of units
    }

Custom Section dict:
    {
        'id': str,                # UUID
        'title': str,             # Section title
        'content': str,           # Markdown content
        'order': int,             # Display order
    }
"""

import json
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

_CWD_DATA = os.path.join(os.getcwd(), "data")
_USER_DATA = os.path.join(os.path.expanduser("~"), "Documents", "Propongo")

env_dir = os.environ.get("PROPONGO_DATA_DIR")
if env_dir:
    _DATA_ROOT = env_dir
elif os.path.isdir(os.path.join(_CWD_DATA, "proposals")):
    _DATA_ROOT = os.path.abspath(_CWD_DATA)
else:
    _DATA_ROOT = _USER_DATA

DATA_ROOT = _DATA_ROOT

PROPOSALS_DIR = os.path.join(_DATA_ROOT, "proposals")
TEMPLATES_DIR = os.path.join(_DATA_ROOT, "templates")

# Demo proposals bundled with the package, seeded into the admin account's
# proposals dir on first use so the gallery is not empty on fresh deploys.
_DEMO_PROPOSALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proposals")


def ensure_dirs() -> None:
    """Ensure data directories exist."""
    os.makedirs(PROPOSALS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)


def _auth_enabled() -> bool:
    return os.environ.get("PROPONGO_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")


def _current_owner() -> str:
    """Username of the logged-in user when multi-user auth is on, else ''.

    Returns an empty string for single-user local mode and for requests made
    outside of a logged-in session (which keeps paths unchanged)."""
    if not _auth_enabled():
        return ""
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return current_user.username
    except (ImportError, RuntimeError):
        pass
    return ""


def _scoped_dir(base_dir: str) -> str:
    """Return `base_dir`, or `base_dir/<owner>` when a user is logged in.

    Creates the directory if needed so load/list/save can rely on it existing.
    """
    os.makedirs(base_dir, exist_ok=True)
    owner = _current_owner()
    if not owner:
        return base_dir
    scoped = os.path.join(base_dir, owner)
    os.makedirs(scoped, exist_ok=True)
    return scoped


def _seed_demo_proposals(target_dir: str, owner: Optional[str] = None) -> None:
    """Seed the bundled demo proposals into an empty proposals dir.

    Runs only for the account named by ``PROPONGO_ADMIN_USER`` (the owner),
    and only when the target dir has no proposals yet, so other users never
    receive the demo content. Copies are skipped when a file already exists
    so existing proposals are never overwritten.
    """
    if owner is None:
        owner = _current_owner()
    seed_user = os.environ.get("PROPONGO_ADMIN_USER", "").strip()
    if not owner or not seed_user or owner != seed_user:
        return
    if not os.path.isdir(target_dir):
        return
    if any(f.endswith(".json") for f in os.listdir(target_dir)):
        return
    if not os.path.isdir(_DEMO_PROPOSALS_DIR):
        return
    for name in os.listdir(_DEMO_PROPOSALS_DIR):
        if not name.endswith(".json"):
            continue
        dest = os.path.join(target_dir, name)
        if not os.path.exists(dest):
            shutil.copyfile(os.path.join(_DEMO_PROPOSALS_DIR, name), dest)


@dataclass
class Proposal:
    """A project proposal containing tasks, budget items, and custom sections."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Proposal"
    client_name: str = ""
    subtitle: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    project_summary: str = ""
    scope: str = ""
    tasks: list = field(default_factory=list)
    qualifications: str = ""

    budget_items: list = field(default_factory=list)
    budget_item_timings: dict = field(default_factory=dict)
    start_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    end_date: str = ""
    indirect_percent: float = 0.0
    show_budget_description: bool = False
    budget_description: str = ""
    timeline_use_days: bool = False
    timeline_show_budget: bool = False
    custom_sections: list = field(default_factory=list)

    is_template: bool = False
    template_name: str = ""
    template_category: str = ""

    milestones: list = field(default_factory=list)
    reports: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the proposal to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Proposal":
        """Create a Proposal from a dictionary, ignoring unknown fields."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self):
        """Save the proposal to disk as a JSON file."""
        self.updated_at = datetime.now().isoformat()
        target_dir = _scoped_dir(TEMPLATES_DIR if self.is_template else PROPOSALS_DIR)
        filepath = os.path.join(target_dir, f"{self.id}.json")
        tmp = filepath + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
            f.write("\n")
        os.replace(tmp, filepath)

    @classmethod
    def load(cls, proposal_id: str, is_template: bool = False) -> Optional["Proposal"]:
        """Load a proposal or template by ID from disk."""
        target_dir = _scoped_dir(TEMPLATES_DIR if is_template else PROPOSALS_DIR)
        filepath = os.path.join(target_dir, f"{proposal_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r") as f:
                return cls.from_dict(json.load(f))
        except (json.JSONDecodeError, OSError):
            return None

    @classmethod
    def list_all(cls) -> list:
        """List all proposals, returning summaries sorted by most recent."""
        target_dir = _scoped_dir(PROPOSALS_DIR)
        _seed_demo_proposals(target_dir)
        proposals = []
        for filename in sorted(os.listdir(target_dir)):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(target_dir, filename), "r") as f:
                        data = json.load(f)
                        proposals.append({
                            "id": data.get("id", filename.replace(".json", "")),
                            "title": data.get("title", "Untitled"),
                            "client_name": data.get("client_name", ""),
                            "subtitle": data.get("subtitle", ""),
                            "updated_at": data.get("updated_at", ""),
                        })
                except (json.JSONDecodeError, OSError):
                    continue
        return sorted(proposals, key=lambda x: x["updated_at"], reverse=True)

    @classmethod
    def list_templates(cls) -> list:
        """List all templates, returning summaries sorted by most recent."""
        target_dir = _scoped_dir(TEMPLATES_DIR)
        templates = []
        for filename in sorted(os.listdir(target_dir)):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(target_dir, filename), "r") as f:
                        data = json.load(f)
                        templates.append({
                            "id": data.get("id", filename.replace(".json", "")),
                            "title": data.get("title", "Untitled"),
                            "template_name": data.get("template_name", ""),
                            "template_category": data.get("template_category", ""),
                            "updated_at": data.get("updated_at", ""),
                        })
                except (json.JSONDecodeError, OSError):
                    continue
        return sorted(templates, key=lambda x: x["updated_at"], reverse=True)

    @classmethod
    def delete(cls, proposal_id: str, is_template: bool = False) -> bool:
        """Delete a proposal or template by ID. Returns True if deleted."""
        target_dir = _scoped_dir(TEMPLATES_DIR if is_template else PROPOSALS_DIR)
        filepath = os.path.join(target_dir, f"{proposal_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    @property
    def total_budget(self) -> float:
        """Compute total budget as the sum of cost_per_unit * units for all items."""
        return sum(
            item.get("cost_per_unit", 0) * item.get("units", 0)
            for item in self.budget_items
        )
