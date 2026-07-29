[![image](https://img.shields.io/pypi/v/geodev.svg)](https://pypi.org/project/propongo2/)

# Welcome to Propongo

A local proposal generator for conservation and natural resource projects. Create professional proposals with scope of work, budgets, qualifications, timelines, and export to PDF or HTML.

## Features

- **Scope of Work** - Define project summary, tasks, and deliverables
- **Budget** - Line-item budgeting with cost/unit calculations, totals, and indirect costs
- **Qualifications** - Document team background and relevant experience
- **Timeline** - Auto-derived task timing from budget items with Gantt chart visualization
- **Custom Sections** - Add unlimited custom sections with Markdown formatting
- **Excel Import** - Import Excel spreadsheets as formatted tables into custom sections
- **Preview** - View the complete proposal with task-grouped budget and timeline bars
- **PDF Export** - Clean, professional PDF output via WeasyPrint
- **HTML Export** - Standalone HTML file with embedded styles
- **Snippet Library** - Reusable markdown components for organization descriptions, deliverable templates, and custom content
- **Save/Load** - Proposals stored as JSON files on disk, auto-save as you work

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTMX, Jinja2, vanilla CSS/JS
- **PDF Export:** WeasyPrint
- **Packaging:** pyproject.toml, setuptools
