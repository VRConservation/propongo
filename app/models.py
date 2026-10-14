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
        # plus any of BUDGET_TIMING_FIELDS that are set
    }

Custom Section dict:
    {
        'id': str,                # UUID
        'title': str,             # Section title
        'content': str,           # Markdown content
        'order': int,             # Display order
    }

map_config dict (Map tab): which context layer the embedded GeoLibre map
opens with. One of:
    {'mode': 'basemap'}                                  # bare map, pick basemap in-app
    {'mode': 'data_url', 'url': '<public data URL>'}     # GeoJSON/COG/PMTiles/etc.
    {'mode': 'project_url', 'url': '<shared .geolibre.json URL>'}
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
MAPS_DIR = os.path.join(_DATA_ROOT, "maps")

# Demo proposals bundled with the package, seeded into the admin account's
# proposals dir on first use so the gallery is not empty on fresh deploys.
_DEMO_PROPOSALS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proposals")


# Timing keys that live on a budget item dict itself. Proposals written before
# normalization kept these in a parallel ``budget_item_timings`` dict keyed by
# item id; ``Proposal.from_dict`` folds that legacy dict into the items on load,
# and it is never written back out.
BUDGET_TIMING_FIELDS = (
    "start_month",
    "start_year",
    "duration_months",
    "lead_entity",
    "recurring",
    "recurring_interval",
    "actual_cost",
)


def item_is_scheduled(item: dict) -> bool:
    """True when a budget item has both a start month and a start year.

    Missing either one means *unscheduled* - not a zero-length schedule. This
    is the same test ``build_budget_by_year()`` uses to fill its ``unscheduled``
    bucket so its totals still reconcile.
    """
    return bool(item.get("start_month")) and bool(item.get("start_year"))


def clear_item_timing(item: dict) -> None:
    """Mark a budget item unscheduled by dropping its timing keys."""
    for key in BUDGET_TIMING_FIELDS:
        item.pop(key, None)


def copy_budget_items(items: list) -> list:
    """Shallow-copy a budget item list so each dict is independent.

    ``list(items)`` alone would share the dicts, so editing the copy's timing
    would mutate the original proposal - which matters for save-as and
    new-from-template.
    """
    return [dict(item) for item in (items or [])]


def ensure_dirs() -> None:
    """Ensure data directories exist."""
    os.makedirs(PROPOSALS_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(MAPS_DIR, exist_ok=True)


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
    """Ensure the bundled demo proposals exist in the admin account's dir.

    Runs only for the account named by ``PROPONGO_ADMIN_USER`` (the owner), so
    other users never receive the demo content. Each demo proposal is copied
    only if it is missing — existing files are never overwritten, so the demos
    are added even to a gallery that already contains user proposals.
    """
    if owner is None:
        owner = _current_owner()
    seed_user = os.environ.get("PROPONGO_ADMIN_USER", "").strip()
    if not owner or not seed_user or owner != seed_user:
        return
    if not os.path.isdir(_DEMO_PROPOSALS_DIR):
        return
    os.makedirs(target_dir, exist_ok=True)
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
    start_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    end_date: str = ""
    indirect_percent: float = 0.0
    show_budget_description: bool = False
    budget_description: str = ""
    timeline_use_days: bool = False
    timeline_show_budget: bool = False
    custom_sections: list = field(default_factory=list)
    map_config: dict = field(default_factory=dict)

    is_template: bool = False
    template_name: str = ""
    template_category: str = ""

    milestones: list = field(default_factory=list)
    reports: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the proposal to a dictionary.

        Timing is stored on the budget items, so ``budget_item_timings`` is not
        a field and is not written out.
        """
        return asdict(self)

    @property
    def budget_item_timings(self) -> dict:
        """Legacy ``{item_id: timing}`` view, derived from the budget items.

        Kept so templates and callers that still expect the old parallel dict
        keep working. Never persisted - ``to_dict()`` serializes fields only.
        """
        return {
            item["id"]: {k: item[k] for k in BUDGET_TIMING_FIELDS if k in item}
            for item in self.budget_items
            if item.get("id") and any(k in item for k in BUDGET_TIMING_FIELDS)
        }

    @budget_item_timings.setter
    def budget_item_timings(self, timings: dict) -> None:
        """Fold a legacy ``{item_id: timing}`` dict into the items themselves.

        Merges rather than replaces: keys absent from an entry leave that
        item's existing timing untouched, so a partial payload (the timeline tab
        posts only the items it rendered) cannot wipe ``actual_cost`` or the
        scheduling of items it did not send. Unknown item ids are ignored.
        """
        by_id = {item.get("id"): item for item in self.budget_items}
        for item_id, timing in (timings or {}).items():
            item = by_id.get(item_id)
            if item is None or not isinstance(timing, dict):
                continue
            for key in BUDGET_TIMING_FIELDS:
                if key in timing:
                    item[key] = timing[key]

    @classmethod
    def from_dict(cls, data: dict) -> "Proposal":
        """Create a Proposal from a dictionary, ignoring unknown fields.

        A legacy ``budget_item_timings`` entry is folded into the matching
        budget items, so files written before normalization keep their
        schedule and get the new shape on the next save.
        """
        data = dict(data)
        legacy_timings = data.pop("budget_item_timings", None)
        proposal = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if legacy_timings:
            proposal.budget_item_timings = legacy_timings
        return proposal

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
