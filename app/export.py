"""Export functionality for PDF, HTML, and DOCX generation."""

import os
import logging
import re as _re
from io import BytesIO
from typing import Tuple
try:
    from weasyprint import HTML
except (OSError, ImportError):
    HTML = None

GTK3_MISSING_MSG = (
    "PDF export requires GTK3. Download the installer: "
    "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/"
    "releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
)
from flask import Blueprint, render_template, request, send_file, jsonify, Response
from markupsafe import Markup
from .models import Proposal
from .utils import build_export_context, build_tracker_export_context
from .config import Config, ERROR_MESSAGES

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)

EXPORT_DIR = Config.EXPORTS_DIR


def ensure_export_dir() -> None:
    """Ensure export directory exists."""
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _md_to_plain(text: str) -> str:
    """Strip markdown to plain text for DOCX."""
    if not text:
        return ""
    text = _re.sub(r'#{1,6}\s+', '', text)
    text = _re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = _re.sub(r'\*(.+?)\*', r'\1', text)
    text = _re.sub(r'`(.+?)`', r'\1', text)
    text = _re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = _re.sub(r'^[-*]\s+', '  - ', text, flags=_re.MULTILINE)
    return text.strip()


def _add_timeline_to_docx(doc, proposal) -> None:
    """Render the Gantt-style timeline as a table for DOCX exports.

    Mirrors the Timeline section shown in the PDF/HTML exports. Bars from
    ``build_export_context`` are grouped into months, quarters, or years
    depending on the total project span; active periods are marked with a
    filled block.
    """
    from datetime import datetime as _dt
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    ctx = build_export_context(proposal)
    timeline_rows = ctx.get("all_rows") or []
    if not timeline_rows:
        return

    doc.add_heading('Timeline', level=1)

    total_months = ctx.get("timeline_total_months", 1)
    granularity = ctx.get("timeline_granularity", "months")
    if granularity == "months":
        period_count = total_months
    elif granularity == "quarters":
        period_count = -(-total_months // 3)
    else:
        period_count = -(-total_months // 12)

    try:
        sd = _dt.strptime(proposal.start_date, "%Y-%m-%d")
        proj_start_month = sd.month
        proj_start_year = sd.year
    except (ValueError, TypeError):
        proj_start_month = 1
        proj_start_year = 2025

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    table = doc.add_table(rows=1, cols=period_count + 1)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    header_cell = table.rows[0].cells[0]
    header_cell.text = 'Task'
    for i in range(period_count):
        cell = table.rows[0].cells[i + 1]
        if granularity == "months":
            label = month_names[(proj_start_month - 1 + i) % 12]
        elif granularity == "quarters":
            q = ((proj_start_month - 1) // 3 + i) % 4 + 1
            label = f"Q{q}"
        else:
            label = str(proj_start_year + i)
        cell.text = label
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(8)

    def _bar_in_period(bar, p_start, p_end):
        return bar["offset"] < p_end and (bar["offset"] + bar["duration"]) > p_start

    for r in timeline_rows:
        row = table.add_row()
        row.cells[0].text = r["name"]
        for i in range(period_count):
            cell = row.cells[i + 1]
            if granularity == "months":
                p_start, p_end = i, i + 1
            elif granularity == "quarters":
                p_start, p_end = i * 3, min((i + 1) * 3, total_months)
            else:
                p_start, p_end = i * 12, min((i + 1) * 12, total_months)
            if any(_bar_in_period(b, p_start, p_end) for b in r["bars"]):
                cell.text = "■"
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        run.font.size = Pt(8)


def _build_proposal_docx(proposal) -> BytesIO:
    """Build a DOCX document for a proposal."""
    from docx import Document
    from docx.shared import Inches, Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(proposal.title or "Proposal")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x1e, 0x3a, 0x5f)

    if proposal.client_name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"Funder: {proposal.client_name}")
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    if proposal.subtitle:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"Program: {proposal.subtitle}")
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(proposal.updated_at[:10] if proposal.updated_at else "")
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    doc.add_paragraph()

    if proposal.project_summary:
        doc.add_heading('Project Summary', level=1)
        for line in _md_to_plain(proposal.project_summary).split('\n'):
            if line.strip():
                doc.add_paragraph(line.strip())

    if proposal.scope:
        doc.add_heading('Scope', level=1)
        for line in _md_to_plain(proposal.scope).split('\n'):
            if line.strip():
                doc.add_paragraph(line.strip())

    if proposal.budget_items:
        doc.add_heading('Budget', level=1)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Light Grid Accent 1'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ['Item', 'Cost/Unit', 'Units', 'Total']
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(10)

        for task in proposal.tasks:
            task_items = [b for b in proposal.budget_items if b.get("task_id") == task["id"]]
            if not task_items:
                continue
            task_total = sum(i.get("cost_per_unit", 0) * i.get("units", 0) for i in task_items)
            row = table.add_row()
            row.cells[0].text = task["name"]
            row.cells[3].text = f"{task_total:,.0f}"
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True
                        run.font.size = Pt(10)
            for item in task_items:
                total = item.get("cost_per_unit", 0) * item.get("units", 0)
                row = table.add_row()
                row.cells[0].text = f"  {item['name']}"
                row.cells[1].text = f"{item.get('cost_per_unit', 0):,.0f}"
                row.cells[2].text = f"{int(item.get('units', 0))}"
                row.cells[3].text = f"{total:,.0f}"
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(10)

        row = table.add_row()
        row.cells[0].text = 'Subtotal'
        row.cells[3].text = f"{proposal.total_budget:,.0f}"
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        indirect_percent = getattr(proposal, 'indirect_percent', 0) or 0
        if indirect_percent > 0:
            indirect_amount = proposal.total_budget * (indirect_percent / 100)
            row = table.add_row()
            row.cells[0].text = f"Indirect ({indirect_percent:.0f}%)"
            row.cells[3].text = f"{indirect_amount:,.0f}"

        row = table.add_row()
        row.cells[0].text = 'Total'
        indirect_amount = proposal.total_budget * (indirect_percent / 100)
        row.cells[3].text = f"${proposal.total_budget + indirect_amount:,.0f}"
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        from .utils import build_budget_by_year
        by_year = build_budget_by_year(proposal)
        if by_year["years"] or by_year["unscheduled"]:
            year_table = doc.add_table(rows=1, cols=3)
            year_table.style = 'Light Grid Accent 1'
            year_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            for i, h in enumerate(['Year', 'Amount', '% of Total']):
                cell = year_table.rows[0].cells[i]
                cell.text = h
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.bold = True
                        run.font.size = Pt(10)
            total_budget = proposal.total_budget
            for row in by_year["years"]:
                r = year_table.add_row()
                r.cells[0].text = str(row["year"])
                r.cells[1].text = f"{row['amount']:,.0f}"
                pct = f"{(row['amount'] / total_budget * 100):.1f}%" if total_budget > 0 else ""
                r.cells[2].text = pct
            for u in by_year["unscheduled"]:
                r = year_table.add_row()
                r.cells[0].text = 'Not scheduled'
                r.cells[1].text = f"{u['amount']:,.0f}"
                pct = f"{(u['amount'] / total_budget * 100):.1f}%" if total_budget > 0 else ""
                r.cells[2].text = pct
            for r in year_table.rows[1:]:
                for cell in r.cells:
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(10)

    if proposal.show_budget_description and proposal.budget_description:
        doc.add_heading('Budget Description', level=1)
        for line in _md_to_plain(proposal.budget_description).split('\n'):
            if line.strip():
                doc.add_paragraph(line.strip())

    if proposal.qualifications:
        doc.add_heading('Qualifications', level=1)
        for line in _md_to_plain(proposal.qualifications).split('\n'):
            if line.strip():
                doc.add_paragraph(line.strip())

    if proposal.custom_sections:
        for section in sorted(proposal.custom_sections, key=lambda s: s.get("order", 0)):
            doc.add_heading(section.get("title", "Section"), level=1)
            for line in _md_to_plain(section.get("content", "")).split('\n'):
                if line.strip():
                    doc.add_paragraph(line.strip())

    _add_timeline_to_docx(doc, proposal)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def _build_tracker_docx(proposal, ctx) -> BytesIO:
    """Build a DOCX document for the project tracker."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(4)
    style.paragraph_format.line_spacing = 1.15

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Project Report: {proposal.title}")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x1e, 0x3a, 0x5f)

    if proposal.client_name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{proposal.client_name}{(' - ' + proposal.subtitle) if proposal.subtitle else ''}")
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    doc.add_paragraph()

    doc.add_heading('Dashboard Summary', level=1)
    table = doc.add_table(rows=2, cols=4)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Tasks Completed', 'Total Tasks', 'Total Budget', 'Milestones']
    values = [f"{ctx['overall_pct']}%", str(len(ctx['tasks'])), f"${ctx['total_with_indirect']:,.0f}", str(len(ctx['milestones']))]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(10)
    for i, v in enumerate(values):
        table.rows[1].cells[i].text = v
        for run in table.rows[1].cells[i].paragraphs[0].runs:
            run.font.size = Pt(10)

    status_labels = {
        "not_started": "Not Started",
        "in_progress": "In Progress",
        "completed": "Completed",
        "delayed": "Delayed",
    }

    doc.add_heading('Tasks', level=1)
    for task in ctx['tasks']:
        doc.add_heading(task.get('name', 'Untitled'), level=2)
        status = status_labels.get(task.get('status', 'not_started'), 'Not Started')
        progress = task.get('progress_pct', 0)
        p = doc.add_paragraph()
        run = p.add_run(f"Status: {status}")
        run.bold = True
        p = doc.add_paragraph(f"Progress: {progress}%")
        if task.get('actual_start'):
            p = doc.add_paragraph(f"Actual Start: {task['actual_start']}")
        if task.get('actual_end'):
            p = doc.add_paragraph(f"Actual End: {task['actual_end']}")
        if task.get('notes'):
            doc.add_paragraph()
            run = p.add_run("Notes:")
            run.bold = True
            for line in task['notes'].split('\n'):
                if line.strip():
                    doc.add_paragraph(line.strip())

    doc.add_heading('Budget Tracking', level=1)
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Task', 'Item', 'Planned', 'Actual', 'Variance']
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for run in table.rows[0].cells[i].paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(9)

    for task in ctx['tasks']:
        tid = task.get("id", "")
        if tid not in ctx['task_budgets']:
            continue
        tb = ctx['task_budgets'][tid]
        row = table.add_row()
        row.cells[0].text = task.get('name', '')
        row.cells[2].text = f"${tb['subtotal']:,.0f}"
        row.cells[3].text = f"${tb['actual_total']:,.0f}"
        variance = tb['actual_total'] - tb['subtotal']
        row.cells[4].text = f"${variance:,.0f}"
        for cell in row.cells:
            for run in cell.paragraphs[0].runs:
                run.bold = True
                run.font.size = Pt(9)
        for item in tb["items"]:
            planned = item.get("cost_per_unit", 0) * item.get("units", 0)
            actual = item.get("actual_cost", 0)
            v = actual - planned
            row = table.add_row()
            row.cells[1].text = item.get('name', '')
            row.cells[2].text = f"${planned:,.0f}"
            row.cells[3].text = f"${actual:,.0f}"
            row.cells[4].text = f"${v:,.0f}"
            for cell in row.cells:
                for run in cell.paragraphs[0].runs:
                    run.font.size = Pt(9)

    row = table.add_row()
    row.cells[0].text = 'Total'
    row.cells[2].text = f"${ctx['total_with_indirect']:,.0f}"
    row.cells[3].text = f"${ctx['total_actual'] + ctx['indirect_amount']:,.0f}"
    for cell in row.cells:
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.size = Pt(9)

    if ctx['milestones']:
        doc.add_heading('Milestones', level=1)
        for m in ctx['milestones']:
            check = "[x]" if m.get("completed") else "[ ]"
            date_str = f" ({m['date']})" if m.get('date') else ''
            doc.add_paragraph(f"{check} {m.get('name', '')}{date_str}")

    if ctx['reports']:
        doc.add_heading('Reports', level=1)
        for r in reversed(ctx['reports']):
            doc.add_heading(r.get('title', 'Report'), level=2)
            if r.get('date'):
                p = doc.add_paragraph(f"Date: {r['date']}")
                p.runs[0].font.color.rgb = RGBColor(0x99, 0x99, 0x99)
            if r.get('content'):
                for line in r['content'].split('\n'):
                    if line.strip():
                        doc.add_paragraph(line.strip())

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


@export_bp.route("/export/pdf/<proposal_id>")
def export_pdf(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as PDF."""
    if HTML is None:
        return jsonify({"error": GTK3_MISSING_MSG}), 500

    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for PDF export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    html_content = render_template("export_proposal.html", **ctx)

    ensure_export_dir()
    pdf_path = os.path.join(EXPORT_DIR, f"{proposal_id}.pdf")
    HTML(string=html_content, base_url=request.host_url).write_pdf(pdf_path)

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{proposal.title or 'proposal'}.pdf",
    )


