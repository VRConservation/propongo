"""LLM-as-judge scoring for proposal sections (Scope, Qualifications, Custom Sections).

Scores a section the way an independent reviewer would - against fixed
criteria owned by the app (see app/judge_criteria.py), not something the
proposal writer defines for themselves. Scoring runs one of two ways
depending on the model picked in the UI:

- "ollama" (default, free): calls a locally running Ollama server
  (OLLAMA_BASE_URL, default http://localhost:11434) with the model named by
  OLLAMA_MODEL. Fully local, no API key, no data leaves the machine - but it
  requires Ollama installed and a model pulled first, see .env.example.
  Uses Ollama's native structured-output support (a JSON schema passed as
  `format`), so - unlike a free-text prompt-and-hope approach - the response
  is already schema-valid JSON.
- "sonnet" / "opus": the real Anthropic API (ANTHROPIC_API_KEY required),
  using a forced-by-instruction `submit_score` tool for reliable structured
  output.
"""

import json
import hashlib
import logging
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from flask import Blueprint, request, jsonify

from .models import Proposal
from .config import Config, ERROR_MESSAGES
from . import judge_criteria

logger = logging.getLogger(__name__)

judge_bp = Blueprint("judge", __name__)

MODEL_LABELS = {
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
}

_MAX_CONTENT_CHARS = 12000
# Local CPU/GPU inference can be slow depending on hardware and model size -
# generous timeout rather than failing fast on a merely-slow machine.
_OLLAMA_TIMEOUT_S = 120
_ANTHROPIC_TIMEOUT_S = 60

SCORE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer", "minimum": 1, "maximum": 5},
        "rationale": {"type": "string", "description": "1-3 sentences explaining the score."},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific required points/questions not (fully) addressed.",
        },
    },
    "required": ["score", "rationale", "strengths", "gaps"],
    "additionalProperties": False,
}

SCORE_TOOL = {
    "name": "submit_score",
    "description": "Submit your evaluation of the section against the scoring criteria.",
    "input_schema": SCORE_JSON_SCHEMA,
}


class JudgeError(Exception):
    """Raised for any scoring failure; carries the HTTP status to return."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class SectionNotFoundError(Exception):
    pass


def _section_title_content_and_source(proposal, section_key: str) -> tuple[str, str, Optional[tuple]]:
    """Return (title, content, rfp_source) for a section, or raise SectionNotFoundError.

    ``rfp_source`` is ``(rfp_template_id, rfp_section_id)`` when the section
    was created via Import RFP, else ``None``. Scope/Qualifications never
    have an RFP source - they're fixed proposal fields, not RFP-derived.
    """
    if section_key == "scope":
        return "Scope", proposal.scope or "", None
    if section_key == "qualifications":
        return "Qualifications", proposal.qualifications or "", None
    for section in getattr(proposal, "custom_sections", None) or []:
        if section.get("id") == section_key:
            template_id = (section.get("rfp_template_id") or "").strip()
            rfp_section_id = (section.get("rfp_section_id") or "").strip()
            rfp_source = (template_id, rfp_section_id) if template_id and rfp_section_id else None
            return section.get("title") or "Untitled Section", section.get("content") or "", rfp_source
    raise SectionNotFoundError(section_key)


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _build_prompts(proposal, section_key: str, section_title: str, content: str,
                    rfp_source: Optional[tuple]) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) shared by both model paths."""
    criteria = judge_criteria.get_criteria(section_key, rfp_source)

    context_lines = [f'Proposal title: "{proposal.title or "Untitled Proposal"}"']
    if proposal.client_name:
        context_lines.append(f"Funder: {proposal.client_name}")
    if proposal.subtitle:
        context_lines.append(f"Program: {proposal.subtitle}")
    if proposal.project_summary:
        summary = proposal.project_summary.strip()
        if len(summary) > 500:
            summary = summary[:500] + "…"
        context_lines.append(f"Project summary: {summary}")

    system_prompt = (
        "You are an independent reviewer scoring one section of a grant/project proposal, the "
        "way a funder's reviewer would - not the person who wrote it. Be honest and specific; do "
        "not inflate scores to be encouraging. Use the proposal context only to judge relevance, "
        "not to excuse a weak section.\n\n"
        + "\n".join(context_lines)
        + f'\n\nSection being graded: "{section_title}"\n\n'
        f"Scoring criteria (1-5):\n{criteria}\n\n"
        'In "gaps", call out specific required points from the criteria or the section\'s own '
        "purpose that are missing or weakly addressed - not generic style complaints unless "
        "the criteria ask for them."
    )

    trimmed = content.strip()
    truncated_note = ""
    if len(trimmed) > _MAX_CONTENT_CHARS:
        trimmed = trimmed[:_MAX_CONTENT_CHARS]
        truncated_note = "\n\n[content truncated for length]"
    user_prompt = f'Section content:\n"""\n{trimmed}{truncated_note}\n"""'

    return system_prompt, user_prompt


