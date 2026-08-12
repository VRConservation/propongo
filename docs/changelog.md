# Changelog

## [Unreleased]

## 1.6.0

Added <br>

- Mapping tab with GeoLibre
- Timeline export as PNG — new "Export PNG" button on the Timeline heading in the preview
- Page numbers in DOCX exports (right-aligned, 9pt gray)
- PDF export page numbers moved to the bottom-right, styled at 9pt gray

Changed <br>

- DOCX timeline now renders as a Gantt chart on a landscape page (colored bars matching the PDF/HTML look instead of block markers)
- Timeline PNG export renders with the same engine as the PDF export (WeasyPrint)

## 1.5.0

Added <br>

- Render deployment support (Dockerfile and render.yaml blueprint)
- User authentication with self-registration and admin accounts
- Admin credentials configurable via environment variables
- Ko-fi donation links

Changed <br>

- User-specific snippets and results library data enabled (seeded from package copies on first run)
- Render deployment upgraded to the Basic plan (adds a persistent disk for proposal data)

Fixed <br>

- Save issues across proposal forms
- French translation corrections
- DOCX export timeline rendering
- Example proposals save correctly
- Seed proposals fixed

## 1.4.0

Added <br>

- Multi-language support — the UI is now available in English, Spanish, and French
- Results library for storing reusable proposal outcomes
- Docker install files (Dockerfile, docker-compose) and installation docs
- Collaboration guide in the docs

Changed <br>

- Budget section improvements (scheduling and by-year breakdown)

Fixed <br>

- Gallery storage location
- Dev server startup now frees port 5000 automatically
- Snippet library loading and save behavior
- Installed package version conflict resolution

## 1.3.0

Added <br>

- Custom sections with Markdown formatting
- Excel import for spreadsheets
- Snippet library for reusable text blocks
- Live Markdown preview for custom sections
- Section reordering with up/down buttons
- Startup message when running propongo command
- Docstrings to all public functions and classes
- API reference documentation via mkdocstrings
- MkDocs documentation site at 3point.xyz/propongo

Changed <br>

- PDF export: reduced landscape margins (1.5cm → 0.8cm), widened task label column (70px → 160px)
- Added Templates section to usage documentation
- Custom regex markdown parser replaced with standard `markdown` library
- Centralized configuration in new `app/config.py`
- Comprehensive logging, type hints, and numeric input validation added
- Removed unused `Task` and `BudgetItem` dataclasses
- `_DATA_ROOT` path unified — no more platform-dependent divergence

Fixed <br>

- Graceful WeasyPrint failure on Windows with GTK3 install link
- Store proposals, templates, and snippets in Documents/Propongo/ instead of site-packages
- Include templates, static files, and snippets in installed package (missing in 1.3.2)
- End date now saves correctly even when no tasks exist (timeline dropdowns were guarded on `#timeline-inputs` which only renders with tasks)
- Timeline Gantt chart, preview, and export no longer enforce a 12-month minimum — actual project duration is respected
- End month now included in chart/preview/export (was off by one)
- Data directory now uses `~/Documents/Propongo/` consistently across all platforms (was `data/` relative to app source on Linux)
- Existing proposals in old `data/` directory are automatically migrated to the new path on first run
- Subtitle field missing from proposal list display on homepage and Switch Proposal modal
- Memory leak from unbounded proposal lock dictionary (switched to `WeakValueDictionary`)
- Duplicate export context code extracted to shared `utils.py`
- Standardized all error messages across the app
- Specific HTTP status codes for Excel import errors (400 vs 500)

Security <br>

- Replaced hardcoded secret key with `FLASK_SECRET_KEY` env var or secure random fallback

## 1.2.0

Added <br>

- Gantt chart timeline visualization
- HTML export

## 1.1.0

Added <br>

- PDF export via WeasyPrint

## 1.0.0

Added <br>

- Initial release
