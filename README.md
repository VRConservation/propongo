# Propongo
billy, billy, billy
A local proposal generator for conservation and natural resource projects. Create professional proposals with scope of work, budgets, qualifications, timelines, and export to PDF or HTML. Detailed documentation, examples, and tutorials can be found at https://3point.xyz/propongo. 

## Features

- **Scope of Work** - Define project summary, tasks, and deliverables
- **Budget** - Line-item budgeting with cost/unit calculations, totals, and indirect costs
- **Qualifications** - Document team background and relevant experience
- **Timeline** - Auto-derived task timing from budget items with Gantt chart visualization
- **Custom Sections** - Add unlimited custom sections with Markdown formatting (NEW!)
- **Excel Import** - Import Excel spreadsheets as formatted tables into custom sections (NEW!)
- **Preview** - View the complete proposal with task-grouped budget and timeline bars
- **PDF Export** - Clean, professional PDF output via WeasyPrint
- **HTML Export** - Standalone HTML file with embedded styles
- **Snippet Library** - Reusable markdown components for organization descriptions, deliverable templates, and custom content
- **Save/Load** - Proposals stored as JSON files on disk, auto-save as you work

## Quick Start

### Install from PyPI (Linux/Mac)

```bash
pip install propongo
propongo
```

Opens at [http://localhost:5000](http://localhost:5000)

### Windows Installation

**Recommended:** Use a virtual environment to avoid conflicts with system Python.

1. **Create virtual environment with Anaconda/Miniconda** (recommended)
   ```powershell
   # Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
   conda create -n propongo python=3.10
   conda activate propongo
   ```
   
   ⚠️ **Warning:** Installing to base Python can cause package conflicts. [Learn about Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for better Python environment management.

2. **Install GTK3 Runtime** (for MS Windows users: required for PDF export)
   - Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/
   - Run installer, choose "Full installation"
   - Restart your computer

3. **Install Propongo**
   ```powershell
   pip install propongo
   ```

4. **Run the application**
   ```powershell
   propongo
   ```
   
5. **Open browser** to http://localhost:5000

**Troubleshooting:** If PDF export fails, ensure GTK3 is in your PATH. If Excel import doesn't work, run: `pip install pandas openpyxl tabulate`

### Install from source

```bash
git clone https://github.com/VRConservation/propongo.git
cd propongo
pip install -e .
propongo
```

### Development setup

```bash
git clone https://github.com/VRConservation/propongo.git
cd propongo
pip install -e ".[dev]"
python run.py
```

## Usage

### Creating a Proposal

1. Click **New Proposal** from the dashboard
2. Enter a title and optional client name in the header
3. Work through each tab:

   **Scope** - Add a project summary, then create tasks/deliverables with descriptions and a lead entity

   **Budget** - Select a task, enter line items with cost per unit and quantities. Totals and indirect costs calculate automatically.

   **Qualifications** - Describe your organization's background and why you're qualified for this project

   **Timeline** - Set project start date and view the auto-derived Gantt chart. Adjust budget item timing and lead entities as needed.

   **Custom Sections** - Add unlimited custom sections with Markdown formatting. Import Excel spreadsheets as formatted tables.

   **Preview** - Review the complete proposal with task-grouped budget and timeline before exporting

### Using Custom Sections (NEW!)

Add custom sections to your proposal for any additional content:

1. Click the **Custom Sections** tab
2. Click **+ Add Section** to create a new section
3. Enter a title and content using Markdown formatting
4. See a live preview of your formatted content
5. Use ↑ and ↓ buttons to reorder sections
6. Click **📊 Import Excel** to import spreadsheet data as tables

**Excel Import:** Import `.xlsx` or `.xls` files and they'll be automatically converted to Markdown tables. Perfect for budget details, personnel lists, equipment inventories, or any tabular data.

### Using Snippets

Click the sidebar icon (&#9776;) to open the snippet library:

- **Organization** - Pre-written organization descriptions
- **Deliverables** - Templates for common deliverable types (surveys, assessments, plans)
- **Custom** - Create and save your own reusable snippets

Click a snippet to insert it at the cursor position in any text field.

### Exporting

- **PDF** - Click "Export PDF" to generate a clean, professional PDF document
- **HTML** - Click "Export HTML" to download a standalone HTML file
- **Print** - Use Ctrl+P / Cmd+P in the Preview tab for browser printing

### Managing Proposals

- Proposals auto-save as you work
- Click "Proposals" in the header to see all saved proposals
- Create, edit, or delete proposals from the dashboard

## Updating

### From PyPI

```bash
pip install --upgrade propongo
```

### From source

```bash
cd propongo
git pull
pip install -e .
```

## Development

### Run tests

```bash
pytest
```

## Project Structure

```
propongo/
├── run.py                      # Dev entry point
├── pyproject.toml              # Package config
├── requirements.txt            # Dependencies
├── app/
│   ├── __init__.py             # Version
│   ├── main.py                 # Flask app + routes
│   ├── models.py               # Proposal data model
│   ├── export.py               # PDF/HTML export
│   ├── snippets.py             # Snippet management
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html           # Layout + HTMX
│   │   ├── index.html          # Proposal dashboard
│   │   ├── scope.html          # Scope editor
│   │   ├── budget.html         # Budget editor
│   │   ├── qualifications.html # Qualifications editor
│   │   ├── timeline.html       # Timeline + Gantt
│   │   ├── preview.html        # Proposal preview
│   │   └── export_proposal.html# PDF export template
│   ├── static/
│   │   ├── css/style.css       # All styles
│   │   └── js/
│   │       ├── app.js          # Core JS + HTMX helpers
│   │       ├── budget.js       # Budget calculations
│   │       ├── gantt.js        # Gantt chart rendering
│   │       └── snippets.js     # Snippet panel logic
│   ├── snippets/               # Stock snippet data
│   │   ├── organization.json
│   │   ├── deliverables.json
│   │   └── custom/             # User-created snippets
│   └── data/
│       ├── proposals/          # Saved proposals (JSON)
│       └── exports/            # Generated PDF/HTML exports
└── tests/
    ├── test_main.py
    └── test_export.py
```

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTMX, Jinja2, vanilla CSS/JS
- **PDF Export:** WeasyPrint
- **Packaging:** pyproject.toml, setuptools

## License

MIT