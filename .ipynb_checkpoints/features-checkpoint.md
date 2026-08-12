# Feature Suggestions & Windows Setup

## 1. Adding Custom Sections to Proposals

### Overview
Currently, Propongo has fixed sections: Scope, Budget, Qualifications, Timeline, and Preview. To add user-customizable sections, here's a recommended approach:

### Implementation Strategy

#### A. Data Model Changes (`app/models.py`)

Add a `custom_sections` field to the `Proposal` dataclass:

```python
@dataclass
class Proposal:
    # ... existing fields ...
    custom_sections: list = field(default_factory=list)
    # Each section: {"id": str, "title": str, "content": str, "order": int}
```

#### B. Backend Routes (`app/main.py`)

Add routes for managing custom sections:

```python
@app.route("/custom-sections/<proposal_id>")
def custom_sections_tab(proposal_id):
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify({"error": "Not found"}), 404
    sections = sorted(
        proposal.custom_sections, 
        key=lambda s: s.get("order", 0)
    )
    return render_template(
        "custom_sections.html", 
        proposal=proposal, 
        sections=sections
    )

@app.route("/api/section/<proposal_id>", methods=["POST"])
def add_section(proposal_id):
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    new_section = {
        "id": str(_uuid.uuid4()),
        "title": data.get("title", "New Section"),
        "content": data.get("content", ""),
        "order": len(proposal.custom_sections)
    }
    proposal.custom_sections.append(new_section)
    proposal.save()
    return jsonify(new_section), 201

@app.route("/api/section/<proposal_id>/<section_id>", methods=["PUT"])
def update_section(proposal_id, section_id):
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    for section in proposal.custom_sections:
        if section["id"] == section_id:
            section.update({
                "title": data.get("title", section["title"]),
                "content": data.get("content", section["content"]),
                "order": data.get("order", section.get("order", 0))
            })
            break
    
    proposal.save()
    return jsonify({"ok": True})

@app.route("/api/section/<proposal_id>/<section_id>", methods=["DELETE"])
def delete_section(proposal_id, section_id):
    proposal = Proposal.load(proposal_id)
    if not proposal:
        return jsonify({"error": "Not found"}), 404
    
    proposal.custom_sections = [
        s for s in proposal.custom_sections 
        if s["id"] != section_id
    ]
    proposal.save()
    return jsonify({"ok": True})
```

#### C. Frontend Template (`app/templates/custom_sections.html`)

Create a new template:

```html
<div class="section">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2>Custom Sections</h2>
        <button class="btn btn-primary" onclick="addCustomSection('{{ proposal.id }}')">
            + Add Section
        </button>
    </div>

    <div id="custom-sections-list">
        {% for section in sections %}
        <div class="custom-section-card" data-section-id="{{ section.id }}" style="margin-bottom: 20px; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <input type="text" 
                       class="section-title-input" 
                       value="{{ section.title }}"
                       placeholder="Section Title"
                       style="font-size: 18px; font-weight: 600; border: 1px solid #e2e8f0; padding: 8px; width: 70%;"
                       onchange="updateSection('{{ proposal.id }}', '{{ section.id }}')">
                
                <div style="display: flex; gap: 8px;">
                    <button class="btn-icon" onclick="moveSectionUp('{{ proposal.id }}', '{{ section.id }}')" title="Move Up">↑</button>
                    <button class="btn-icon" onclick="moveSectionDown('{{ proposal.id }}', '{{ section.id }}')" title="Move Down">↓</button>
                    <button class="btn-icon btn-danger-icon" onclick="deleteSection('{{ proposal.id }}', '{{ section.id }}')" title="Delete">×</button>
                </div>
            </div>

            <textarea class="section-content-input" 
                      rows="8"
                      placeholder="Enter section content (Markdown supported)..."
                      onchange="updateSection('{{ proposal.id }}', '{{ section.id }}')"
                      style="width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 4px;">{{ section.content }}</textarea>
            
            <div class="markdown-preview" style="margin-top: 12px; padding: 12px; background: #f8fafc; border-radius: 4px;">
                <strong>Preview:</strong>
                {{ section.content | md }}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

#### D. JavaScript Functions (`app/static/js/app.js`)

Add these functions:

```javascript
async function addCustomSection(proposalId) {
    const response = await fetch(`/api/section/${proposalId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: 'New Section',
            content: ''
        })
    });
    
    if (response.ok) {
        // Reload the custom sections tab
        const btn = document.querySelector('[onclick*="custom-sections"]');
        if (btn) await switchTab(proposalId, 'custom-sections', btn);
    }
}

async function updateSection(proposalId, sectionId) {
    const card = document.querySelector(`[data-section-id="${sectionId}"]`);
    const title = card.querySelector('.section-title-input').value;
    const content = card.querySelector('.section-content-input').value;
    
    await fetch(`/api/section/${proposalId}/${sectionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
    });
}

async function deleteSection(proposalId, sectionId) {
    if (!confirm('Delete this section?')) return;
    
    await fetch(`/api/section/${proposalId}/${sectionId}`, {
        method: 'DELETE'
    });
    
    // Reload the custom sections tab
    const btn = document.querySelector('[onclick*="custom-sections"]');
    if (btn) await switchTab(proposalId, 'custom-sections', btn);
}

async function moveSectionUp(proposalId, sectionId) {
    // Implementation for reordering sections
    // Load all sections, swap orders, update all
}

async function moveSectionDown(proposalId, sectionId) {
    // Implementation for reordering sections
}
```

#### E. Update Base Template (`app/templates/base.html`)

Add a tab for Custom Sections in the navigation:

```html
<button class="tab-btn" onclick="switchTab('{{ proposal.id }}', 'custom-sections', this)">
    Custom Sections
