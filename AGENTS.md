# AGENTS.md

Flask + HTMX proposal generator for conservation projects. Data stored as JSON on disk. Docs site at 3point.xyz/propongo. Requires Python >= 3.10.

## Commands

- Dev server: `python run.py` (installed deps). Console script `propongo` = `app.main:run_server`.
- Setup: `pip install -e ".[dev]"` (adds pytest, bump2version, build, twine).
- Tests: `pytest` (113 tests, fast). No lint or format tooling is configured — do not invent lint commands.
- Docs: `mkdocs serve` / `mkdocs build` (mkdocs-material + mkdocstrings). Auto-deployed to GitHub Pages on push to `main`.

## Gotchas

- `run.py` runs `fuser -k 5000/tcp` on startup — it silently kills whatever holds port 5000 before serving. DEBUG defaults to True. The debug reloader child (detected via `WERKZEUG_RUN_MAIN`) skips the kill so a file edit doesn't kill the very server the reloader is restarting.
- Data root resolution (`app/models.py`): `PROPONGO_DATA_DIR` env var wins, else `<cwd>/data` if it already has a `proposals/` dir, else `~/Documents/Propongo`. Running `python run.py` or `propongo` from the repo root resolves to `<repo>/data` (proposals/, templates/, snippets/, results/, exports/). NOTE: no path is derived from `__file__` — an installed copy resolves by cwd, never into site-packages.
- Snippets and the results library are user data under the data root (`data/snippets/`, `data/results/`). The results library seeds itself from the package copy (`app/results/library.json`) on first run; snippets ship no stock content — a fresh install starts empty. Snippet categories are free-form labels stored on each snippet; `organization`/`deliverables` list files are legacy storage still honored for old data. Edits via the UI write to the data dir.
- `PUT /api/proposal/<id>` ignores `id`, `title`, and `created_at` (title is changed only via save-as/new-from-template); tasks are merged by id, other top-level fields are overwritten.
- Auth exists and is multi-user-capable, but **disabled by default**: gate is `PROPONGO_AUTH_ENABLED` (`app/auth.py`, `app/models.py:_auth_enabled`), defaulting to `false`. When off it behaves as a local single-user install; when on, a `before_request` hook redirects unauthenticated users and data dirs are scoped per-username (`_scoped_dir()`). Users live in a JSON file (`users.json`) — there is **no database**, no sqlite, no SQLAlchemy.
- Budget timing lives **on the budget item dict** (`BUDGET_TIMING_FIELDS` in `app/models.py`: `start_month`, `start_year`, `duration_months`, `lead_entity`, `recurring`, `recurring_interval`, `actual_cost`). It used to be a parallel `budget_item_timings` dict keyed by item id; that key is now a **derived compatibility property** — reading it builds the dict from the items, assigning to it folds the incoming dict back into them (merge, never wholesale replace, so a partial payload can't wipe other items' timing or their `actual_cost`). `from_dict` still accepts the legacy key and migrates it, so old on-disk files keep working; it is never written back out. Don't reintroduce a second source of truth.
- A budget item is **scheduled** only if it has both `start_month` and `start_year` — use `models.item_is_scheduled()`, not a truthiness check on the timing dict. Missing either means unscheduled, which is what `build_budget_by_year()` reports in its `unscheduled` bucket so totals reconcile; `models.clear_item_timing()` is how the budget PUT route returns an item to that state. Never leave a zero-duration schedule behind as a proxy for "unset".
- Schedule fields are written by two paths that must agree: the budget tab (`POST`/`PUT /api/budget/...`) and the timeline tab (`PUT /api/proposal/<id>`, via `gantt.js`/`app.js` posting `budget_item_timings`). Shared fields go through `main._apply_item_schedule()`; if you add a field, wire it in both or the two tabs will disagree.
- Copying a proposal (`save-as`, `save-as-template`, `new-from-template`) must use `models.copy_budget_items()`. A plain `list(items)` shares the dicts, so editing the copy's schedule would reach back into the original.
- Tests patch `models.PROPOSALS_DIR` via module-level `setup_function`/`teardown_function` (no fixtures); adding tests that touch the data dir should follow the same pattern.
- Environment (miniconda env `propo`): **always `conda activate propo` first — never use base.** The base env (`/opt/miniconda3`) is a separate install and has been stripped of `flask-login`, so `python run.py` there will fail. `propo` is `propongo` installed **non-editable** into `site-packages/app` (must reinstall with `pip install .` after editing source — the console script and server import that copy, not the repo). An old editable `propongo2` hook also maps `app` to a different checkout (`/3-resources/propongo2`), so do NOT switch this repo to `pip install -e .` — the `app` top-level name collides and the wrong checkout wins. `python run.py` from the repo root avoids all of this (cwd precedes site-packages on `sys.path`).

## Structure

- `app/main.py` — all page + API routes in the `create_app()` factory (proposals, tasks, budget, sections, tracker). `app/export.py`, `app/snippets.py`, `app/results.py` are blueprints registered there.
- `app/models.py` — `Proposal` dataclass; tasks/budget items are plain dicts, not dataclasses. Budget-item timing is stored on the item itself; `budget_item_timings` survives only as a derived legacy view (see gotchas).
- `app/utils.py` — `build_export_context()` is the single source of truth shared by preview and all exports; `build_budget_by_year()` spreads costs across calendar years.
- Frontend is HTMX + Jinja2 + vanilla JS (`app/static/js/`), no build step. Templates/static are shipped via `[tool.setuptools.package-data]` — keep that list in sync when adding files.

## Conventions

- i18n: UI strings live in `app/i18n.py` as dicts keyed by the English string (en/es/fr). When adding user-visible text in templates or JS, add matching es/fr keys (JS uses `js_translations`).
- Markdown is rendered with the `markdown` lib + tables/nl2br/fenced_code/sane_lists extensions (`app.main:markdown_to_html`).
- Exports: PDF is the HTML export printed via WeasyPrint (self-contained, no headless browser; degrades to a 500 message if missing). Markdown via html2text. Timeline PNG uses WeasyPrint onto a content-sized page, rasterized with pypdfium2 (needs GTK on Windows). Playwright is **not** part of export — it is used only to screenshot the GeoLibre map embed (`app/utils.py`).

## Releases

- Flow (see `bump.md`): first commit changelog updates, then `bump2version patch|minor|major`. It commits and tags `v{version}`; the tag triggers the PyPI publish workflow.
- Version lives in `pyproject.toml` and `app/__init__.py`; `docs/changelog.md` needs the new `## {version}` header added manually before bumping — bump2version's config writes literal `\n` into that file, so don't rely on it to format the heading.
- The changelog is condensed: one `##` section per minor/major release, with patch bullets merged flat into it (no per-patch `###` headings). After a patch bump, move its bullets into the existing minor section rather than leaving a new `##` header.
