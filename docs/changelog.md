# Changelog

## [Unreleased]\n\n## 1.5.1\n\n## 1.5.0\n\n## 1.4.2\n\n## 1.4.1\n\n## 1.4.0


## 1.3.6

Fixed <br>
- Data directory now uses `~/Documents/Propongo/` consistently across all platforms (was `data/` relative to app source on Linux)
- Existing proposals in old `data/` directory are automatically migrated to the new path on first run
- Subtitle field missing from proposal list display on homepage and Switch Proposal modal

Changed <br>
- `_DATA_ROOT` path unified — no more platform-dependent divergence


## 1.3.5

Security <br>
- Replaced hardcoded secret key with `FLASK_SECRET_KEY` env var or secure random fallback

Fixed <br>
- Memory leak from unbounded proposal lock dictionary (switched to `WeakValueDictionary`)
- Duplicate export context code extracted to shared `utils.py`
- Standardized all error messages across the app
- Specific HTTP status codes for Excel import errors (400 vs 500)

Changed <br>
- Custom regex markdown parser replaced with standard `markdown` library
- Centralized configuration in new `app/config.py`
- Comprehensive logging, type hints, and numeric input validation added
- Removed unused `Task` and `BudgetItem` dataclasses

## 1.3.4

Fixed <br>
- End date now saves correctly even when no tasks exist (timeline dropdowns were guarded on `#timeline-inputs` which only renders with tasks)
- Timeline Gantt chart, preview, and export no longer enforce a 12-month minimum — actual project duration is respected
- End month now included in chart/preview/export (was off by one)

Changed <br>
- PDF export: reduced landscape margins (1.5cm → 0.8cm), widened task label column (70px → 160px)
- Added Templates section to usage documentation

## 1.3.3

Fixed <br>
- Include templates, static files, and snippets in installed package (missing in 1.3.2)

## 1.3.2

Fixed <br>
- Graceful WeasyPrint failure on Windows with GTK3 install link
- Store proposals, templates, and snippets in Documents/Propongo/ instead of site-packages

Added <br>
- Docstrings to all public functions and classes
- API reference documentation via mkdocstrings
- MkDocs documentation site at 3point.xyz/propongo

## 1.3.1

Added <br>
- Startup message when running propongo command

## 1.3.0

Added <br>
- Custom sections with Markdown formatting
- Excel import for spreadsheets
- Snippet library for reusable text blocks
- Live Markdown preview for custom sections
- Section reordering with up/down buttons

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
