[![image](https://img.shields.io/pypi/v/propongo.svg)](https://pypi.org/project/propongo/)

# Welcome to Propongo
[Propongo](https://propongo.org) is a proposal generator for conservation and natural resource projects. Create professional proposals with scope of work, budgets, qualifications, timelines, and export to PDF, Word, or HTML. The app features English, French, and Spanish versions. See the Examples section to get started and more details on how to usee the app.

## Features
- **Scope of Work** - Define project summary, tasks, and deliverables
- **Budget** - Line-item budgeting with cost/unit calculations, totals, and indirect costs
- **Qualifications** - Document team background and relevant experience
- **Timeline** - Auto-derived task timing from budget items with Gantt chart visualization
- **Custom Sections** - Add unlimited custom sections with Markdown formatting
- **Map** - Experimental map page allows import of project map from GeoLibre or as a png/jpg
- **Preview** - View the complete proposal with task-grouped budget and timeline bars and export your proposla as a HTML, PDF, or Markdown file.
- **Snippet Library** - Reusable markdown components for organization descriptions, deliverable templates, and custom content
- **Import** - Import a pdf of an RFP to the custom section and it will read then add required sections or import Excel spreadsheets as formatted tables into custom sections
- **Project tracking** - When a proposal is secured, use the tracking feature to manage project deliverables, timeline, and budget spend.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTMX, Jinja2, vanilla CSS/JS
- **PDF Export:** WeasyPrint
- **Packaging:** pyproject.toml, setuptools
