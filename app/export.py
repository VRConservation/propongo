"""Export functionality for HTML, PDF, and Markdown generation.

PDF exports are produced by printing the export HTML document with WeasyPrint.
WeasyPrint is lightweight and self-contained (no headless browser), so PDF
export stays within memory limits on constrained instances. Because it does
not execute JavaScript, the live GeoLibre map iframe cannot be printed —
instead the export template shows an uploaded static map image, a remote
``image_url``, or (failing both) an auto-generated snapshot of the Map tab's
live map, cached on disk so only the first export after a config change pays
the render cost. See ``get_cached_map_export_image`` in ``utils.py``.
"""

import os
import re
import calendar
import logging
from io import BytesIO
from typing import Tuple

import html2text

from flask import Blueprint, render_template, request, send_file, jsonify, Response
from .models import Proposal
from .utils import build_export_context, build_tracker_export_context, get_cached_map_export_image
from .config import Config, ERROR_MESSAGES

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)

GTK3_MISSING_MSG = (
    "Timeline PNG export requires GTK3. Download the installer: "
    "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/"
    "releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
)


def _render_pdf(html_content: str, base_url: str | None = None) -> bytes:
    """Print *html_content* to PDF bytes with WeasyPrint.

    WeasyPrint is a lightweight, self-contained renderer (no headless browser
    dependency), so PDF export stays well within memory limits on constrained
    instances (e.g. Render free/basic). Because it does not execute JavaScript,
    the live GeoLibre map iframe cannot be rendered — by the time *html_content*
    reaches here, the map has already been resolved to a static image (or
    omitted), see ``export_pdf`` and ``export_proposal.html``.
    """
    try:
        from weasyprint import HTML
    except (OSError, ImportError) as exc:
        raise RuntimeError("WeasyPrint is not installed or missing its system libraries") from exc

    buf = BytesIO()
    HTML(string=html_content, base_url=base_url).write_pdf(buf)
    return buf.getvalue()


def _local_map_data_uri(proposal) -> str | None:
    """Return an embedded data URI for the proposal's uploaded static map image.

    Reads the image stored under the data dir (``map_config.image_path`` in
    ``static_image`` mode) so WeasyPrint can embed it without fetching over the
    network. Returns *None* when no local image is configured.
    """
    maps_dir = os.path.join(Config.DATA_DIR, "maps")
    map_config = getattr(proposal, "map_config", None) or {}
    image_path = (map_config.get("image_path") or "").strip()
    if not image_path or map_config.get("mode") != "static_image":
        return None

    full = os.path.join(maps_dir, image_path)
    try:
        with open(full, "rb") as fh:
            data = fh.read()
    except (OSError, IOError):
        return None

    ext = os.path.splitext(image_path)[1].lower()
    mime = {"": "image/png", ".png": "image/png", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"}.get(ext, "application/octet-stream")
    import base64
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _auto_map_data_uri(proposal) -> str | None:
    """Return a data URI for an auto-generated snapshot of the live map.

    PDF fallback for proposals that have no uploaded static image and no
    remote ``image_url``: renders (and caches) a screenshot of whatever is
    configured on the Map tab instead of requiring a manual PNG export. See
    ``get_cached_map_export_image``. Returns *None* when generation fails
    (e.g. no network access, or Playwright unavailable on this host).
    """
    image = get_cached_map_export_image(proposal)
    if not image:
        return None
    import base64
    return f"data:image/png;base64,{base64.b64encode(image).decode('ascii')}"


def _html_to_markdown(html_content: str) -> str:
    """Convert an export HTML document to plain Markdown text."""
    h = html2text.HTML2Text()
    h.body_width = 0
    h.hide_inline_images = False
    return h.handle(html_content).strip()


def _strip_timeline_chart(html_content: str) -> str:
    """Remove the visual ``.timeline-chart`` gantt from an export document.

    The gantt is built from absolutely-positioned divs that collapse into a
    garbled blob when converted to Markdown. The Markdown export replaces it
    with a real table (see ``_timeline_markdown_table``), so the raw div chart
    is dropped here. The PDF/HTML exports are unaffected.
    """
    pattern = re.compile(r'<div class="timeline-chart"[^>]*>.*?</div>\s*</div>', re.DOTALL)
    return pattern.sub("", html_content, count=1)


def _timeline_markdown_table(proposal, ctx: dict) -> str:
    """Render the timeline as an ASCII-gantt Markdown table.

    One row per task (indented for budget sub-rows), one column per month,
    quarter, or year depending on ``timeline_granularity``. Active cells are
    marked with a full block ``█`` (fully covered) or a light block ``░``
    (partial overlap), reproducing the visual gantt as plain text.
    """
    all_rows = ctx.get("all_rows") or []
    if not all_rows:
        return ""
    total_months = ctx.get("timeline_total_months") or 1
    granularity = ctx.get("timeline_granularity") or "months"

    try:
        start_year = int(proposal.start_date[:4])
        start_month = int(proposal.start_date[5:7])
    except (TypeError, ValueError, IndexError):
        start_year, start_month = 2025, 1

    cell_size = {"months": 1, "quarters": 3, "years": 12}[granularity]
    ncols = (total_months + cell_size - 1) // cell_size

    def _col_start_year(c):
        return start_year + (start_month - 1 + c * cell_size) // 12

    if granularity == "months":
        heads = [
            calendar.month_abbr[(start_month - 1 + m) % 12 + 1]
            + ("'" + str(_col_start_year(m))[2:] if _col_start_year(m) != start_year else "")
            for m in range(ncols)
        ]
    elif granularity == "quarters":
        heads = [
            f"Q{(start_month - 1 + q * 3) % 12 // 3 + 1}"
            + ("'" + str(_col_start_year(q))[2:] if _col_start_year(q) != start_year else "")
            for q in range(ncols)
        ]
    else:
        heads = [str(start_year + i) for i in range(ncols)]

    headers = ["Task"] + heads
    header_line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] + [":---:"] * ncols) + " |"

    def _active_fraction(bars) -> list:
        active = [0] * ncols
        for bar in bars:
            boff, bdur = int(bar.get("offset") or 0), int(bar.get("duration") or 1)
            for c in range(ncols):
                c_start = c * cell_size
                c_end = c_start + cell_size
                overlap = min(c_end, boff + bdur) - max(c_start, boff)
                if overlap > 0:
                    active[c] += overlap
        return active

    rows = []
    for r in all_rows:
        active = _active_fraction(r.get("bars") or [])
        name = r.get("name", "")
        if r.get("is_indent"):
            name = f"    {name}"
        cells = []
        for c in range(ncols):
            frac = active[c] / cell_size
            if frac >= 0.999:
                cells.append("█")
            elif frac > 0:
                cells.append("░")
            else:
                cells.append(" ")
        rows.append("| " + " | ".join([name] + cells) + " |")

    return "\n".join([header_line, sep] + rows)