@export_bp.route("/export/html/<proposal_id>")
def export_html(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as HTML file."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for HTML export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_export_context(proposal)
    html_content = render_template("export_proposal.html", **ctx)

    return Response(
        html_content,
        mimetype="text/html",
        headers={"Content-Disposition": "inline"},
    )


@export_bp.route("/export/docx/<proposal_id>")
def export_docx(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export proposal as DOCX file."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        logger.warning(f"Proposal not found for DOCX export: {proposal_id}")
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    try:
        buf = _build_proposal_docx(proposal)
    except ImportError:
        return jsonify({"error": "python-docx not installed"}), 500
    except Exception as e:
        logger.error(f"DOCX export failed: {e}")
        return jsonify({"error": f"DOCX export failed: {str(e)}"}), 500

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"{proposal.title or 'proposal'}.docx",
    )


@export_bp.route("/export/tracker/pdf/<proposal_id>")
def export_tracker_pdf(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export tracker as PDF."""
    if HTML is None:
        return jsonify({"error": GTK3_MISSING_MSG}), 500

    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_tracker_export_context(proposal)
    html_content = render_template("export_tracker.html", **ctx)

    ensure_export_dir()
    pdf_path = os.path.join(EXPORT_DIR, f"tracker_{proposal_id}.pdf")
    HTML(string=html_content, base_url=request.host_url).write_pdf(pdf_path)

    return send_file(
        pdf_path,
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


@export_bp.route("/export/tracker/docx/<proposal_id>")
def export_tracker_docx(proposal_id: str) -> Tuple[Response, int] | Response:
    """Export tracker as DOCX."""
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify(ERROR_MESSAGES['PROPOSAL_NOT_FOUND']), 404

    ctx = build_tracker_export_context(proposal)

    try:
        buf = _build_tracker_docx(proposal, ctx)
    except ImportError:
        return jsonify({"error": "python-docx not installed"}), 500
    except Exception as e:
        logger.error(f"Tracker DOCX export failed: {e}")
        return jsonify({"error": f"DOCX export failed: {str(e)}"}), 500

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"{proposal.title or 'project'}_tracker.docx",
    )
