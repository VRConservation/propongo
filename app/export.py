"""Export functionality for HTML, PDF, and Markdown generation.

PDF exports are produced by printing the exact same HTML document the HTML
export serves with headless Chromium. Only a real browser engine executes the
JavaScript behind the live GeoLibre map iframe, so this is what keeps the map
in the PDF; WeasyPrint (still used for the timeline PNG) drops iframes.
"""

import os
import base64
import time
import logging
from io import BytesIO
from typing import Tuple

import html2text

from flask import Blueprint, render_template, request, send_file, jsonify, Response
from .models import Proposal
from .utils import build_export_context, build_tracker_export_context
from .config import Config, ERROR_MESSAGES

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)

CHROMIUM_MISSING_MSG = (
    "PDF export requires headless Chromium. Install it with: "
    "pip install playwright && playwright install chromium"
)

GTK3_MISSING_MSG = (
    "Timeline PNG export requires GTK3. Download the installer: "
    "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/"
    "releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
)


def _chromium_missing_error(exc: Exception) -> bool:
    """True if *exc* indicates Playwright's browser executable is missing.

    Playwright raises ``Error: Executable doesn't exist at ...`` when the
    Chromium build (``playwright install chromium``) has not been installed,
    even though the Python package itself is present.
    """
    return "executable doesn't exist" in str(exc).lower()


def _map_image_ready(png: bytes) -> bool:
    """Heuristic for whether a canvas screenshot contains an actual drawn map.

    A blank/loading GeoLibre canvas is near-uniform light gray; a rendered map
    has a high ratio of colored pixels. Falls back to a byte-size check when
    Pillow/numpy are unavailable.
    """
    try:
        import io
        import numpy as np
        from PIL import Image

        a = np.array(Image.open(io.BytesIO(png)).convert("RGB")).reshape(-1, 3).astype(int)
        colored = ((np.abs(a - 255).sum(axis=1)) > 60).mean()
        return float(colored) >= 0.4
    except Exception:
        return len(png) > 50000


def _render_pdf(html_content: str, map_wait: float = 15.0) -> bytes:
    """Print *html_content* to PDF bytes with headless Chromium.

    The live GeoLibre map iframe loads the full workspace app (buttons,
    panels, settings), which would clutter the PDF. Instead we screenshot just
    the map canvas from inside the iframe (once it has actually drawn content)
    and swap the iframe for that clean image before printing. Waits are
    bounded — no blanket ``networkidle`` on the map frame, which keeps the
    export fast.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": 1400, "height": 1000},
                device_scale_factor=2,
            )
            page.set_content(html_content, wait_until="load")

            geo_frame = next((f for f in page.frames if "geolibre" in f.url), None)
            if geo_frame is not None:
                try:
                    canvas = geo_frame.locator("canvas").first
                    canvas.wait_for(state="attached", timeout=10000)
                    png = b""
                    start = time.monotonic()
                    while time.monotonic() - start < map_wait:
                        candidate = canvas.screenshot()
                        if _map_image_ready(candidate):
                            png = candidate
                            break
                        png = candidate
                        page.wait_for_timeout(500)
                    if _map_image_ready(png):
                        data_uri = "data:image/png;base64," + base64.b64encode(png).decode()
                        page.evaluate(
                            """(src) => {
                                const el = document.getElementById('map-export-frame');
                                if (el) {
                                    const img = document.createElement('img');
                                    img.src = src;
                                    img.style.maxWidth = '100%';
                                    img.style.display = 'block';
                                    el.replaceWith(img);
                                }
                            }""",
                            data_uri,
                        )
                except Exception as exc:
                    logger.debug("Map capture for PDF export failed: %s", exc)

            return page.pdf(
                format="Letter",
                print_background=True,
            )
        finally:
            browser.close()


def _html_to_markdown(html_content: str) -> str:
    """Convert an export HTML document to plain Markdown text."""
    h = html2text.HTML2Text()
    h.body_width = 0
    h.hide_inline_images = False
    return h.handle(html_content).strip()


@export_bp.route("/export/pdf/<proposal_id>")
def export_pdf(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as PDF by printing the HTML export in headless Chromium."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for PDF export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    ctx["map_static_data_uri"] = None
    html_content = render_template("export_proposal.html", **ctx)

    try:
        pdf_bytes = _render_pdf(html_content)
    except ImportError:
        return jsonify({"error": CHROMIUM_MISSING_MSG}), 500
    except Exception as e:
        if _chromium_missing_error(e):
            return jsonify({"error": CHROMIUM_MISSING_MSG}), 500
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
    md_content = _html_to_markdown(html_content)

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
        pdf_bytes = _render_pdf(html_content)
    except ImportError:
        return jsonify({"error": CHROMIUM_MISSING_MSG}), 500
    except Exception as e:
        if _chromium_missing_error(e):
            return jsonify({"error": CHROMIUM_MISSING_MSG}), 500
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