@export_bp.route("/export/pdf/<proposal_id>")
def export_pdf(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as PDF by printing the HTML export with WeasyPrint.

    The live GeoLibre iframe cannot be rendered by WeasyPrint, so the map is
    resolved to a static image in priority order: an uploaded PNG/JPG, a
    remote ``image_url``, then an auto-generated (and cached) snapshot of
    whatever is configured on the Map tab. Only if all of those fail is the
    map omitted with a note.
    """
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for PDF export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    ctx["map_static_data_uri"] = _local_map_data_uri(proposal)
    if not ctx["map_static_data_uri"] and ctx.get("map_ctx") and not ctx["map_ctx"].get("image_url"):
        ctx["map_static_data_uri"] = _auto_map_data_uri(proposal)
    ctx["for_pdf"] = True
    html_content = render_template("export_proposal.html", **ctx)

    try:
        pdf_bytes = _render_pdf(html_content, base_url=request.host_url)
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        return jsonify({"error": f"PDF export failed: {str(e)}"}), 500

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{proposal.title or 'proposal'}.pdf",
    )


@export_bp.route("/export/html/<proposal_id>")
def export_html(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as HTML file.

    Uses the live GeoLibre iframe (same as preview) — no static image
    needed since HTML renders in a browser.
    """
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for HTML export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    ctx["map_static_data_uri"] = None

    html_content = render_template("export_proposal.html", **ctx)

    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "inline"},
    )


@export_bp.route("/export/markdown/<proposal_id>")
def export_markdown(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as a Markdown document.

    Replaces the former DOCX export as the editable, plain-text format. The
    same HTML export template is rendered, then converted to Markdown.
    """
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for Markdown export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    ctx["map_static_data_uri"] = None

    html_content = render_template("export_proposal.html", **ctx)
    html_content = _strip_timeline_chart(html_content)
    md_content = _html_to_markdown(html_content)

    timeline_table = _timeline_markdown_table(proposal, ctx)
    if timeline_table:
        md_content = md_content.replace(
            "## Timeline\n", f"## Timeline\n\n{timeline_table}\n"
        )

    return Response(
        md_content,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={proposal.title or 'proposal'}.md"},
    )


@export_bp.route("/export/timeline/png/<proposal_id>")
def export_timeline_png(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export just the timeline chart as a PNG image.

    Renders the chart with WeasyPrint onto a content-sized page, then
    rasterizes it with pypdfium2 so the image is a tight crop rather than a
    full page.
    """
    try:
        from weasyprint import HTML
    except (OSError, ImportError):
        return jsonify({"error": GTK3_MISSING_MSG}), 500

    try:
        import pypdfium2 as pdfium
    except ImportError:
        return jsonify({"error": "pypdfium2 not installed"}), 500

    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for timeline PNG export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    html_content = render_template("timeline_export.html", **ctx)

    os.makedirs(Config.EXPORTS_DIR, exist_ok=True)
    pdf_buf = BytesIO()
    HTML(string=html_content, base_url=request.host_url).write_pdf(pdf_buf)
    pdf_buf.seek(0)

    pdf = pdfium.PdfDocument(pdf_buf)
    page = pdf[0]
    bitmap = page.render(scale=2)
    pil = bitmap.to_pil()
    png_path = os.path.join(Config.EXPORTS_DIR, f"timeline_{proposal_id}.png")
    pil.save(png_path, "PNG")

    return send_file(
        png_path,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"{proposal.title or 'proposal'}_timeline.png",
    )


@export_bp.route("/export/tracker/pdf/<proposal_id>")
def export_tracker_pdf(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export tracker as PDF."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_tracker_export_context(proposal)
    html_content = render_template("export_tracker.html", **ctx)

    try:
        pdf_bytes = _render_pdf(html_content, base_url=request.host_url)
    except Exception as e:
        logger.error(f"Tracker PDF export failed: {e}")
        return jsonify({"error": f"PDF export failed: {str(e)}"}), 500

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{proposal.title or 'project'}_tracker.pdf",
    )


@export_bp.route("/export/tracker/html/<proposal_id>")
def export_tracker_html(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export tracker as HTML."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_tracker_export_context(proposal)
    html_content = render_template("export_tracker.html", **ctx)

    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "inline"},
    )


@export_bp.route("/export/tracker/markdown/<proposal_id>")
def export_tracker_markdown(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export tracker as a Markdown document."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_tracker_export_context(proposal)
    md_content = _html_to_markdown(render_template("export_tracker.html", **ctx))

    return Response(
        md_content,
        mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={proposal.title or 'project'}_tracker.md"},
    )