"""Evidence-based results library.

Stores reusable evidence-based findings (title, category, evidence text,
and source/reference) as JSON under the resolved data root, seeded from a
stock library shipped with the package on first run. Scoped per user when
multi-user auth is enabled.
"""

import json
import os
import shutil
import uuid
import logging
from typing import Tuple
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from .config import ERROR_MESSAGES
from . import models

logger = logging.getLogger(__name__)

results_bp = Blueprint("results", __name__)

_PKG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
RESULTS_DIR = os.path.join(models.DATA_ROOT, "results")


def _results_root() -> str:
    """Results root for the current user.

    Returns `data/results/<owner>` when multi-user auth is on and someone is
    logged in, otherwise the shared `data/results` (single-user mode).
    """
    return models._scoped_dir(RESULTS_DIR)


def _library_file() -> str:
    return os.path.join(_results_root(), "library.json")


def ensure_dirs():
    """Ensure the per-user results directory exists, seeding the stock library."""
    root = _results_root()
    os.makedirs(root, exist_ok=True)
    library = os.path.join(root, "library.json")
    seed = os.path.join(_PKG_DIR, "library.json")
    if os.path.exists(seed) and not os.path.exists(library):
        shutil.copyfile(seed, library)


def load_library() -> list:
    """Load the results library, seeding from stock data on first run."""
    ensure_dirs()
    library = _library_file()
    if os.path.exists(library):
        try:
            with open(library, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    seed = os.path.join(_PKG_DIR, "library.json")
    if os.path.exists(seed):
        try:
            with open(seed, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_library(entries: list) -> None:
    """Persist the results library to disk."""
    ensure_dirs()
    tmp = _library_file() + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")
    os.replace(tmp, _library_file())


@results_bp.route("/api/results")
def list_results() -> Tuple[Response, int] | Response:
    """Return all library entries."""
    return jsonify(load_library())


@results_bp.route("/api/results", methods=["POST"])
def add_result() -> Tuple[Response, int] | Response:
    """Add a new evidence-based result to the library."""
    data = request.get_json()
    if not data or not (data.get("title") or "").strip():
        return jsonify({"error": "Title required"}), 400

    entry = {
        "id": data.get("id") or uuid.uuid4().hex[:8],
        "title": data["title"].strip(),
        "category": (data.get("category") or "").strip(),
        "evidence": (data.get("evidence") or ""),
        "source": (data.get("source") or "").strip(),
        "created_at": datetime.now().isoformat(),
    }

    entries = load_library()
    entries.append(entry)
    save_library(entries)
    return jsonify(entry), 201


@results_bp.route("/api/results/<result_id>", methods=["PUT"])
def update_result(result_id: str) -> Tuple[Response, int] | Response:
    """Update an existing result entry."""
    data = request.get_json()
    entries = load_library()
    for entry in entries:
        if entry.get("id") == result_id:
            if data.get("title") is not None:
                entry["title"] = str(data["title"]).strip()
            if data.get("category") is not None:
                entry["category"] = str(data["category"]).strip()
            if data.get("evidence") is not None:
                entry["evidence"] = data["evidence"]
            if data.get("source") is not None:
                entry["source"] = str(data["source"]).strip()
            save_library(entries)
            return jsonify(entry)
    return jsonify(ERROR_MESSAGES['SECTION_NOT_FOUND']), 404


@results_bp.route("/api/results/<result_id>", methods=["DELETE"])
def delete_result(result_id: str) -> Tuple[Response, int] | Response:
    """Delete a result entry from the library."""
    entries = load_library()
    remaining = [e for e in entries if e.get("id") != result_id]
    if len(remaining) == len(entries):
        return jsonify(ERROR_MESSAGES['SECTION_NOT_FOUND']), 404
    save_library(remaining)
    return jsonify({"ok": True})
