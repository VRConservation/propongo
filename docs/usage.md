# Usage

## Creating a Proposal

1. Click **New Proposal** from the dashboard
2. Enter a title and optional client name in the header
3. Work through each tab:

    **Scope** - Add a project summary, then create tasks/deliverables with descriptions and a lead entity

    **Budget** - Select a task, enter line items with cost per unit and quantities. Totals and indirect costs calculate automatically.

    **Qualifications** - Describe your organization's background and why you're qualified for this project

    **Timeline** - Set project start date and view the auto-derived Gantt chart. Adjust budget item timing and lead entities as needed.

    **Custom Sections** - Add unlimited custom sections with Markdown formatting. Import Excel spreadsheets as formatted tables.

    **Preview** - Review the complete proposal with task-grouped budget and timeline before exporting as a pdf, word, or html file.

## Using Custom Sections

Add custom sections to your proposal for any additional content:

1. Click the **Custom Sections** tab
2. Click **+ Add Section** to create a new section
3. Enter a title and content using Markdown formatting
4. See a live preview of your formatted content
5. Use ↑ and ↓ buttons to reorder sections
6. Click **Import Excel** to import spreadsheet data as tables

**Excel Import:** Import `.xlsx` or `.xls` files and they'll be automatically converted to Markdown tables. Perfect for budget details, personnel lists, equipment inventories, or any tabular data.

## Using Snippets

Click the sidebar icon (&#9776;) to open the snippet library:

- **Organization** - Pre-written organization descriptions
- **Deliverables** - Templates for common deliverable types (surveys, assessments, plans)
- **Custom** - Create and save your own reusable snippets

Click a snippet to insert it at the cursor position in any text field.

## Exporting

- **PDF** - Click "Export PDF" to generate a clean, professional PDF document
- **HTML** - Click "Export HTML" to download a standalone HTML file
- **Print** - Use Ctrl+P / Cmd+P in the Preview tab for browser printing

## Managing Proposals

- Proposals auto-save as you work
- Click "Proposals" in the header to see all saved proposals
- Create, edit, or delete proposals from the dashboard

## Using Templates

Reuse proposal structures by saving them as templates:

1. **Save a template** — In the editor, click the menu (&#9776;) and select **Save as Template**. Give it a name and optional category.
2. **Browse templates** — Click **Templates** from the dashboard or the editor menu to see all saved templates.
3. **Create from template** — Click **Use Template** on any template card to create a new proposal pre-populated with all tasks, budget items, sections, and timeline settings from that template.
4. **Delete templates** — Click **Delete** on any template card to remove it.

Templates preserve: scope, tasks, budget items, qualifications, custom sections, timeline settings, and budget timing. Client-specific fields like title and client name are left blank for the new proposal.

## Updating
### From PyPI

```bash
pip install --upgrade propongo2
```

### From source

```bash
cd propongo2
git pull
pip install -e .
```