</button>
```

And update the `switchTab` function in app.js to include:

```javascript
const routes = {
    scope: '/scope/',
    budget: '/budget/',
    qualifications: '/qualifications/',
    timeline: '/timeline/',
    'custom-sections': '/custom-sections/',  // Add this
    preview: '/preview/'
};
```

#### F. Update Export Templates

Modify `app/templates/export_proposal.html` to include custom sections:

```html
{% if proposal.custom_sections %}
    {% for section in proposal.custom_sections | sort(attribute='order') %}
    <div class="section">
        <h2>{{ section.title }}</h2>
        <div class="content">
            {{ section.content | md }}
        </div>
    </div>
    {% endfor %}
{% endif %}
```

### Alternative: Simpler Implementation

If you want a simpler approach without full section management:

1. **Add a single "Additional Sections" field** to the Proposal model
2. Use a format like `## Section Title\nContent\n\n## Another Section\nMore content`
3. Parse this during export to create multiple sections
4. Provide a single textarea with Markdown formatting tips

---

## 2. Windows Installation & Usage Guide

### Prerequisites

Windows users need:
- **Python 3.10 or higher** ([Download](https://www.python.org/downloads/))
- **GTK for Windows** (required by WeasyPrint for PDF generation)

### Step-by-Step Installation

#### Option 1: Install from PyPI (Recommended for Users)

1. **Install Python**
   - Download Python from [python.org](https://www.python.org/downloads/)
   - During installation, **check "Add Python to PATH"**
   - Verify installation:
     ```powershell
     python --version
     ```

2. **Install GTK3 Runtime** (for PDF export)
   - Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Run the installer
   - Choose "Full installation"
   - **Restart your computer** after installation

3. **Install Propongo**
   ```powershell
   pip install propongo
   ```

4. **Run Propongo**
   ```powershell
   propongo
   ```
   
   The application will start at `http://localhost:5000`
   Open this URL in your web browser.

#### Option 2: Install from Source (For Developers)

1. **Install Python and GTK** (as above)

2. **Install Git for Windows**
   - Download from: https://git-scm.com/download/win

3. **Clone the Repository**
   ```powershell
   git clone https://github.com/VRConservation/propongo.git
   cd propongo
   ```

4. **Create a Virtual Environment** (recommended)
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

5. **Install in Development Mode**
   ```powershell
   pip install -e .
   ```
   
   Or for development with testing tools:
   ```powershell
   pip install -e ".[dev]"
   ```

6. **Run the Application**
   ```powershell
   python run.py
   ```
   
   Or:
   ```powershell
   propongo
   ```

### Troubleshooting Windows Issues

#### PDF Export Not Working

**Problem:** WeasyPrint errors when exporting to PDF

**Solution:**
1. Ensure GTK3 is installed (see Step 2 above)
2. Add GTK to your PATH:
   - Open System Properties → Environment Variables
   - Edit PATH variable
   - Add: `C:\Program Files\GTK3-Runtime Win64\bin` (or your GTK install location)
3. Restart your terminal/PowerShell

#### Port Already in Use

**Problem:** `Address already in use` error

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

Or run on a different port:
```powershell
# Edit run.py to change the port
# Or set environment variable
$env:FLASK_RUN_PORT=5001
python run.py
```

#### Permission Errors

**Problem:** Cannot save proposals

**Solution:**
- Run PowerShell as Administrator, or
- Install in a user directory (not Program Files)
- Check that `data/proposals` directory has write permissions

### Creating a Windows Shortcut

1. Create a batch file `start_propongo.bat`:
   ```batch
   @echo off
   call C:\path\to\your\venv\Scripts\activate.bat
   propongo
   pause
   ```

2. Create a shortcut to this batch file
3. Right-click shortcut → Properties → Change Icon
4. Pin to Start Menu or Taskbar

### Building a Windows Executable (Advanced)

To create a standalone `.exe` for distribution:

1. **Install PyInstaller**
   ```powershell
   pip install pyinstaller
   ```

2. **Create the executable**
   ```powershell
   pyinstaller --onefile --windowed --name Propongo run.py
   ```

3. **Package with dependencies**
   - Copy the `app` folder to `dist/`
   - Copy `data` folder to `dist/`
   - Include GTK runtime DLLs

4. **Create an installer** using:
   - Inno Setup: https://jrsoftware.org/isinfo.php
   - NSIS: https://nsis.sourceforge.io/

### System Requirements (Windows)

- **OS:** Windows 10 or 11 (64-bit)
- **RAM:** 2GB minimum, 4GB recommended
- **Disk Space:** 500MB for application and dependencies
- **Browser:** Chrome, Firefox, or Edge (modern versions)

### Additional Windows Notes

1. **Firewall:** You may need to allow Python through Windows Firewall
2. **Antivirus:** Some antivirus software may flag the executable on first run
3. **WSL Alternative:** You can also run Propongo in Windows Subsystem for Linux
4. **Docker:** Consider using Docker Desktop for Windows for easier deployment

---

## Summary

**For Custom Sections:**
- Implement a flexible data model with section title, content, and ordering
- Use markdown for rich text formatting
- Allow users to add/edit/delete/reorder sections
- Include in PDF/HTML exports

**For Windows Users:**
- Python 3.10+ and GTK3 Runtime are essential
- PyPI installation is simplest for end users
- Source installation gives more control for developers
- WeasyPrint can be tricky on Windows but GTK3 installation solves most issues