def _normalize_result(raw: dict) -> dict:
    """Validate/coerce a raw judge payload into the persisted result shape."""
    if not isinstance(raw, dict):
        raise JudgeError("The model didn't return a usable score.")

    try:
        score = int(raw.get("score"))
    except (TypeError, ValueError):
        raise JudgeError("The model didn't return a usable score.")
    score = max(1, min(5, score))

    rationale = raw.get("rationale")
    rationale = str(rationale).strip() if rationale else ""

    def _str_list(value) -> list:
        if not isinstance(value, list):
            return []
        return [str(v).strip() for v in value if str(v).strip()]

    return {
        "score": score,
        "rationale": rationale,
        "strengths": _str_list(raw.get("strengths")),
        "gaps": _str_list(raw.get("gaps")),
    }


def _call_ollama(system_prompt: str, user_prompt: str) -> dict:
    payload = json.dumps({
        "model": Config.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": SCORE_JSON_SCHEMA,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_OLLAMA_TIMEOUT_S) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 404 and "not found" in body.lower():
            raise JudgeError(
                f"Ollama model \"{Config.OLLAMA_MODEL}\" isn't pulled yet. Run "
                f"`ollama pull {Config.OLLAMA_MODEL}`, or set OLLAMA_MODEL to a model you have "
                "(see .env.example).",
                status_code=400,
            )
        raise JudgeError(f"Ollama returned an error: {body}")
    except urllib.error.URLError as exc:
        raise JudgeError(
            f"Could not reach Ollama at {Config.OLLAMA_BASE_URL} ({exc.reason}). Is it installed "
            "and running? See .env.example for setup instructions, or choose Sonnet/Opus instead.",
            status_code=400,
        )
    except TimeoutError:
        raise JudgeError("Ollama timed out. The model may be slow on this machine - try again, "
                          "use a smaller model, or choose Sonnet/Opus instead.")

    content = (data.get("message") or {}).get("content", "")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise JudgeError("Ollama didn't return a usable score this time. Try again.")


def _call_anthropic(system_prompt: str, user_prompt: str, model_id: str) -> dict:
    if not Config.ANTHROPIC_API_KEY:
        raise JudgeError(
            "Set ANTHROPIC_API_KEY in your .env to use Claude Sonnet/Opus.",
            status_code=400,
        )

    try:
        import anthropic
    except ImportError:
        raise JudgeError("The anthropic package isn't installed.", status_code=400)

    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY, timeout=_ANTHROPIC_TIMEOUT_S)

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=1024,
            system=system_prompt + "\n\nCall the submit_score tool with your evaluation.",
            tools=[SCORE_TOOL],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIError as exc:
        raise JudgeError(f"Claude API error: {exc}")

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_score":
            return block.input

    raise JudgeError("Claude didn't return a score. Try again.")


def score_section(proposal, section_key: str, model_choice: str) -> dict:
    """Score *section_key* on *proposal* with the chosen model.

    Returns the result dict. Raises SectionNotFoundError or JudgeError.
    """
    title, content, rfp_source = _section_title_content_and_source(proposal, section_key)

    system_prompt, user_prompt = _build_prompts(proposal, section_key, title, content, rfp_source)

    if model_choice == "ollama":
        raw = _call_ollama(system_prompt, user_prompt)
        model_label = f"ollama/{Config.OLLAMA_MODEL}"
    elif model_choice in ("sonnet", "opus"):
        raw = _call_anthropic(system_prompt, user_prompt, MODEL_LABELS[model_choice])
        model_label = MODEL_LABELS[model_choice]
    else:
        raise JudgeError(f"Unknown model choice: {model_choice}", status_code=400)

    result = _normalize_result(raw)
    result["model"] = model_label
    result["scored_at"] = datetime.now().isoformat()
    result["content_hash"] = _content_hash(content)
    return result


@judge_bp.route("/api/section/<proposal_id>/<section_key>/score", methods=["POST"])
def score_section_route(proposal_id, section_key):
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES["PROPOSAL_NOT_FOUND"]), 404

    data = request.get_json(silent=True) or {}
    model_choice = data.get("model", "ollama")

    try:
        result = score_section(proposal, section_key, model_choice)
    except SectionNotFoundError:
        return jsonify(ERROR_MESSAGES["SECTION_KEY_NOT_FOUND"]), 404
    except JudgeError as exc:
        logger.warning("Judge scoring failed for %s/%s: %s", proposal_id, section_key, exc)
        return jsonify({"error": str(exc)}), exc.status_code

    judging = dict(proposal.judging or {})
    judging[section_key] = result
    proposal.judging = judging
    proposal.save()

    return jsonify(result), 200
