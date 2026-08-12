# AGENTS.md

Flask + HTMX proposal generator for conservation projects. Local single-user app; data stored as JSON on disk. Docs site at 3point.xyz/propongo. Requires Python >= 3.10.

## Commands

- Dev server: `python run.py` (installed deps). Console script `propongo` = `app.main:run_server`.
- Setup: `pip install -e ".[dev]"` (adds pytest, bump2version, build, twine).
- Tests: `pytest` (24 tests, fast). No lint or format tooling is configured — do not invent lint commands.
- Docs: `mkdocs serve` / `mkdocs build` (mkdocs-material + mkdocstrings). Auto-deployed to GitHub Pages on push to `main`.

## Gotchas

- `run.py` runs `fuser -k 5000/tcp` on startup — it silently kills whatever holds port 5000 before serving. DEBUG defaults to True. The debug reloader child (detected via `WERKZEUG_RUN_MAIN`) skips the kill so a file edit doesn't kill the very server the reloader is restarting.
- Data root resolution (`app/models.py`): `PROPONGO_DATA_DIR` env var wins, else `<cwd>/data` if it already has a `proposals/` dir, else `~/Documents/Propongo`. Running `python run.py` or `propongo` from the repo root resolves to `<repo>/data` (proposals/, templates/, snippets/, results/, exports/). NOTE: no path is derived from `__file__` — an installed copy resolves by cwd, never into site-packages.
- Snippets and the results library are user data under the data root (`data/snippets/`, `data/results/`), seeded from package copies (`app/snippets/*.json`, `app/results/library.json`) on first run. Edits via the UI write to the data dir; `app/snippets/custom/` only ships stock files.
- `PUT /api/proposal/<id>` ignores `id`, `title`, and `created_at` (title is changed only via save-as/new-from-template); tasks are merged by id, other top-level fields are overwritten.
- Tests patch `models.PROPOSALS_DIR` via module-level `setup_function`/`teardown_function` (no fixtures); adding tests that touch the data dir should follow the same pattern.
- Environment (miniconda env `propo`): **always `conda activate propo` first — never use base.** The base env (`/opt/miniconda3`) is a separate install and has been stripped of `flask-login`, so `python run.py` there will fail. `propo` is `propongo` installed **non-editable** into `site-packages/app` (must reinstall with `pip install .` after editing source — the console script and server import that copy, not the repo). An old editable `propongo2` hook also maps `app` to a different checkout (`/3-resources/propongo2`), so do NOT switch this repo to `pip install -e .` — the `app` top-level name collides and the wrong checkout wins. `python run.py` from the repo root avoids all of this (cwd precedes site-packages on `sys.path`).

## Structure

- `app/main.py` — all page + API routes in the `create_app()` factory (proposals, tasks, budget, sections, tracker). `app/export.py`, `app/snippets.py`, `app/results.py` are blueprints registered there.
- `app/models.py` — `Proposal` dataclass; tasks/budget items are plain dicts, not dataclasses. Budget timing lives in `budget_item_timings` keyed by item id.
- `app/utils.py` — `build_export_context()` is the single source of truth shared by preview and all exports; `build_budget_by_year()` spreads costs across calendar years.
- Frontend is HTMX + Jinja2 + vanilla JS (`app/static/js/`), no build step. Templates/static/snippets are shipped via `[tool.setuptools.package-data]` — keep that list in sync when adding files.

## Conventions

- i18n: UI strings live in `app/i18n.py` as dicts keyed by the English string (en/es/fr). When adding user-visible text in templates or JS, add matching es/fr keys (JS uses `js_translations`).
- Markdown is rendered with the `markdown` lib + tables/nl2br/fenced_code/sane_lists extensions (`app.main:markdown_to_html`).
- Exports: PDF via WeasyPrint (needs GTK on Windows), DOCX via python-docx. Both degrade to a 500 with a message if libs are missing.

## Releases

- Flow (see `bump.md`): first commit changelog updates, then `bump2version patch|minor|major`. It commits and tags `v{version}`; the tag triggers the PyPI publish workflow.
- Version lives in `pyproject.toml` and `app/__init__.py`; `docs/changelog.md` needs the new `## {version}` header added manually before bumping — bump2version's config writes literal `\n` into that file, so don't rely on it to format the heading.
- The changelog is condensed: one `##` section per minor/major release, with patch bullets merged flat into it (no per-patch `###` headings). After a patch bump, move its bullets into the existing minor section rather than leaving a new `##` header.
