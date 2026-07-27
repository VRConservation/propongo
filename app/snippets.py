"""Snippet management for reusable text blocks."""

import json
import os
import uuid
import logging
from typing import Tuple, Dict, List, Any
from flask import Blueprint, render_template, request, jsonify, Response
from .config import ERROR_MESSAGES

logger = logging.getLogger(__name__)

snippets_bp = Blueprint("snippets", __name__)

SNIPPETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "snippets")
CUSTOM_DIR = os.path.join(SNIPPETS_DIR, "custom")


def ensure_dirs():
    """Ensure snippet directories exist."""
    os.makedirs(SNIPPETS_DIR, exist_ok=True)
    os.makedirs(CUSTOM_DIR, exist_ok=True)


def load_snippets(filename):
    """Load snippets from a JSON file."""
    filepath = os.path.join(SNIPPETS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []


def save_snippets(filename, data):
    """Save snippets to a JSON file."""
    ensure_dirs()
    filepath = os.path.join(SNIPPETS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def load_custom_snippets():
    """Load all user-created custom snippets."""
    ensure_dirs()
    snippets = []
    for filename in sorted(os.listdir(CUSTOM_DIR)):
        if filename.endswith(".json"):
            with open(os.path.join(CUSTOM_DIR, filename), "r") as f:
                snippets.append(json.load(f))
    return snippets


@snippets_bp.route("/snippets")
def get_all_snippets():
    """Return all snippets grouped by category."""
    return jsonify({
        "organization": load_snippets("organization.json"),
        "deliverables": load_snippets("deliverables.json"),
        "custom": load_custom_snippets(),
    })


@snippets_bp.route("/snippets/<category>", methods=["POST"])
def add_snippet(category):
    """Add a new snippet to the given category."""
    data = request.get_json()
    if not data or "title" not in data or "content" not in data:
        return jsonify({"error": "title and content required"}), 400

    snippet = {
        "id": data.get("id", uuid.uuid4().hex[:8]),
        "title": data["title"],
        "content": data["content"],
        "category": category,
    }

    if category == "custom":
        ensure_dirs()
        filepath = os.path.join(CUSTOM_DIR, f"{snippet['id']}.json")
        with open(filepath, "w") as f:
            json.dump(snippet, f, indent=2)
    elif category in ("organization", "deliverables"):
        snippets = load_snippets(f"{category}.json")
        snippets.append(snippet)
        save_snippets(f"{category}.json", snippets)
    else:
        return jsonify({"error": "Invalid category"}), 400

    return jsonify(snippet), 201


@snippets_bp.route("/snippets/<category>/<snippet_id>", methods=["DELETE"])
def delete_snippet(category, snippet_id):
    """Delete a snippet by category and ID."""
    if category == "custom":
        filepath = os.path.join(CUSTOM_DIR, f"{snippet_id}.json")
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
    filepath = os.path.join(CUSTOM_DIR, f"{snippet['id']}.json")
    with open(filepath, "w") as f:
        json.dump(snippet, f, indent=2)

    return jsonify(snippet), 201
