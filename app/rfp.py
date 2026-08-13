"""RFP section import.

Turns a funder's Request for Proposals (RFP) into the required proposal
sections the applicant must write. The sections themselves are produced
offline by an agent that reads the RFP (or by hand) and described as JSON
(see ``app/rfp/`` for the bundled example). This module only applies those
descriptions to a proposal, keeping Propongo fully local and dependency-free.

Each entry in the JSON ``sections`` list looks like:

    {
        "id": "cal-fire-wpb-2025-bg",
        "track": "Business Development",   # optional variant filter
        "title": "Project Background",
        "points": 10,                      # optional
        "attachment": "Scope of Work attachment",   # optional, where the RFP
                                                    # says the criterion is
                                                    # addressed
        "requirements": ["...", "..."]     # RFP bullet requirements
    }

Each requirement may be a plain string or an object
``{"header": "Deliverables", "text": "List and describe deliverables."}``.
The ``header`` is a short summary for the bullet, copied verbatim from the
RFP when it suggests one; it renders as ``- **Header:** text``. Leave it out
when the RFP has no named requirement.

Applying a template adds one custom section per entry, titled
``Project Background (10 pts)``, whose markdown content is a checklist of
the RFP requirements. Importing the same template twice never duplicates
sections — entries whose title already exists are skipped.
"""

import json
import logging
import os
import uuid
from typing import Tuple
from flask import Blueprint, request, jsonify, Response

from . import models
from .config import ERROR_MESSAGES

logger = logging.getLogger(__name__)

rfp_bp = Blueprint("rfp", __name__)

# Stock templates ship inside the package; additional agent-produced
# templates can be dropped into data/rfp/ as JSON files.
_PKG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rfp")
USER_DIR = os.path.join(models.DATA_ROOT, "rfp")

_TEMPLATE_FIELDS = ("id", "title", "agency", "program", "fiscal_year", "source", "summary")
_SECTION_FIELDS = ("id", "track", "title", "points", "attachment", "requirements")


