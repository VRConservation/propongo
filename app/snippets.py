"""Snippet management for reusable text blocks."""

import json
import os
import uuid
import logging
from typing import Tuple, Dict, List, Any
from flask import Blueprint, render_template, request, jsonify, Response
from .config import ERROR_MESSAGES
from . import models

logger = logging.getLogger(__name__)

snippets_bp = Blueprint("snippets", __name__)

# Snippet data lives under the resolved data root alongside proposals and
# templates, scoped per user when multi-user auth is enabled. New installs
# start empty; organization/deliverables list files are still honored for
# data written by older versions.
SNIPPETS_DIR = os.path.join(models.DATA_ROOT, "snippets")
_STOCK_SOURCES = ("organization", "deliverables")


def _snippets_root() -> str:
    """Snippets root for the current user.

    Returns `data/snippets/<owner>` when multi-user auth is on and someone is
    logged in, otherwise the shared `data/snippets` (single-user mode).
    """
    return models._scoped_dir(SNIPPETS_DIR)


def _custom_dir() -> str:
    return os.path.join(_snippets_root(), "custom")


def ensure_dirs():
    """Ensure per-user snippet directories exist."""
    root = _snippets_root()
    os.makedirs(root, exist_ok=True)
    os.makedirs(_custom_dir(), exist_ok=True)


def load_snippets(filename):
    """Load snippets from the current user's data directory."""
    ensure_dirs()
    filepath = os.path.join(_snippets_root(), filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []


def save_snippets(filename, data):
    """Save snippets to the current user's data directory."""
    ensure_dirs()
    filepath = os.path.join(_snippets_root(), filename)
    tmp = filepath + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, filepath)


def load_custom_snippets():
    """Load all custom snippets for the current user."""
    ensure_dirs()
    snippets = []
    for filename in sorted(os.listdir(_custom_dir())):
        if filename.endswith(".json"):
            with open(os.path.join(_custom_dir(), filename), "r") as f:
                snippets.append(json.load(f))
    return snippets


_STOCK_SOURCES = ("organization", "deliverables")


def _with_source(snippets, source):
    """Copy each snippet dict and tag where it is stored.

    The storage source (which file/directory holds the snippet) is kept
    separate from the display `category`, which users can edit freely.
    """
    tagged = []
    for s in snippets:
        item = dict(s)
        item["source"] = source
        tagged.append(item)
    return tagged


@snippets_bp.route("/snippets")
def get_all_snippets():
    """Return all snippets grouped by category, tagged with their source."""
    return jsonify({
        "organization": _with_source(load_snippets("organization.json"), "organization"),
        "deliverables": _with_source(load_snippets("deliverables.json"), "deliverables"),
        "custom": _with_source(load_custom_snippets(), "custom"),
    })


@snippets_bp.route("/snippets/<category>", methods=["POST"])
def add_snippet(category):
    """Add a new snippet to the given category.

    Stock categories (`organization`, `deliverables`) append to their list
    files; anything else — including free-form labels sent in the body's
    `category` field — is stored under custom/ so it stays user-editable.
    """
    data = request.get_json()
    if not data or "title" not in data or "content" not in data:
        return jsonify({"error": "title and content required"}), 400

    if category in _STOCK_SOURCES:
        label = category
    else:
        label = str(data.get("category") or "").strip() or category

    snippet = {
        "id": data.get("id", uuid.uuid4().hex[:8]),
        "title": data["title"],
        "content": data["content"],
        "category": label,
    }

    if category in _STOCK_SOURCES:
        snippets = load_snippets(f"{category}.json")
        snippets.append(snippet)
        save_snippets(f"{category}.json", snippets)
    else:
        ensure_dirs()
        filepath = os.path.join(_custom_dir(), f"{snippet['id']}.json")
        with open(filepath, "w") as f:
            json.dump(snippet, f, indent=2)

    return jsonify(snippet), 201


@snippets_bp.route("/snippets/<category>/<snippet_id>", methods=["PUT"])
def update_snippet(category, snippet_id):
    """Update a snippet's title, content, and/or category.

    Only the display fields change; the snippet stays in its current storage
    location (list file or custom directory), which is identified by the URL.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "no fields to update"}), 400

    updates = {}
    for field in ("title", "content", "category"):
        if field in data and str(data[field]).strip():
            updates[field] = str(data[field])
    if not updates:
        return jsonify({"error": "no fields to update"}), 400

    if category == "custom":
        filepath = os.path.join(_custom_dir(), f"{snippet_id}.json")
        if not os.path.exists(filepath):
            return jsonify(ERROR_MESSAGES['SECTION_NOT_FOUND']), 404
        with open(filepath, "r") as f:
            snippet = json.load(f)
        snippet.update(updates)
        tmp = filepath + ".tmp"
        with open(tmp, "w") as f:
            json.dump(snippet, f, indent=2)
        os.replace(tmp, filepath)
        return jsonify(snippet)

    if category in _STOCK_SOURCES:
        snippets = load_snippets(f"{category}.json")
        for i, s in enumerate(snippets):
            if s.get("id") == snippet_id:
                updated = dict(s)
                updated.update(updates)
                snippets[i] = updated
                save_snippets(f"{category}.json", snippets)
                return jsonify(updated), 200

    return jsonify(ERROR_MESSAGES['SECTION_NOT_FOUND']), 404


@snippets_bp.route("/snippets/<category>/<snippet_id>", methods=["DELETE"])
def delete_snippet(category, snippet_id):
    """Delete a snippet by category and ID."""
    if category == "custom":
        filepath = os.path.join(_custom_dir(), f"{snippet_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"ok": True})
    elif category in ("organization", "deliverables"):
        snippets = load_snippets(f"{category}.json")
        snippets = [s for s in snippets if s.get("id") != snippet_id]
        save_snippets(f"{category}.json", snippets)
        return jsonify({"ok": True})

    return jsonify(ERROR_MESSAGES['SECTION_NOT_FOUND']), 404


@snippets_bp.route("/snippets/import", methods=["POST"])
def import_snippet():
    """Import a snippet from a .md, .txt, or .docx file."""
    if "file" not in request.files:
        return jsonify(ERROR_MESSAGES['NO_FILE']), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify(ERROR_MESSAGES['NO_FILE']), 400

    filename = file.filename.lower()
    title = request.form.get("title", "").strip()
    if not title:
        title = os.path.splitext(file.filename)[0]

    try:
        if filename.endswith(".md") or filename.endswith(".markdown") or filename.endswith(".txt"):
            content = file.read().decode("utf-8")
        elif filename.endswith(".docx"):
            from docx import Document
            doc = Document(file)
            content = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            return jsonify({"error": "Unsupported file type. Use .md, .txt, or .docx"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    if not content.strip():
        return jsonify({"error": "File is empty"}), 400

    snippet = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "content": content,
        "category": "custom",
    }

    ensure_dirs()
    filepath = os.path.join(_custom_dir(), f"{snippet['id']}.json")
    with open(filepath, "w") as f:
        json.dump(snippet, f, indent=2)

    return jsonify(snippet), 201
