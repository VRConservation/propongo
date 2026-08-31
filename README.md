# Propongo
A proposal generator for conservation and natural resource projects available as an app at [propongo.org](https://propongo.org). Create professional proposals in English, French, or Spanish with scope of work, budgets, qualifications, timelines, and export to PDF or HTML. Detailed documentation, examples, and tutorials can be found at https://3point.xyz/propongo. 

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

## Quick Start

### Run as an app
1. Visit [Propongo.org](https://propongo.org)
2. Create a login username and password
3. Start using by clicking on new proposal

### Linux/Mac

```bash
pip install propongo
propongo
```

Opens at [http://localhost:5000](http://localhost:5000)

### Windows

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
   - Run installer; choose "Full installation"
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

### Docker (Mac, Linux, Windows)

A containerized option is provided via `Dockerfile` and `docker-compose.yml`. This avoids installing Python, GTK, and the WeasyPrint system libraries on your host. If you don't have Docker installed yet, follow the steps for your OS below.

#### Install Docker

**Mac** (via Homebrew):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install --cask docker
open -a Docker
```

**Linux** (Ubuntu/Debian; see https://docs.docker.com/engine/install/ for other distros):
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```
Log out and back in (or restart) so the `docker` group takes effect.

**Windows** (via PowerShell, administrator):
```powershell
winget install --id Docker.DockerDesktop
# or: choco install docker-desktop
```

#### Install git

**Mac / Linux:**
```bash
brew install git        # Mac
sudo apt install git    # Linux
```

**Windows:**
```powershell
winget install --id Git.Git
```

#### Run Propongo

Wait until Docker is fully started: run `docker info` and re-run until it completes without error (takes ~30 seconds after Docker starts).

```bash
git clone https://github.com/VRConservation/propongo.git
cd propongo

# Build and start
docker compose up -d --build

# Or with plain docker
docker build -t propongo .
docker run -d -p 5000:5000 -v "$PWD/data:/app/data" propongo
```

Open [http://localhost:5000](http://localhost:5000).

- Proposals, templates, and exports are stored in `./data/` on your host (mounted into the container), so your data persists across restarts and upgrades.
- The container runs as an unprivileged user (uid 1000). If your host user's uid differs, add `user: "${UID}:${GID}"` to the `propongo` service in `docker-compose.yml` (or pass `--user $(id -u):$(id -g)` to `docker run`) so the mounted volume stays writable.
- Stop with `docker compose down`.
- **Port 5000 conflict:** macOS AirPlay Receiver and some Windows services also use port 5000. If the page won't load, change `"5000:5000"` to `"8080:5000"` in `docker-compose.yml`, re-run `docker compose up -d`, and visit http://localhost:8080.

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

**Excel Import:** Import `.xlsx` or `.xls` files, and they'll be automatically converted to Markdown tables. Perfect for budget details, personnel lists, equipment inventories, or any tabular data.

### Using Snippets

Click the sidebar icon (&#9776;) to open the snippet library. You start with an empty library — add your own reusable snippets and group them by category (e.g. Organization, Deliverables, Team), or import them from `.md`, `.txt`, and `.docx` files.

Click a snippet to insert it at the cursor position in any text field; hover a snippet to edit or delete it.

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