def _read_json_file(path: str):
    """Return the parsed JSON from ``path`` or None on any error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError):
        logger.warning("Ignoring unreadable RFP template %s", path)
        return None


def _iter_template_files():
    """Yield (path, is_user) for every *.json template in scope."""
    if os.path.isdir(_PKG_DIR):
        for name in sorted(os.listdir(_PKG_DIR)):
            if name.endswith(".json"):
                yield os.path.join(_PKG_DIR, name), False
    if os.path.isdir(USER_DIR):
        for name in sorted(os.listdir(USER_DIR)):
            if name.endswith(".json"):
                yield os.path.join(USER_DIR, name), True


def load_templates() -> list:
    """Load all RFP templates, with user templates overriding stock by id."""
    templates = {}
    order = []
    for path, is_user in _iter_template_files():
        data = _read_json_file(path)
        if not isinstance(data, dict) or not (data.get("id") or "").strip():
            continue
        tid = data["id"].strip()
        if tid not in templates:
            order.append(tid)
        templates[tid] = data
    return [templates[tid] for tid in order]


def load_template(template_id: str):
    """Return the template with ``template_id`` or None."""
    for template in load_templates():
        if template.get("id") == template_id:
            return template
    return None


def build_section_content(section: dict) -> str:
    """Build the markdown checklist content for one RFP section entry."""
    lines = []
    points = section.get("points")
    if points:
        lines.append(f"**RFP scoring criterion — {points} points**")
    else:
        lines.append("**RFP scoring criterion**")
    attachment = (section.get("attachment") or "").strip()
    if attachment:
        lines.append(f"**Addressed per the RFP in:** {attachment}")
    requirements = section.get("requirements") or []
    if requirements:
        lines.append("")
        lines.append("Required elements:")
        for req in requirements:
            if isinstance(req, dict):
                header = (req.get("header") or "").strip()
                text = str(req.get("text") or "").strip()
                if header and text:
                    lines.append(f"- **{header}:** {text}")
                elif header:
                    lines.append(f"- **{header}**")
                elif text:
                    lines.append(f"- {text}")
            else:
                req = str(req).strip()
                if req:
                    lines.append(f"- {req}")
    return "\n".join(lines)


def _section_title(section: dict) -> str:
    """Custom section title, e.g. ``Project Background (10 pts)``."""
    title = (section.get("title") or "New Section").strip()
    points = section.get("points")
    if points:
        return f"{title} ({points} pts)"
    return title


def apply_sections(proposal, sections: list) -> dict:
    """Add RFP-derived sections to ``proposal`` as custom sections.

    Entries whose generated title already exists in the proposal are
    skipped so re-importing a template is idempotent.

    Returns a summary dict with ``added``, ``skipped`` and ``created``.
    """
    existing = getattr(proposal, "custom_sections", None) or []
    existing_titles = {str(s.get("title", "")).strip().lower() for s in existing}
    created = []
    skipped = 0
    for section in sections:
        if not isinstance(section, dict) or not (section.get("title") or "").strip():
            skipped += 1
            continue
        title = _section_title(section)
        if title.lower() in existing_titles:
            skipped += 1
            continue
        new_section = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": build_section_content(section),
            "order": len(existing) + len(created),
        }
        created.append(new_section)
        existing_titles.add(title.lower())
    proposal.custom_sections = list(existing) + created
    return {"added": len(created), "skipped": skipped, "created": created}


def _validate_template(template: dict) -> Tuple[list, list]:
    """Return (sections, errors) for a candidate template dict."""
    if not isinstance(template, dict):
        return [], ["RFP template must be a JSON object"]
    sections = template.get("sections")
    if not isinstance(sections, list) or not sections:
        return [], ["RFP template must include a non-empty 'sections' list"]
    errors = []
    for i, section in enumerate(sections):
        if not isinstance(section, dict) or not (section.get("title") or "").strip():
            errors.append(f"Section {i + 1}: 'title' is required")
    return sections, errors


@rfp_bp.route("/api/rfp/templates")
def list_templates() -> Response:
    """List available RFP templates with a section count per track."""
    items = []
    for template in load_templates():
        sections = template.get("sections") or []
        tracks = []
        for section in sections:
            track = (section.get("track") or "").strip()
            if track and track not in tracks:
                tracks.append(track)
        items.append({
            "id": template.get("id"),
            "title": template.get("title"),
            "agency": template.get("agency"),
            "program": template.get("program"),
            "fiscal_year": template.get("fiscal_year"),
            "source": template.get("source"),
            "summary": template.get("summary"),
            "tracks": tracks,
            "section_count": len(sections),
        })
    return jsonify(items)


@rfp_bp.route("/api/proposal/<proposal_id>/import-rfp", methods=["POST"])
def import_rfp(proposal_id: str) -> Tuple[Response, int] | Response:
    """Apply RFP-required sections to a proposal.

    Body is JSON. Provide either ``template_id`` (plus optional ``track``
    to import only one applicant track) or a raw ``sections`` list from a
    file produced by the agent for a different RFP.
    """
    proposal = models.Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400

    if isinstance(data.get("sections"), list):
        sections, errors = _validate_template(data)
        if errors:
            return jsonify({"error": "Invalid RFP data", "details": errors}), 400
    else:
        template_id = (data.get("template_id") or "").strip()
        template = load_template(template_id) if template_id else None
        if not template:
            return jsonify({"error": "RFP template not found"}), 404
        sections, errors = _validate_template(template)
        if errors:
            return jsonify({"error": "Invalid RFP template", "details": errors}), 400
        track = (data.get("track") or "").strip()
        if track:
            sections = [s for s in sections if (s.get("track") or "").strip() == track]

    result = apply_sections(proposal, sections)
    proposal.save()
    logger.info(
        "Imported RFP sections into proposal %s: %s added, %s skipped",
        proposal_id, result["added"], result["skipped"],
    )
    return jsonify(result), 200
