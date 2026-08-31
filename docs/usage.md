# Usage
Go to [propongo.org](https://propongo.org) to register and sign in. This leads you to the dashboard where your proposals will be saved.

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
3. Enter a title and content using Markdown formatting (see below)
4. Check the formatting in the **Preview** tab before exporting
5. Use ↑ and ↓ buttons to reorder sections
6. Click **Import Excel** to import spreadsheet data as tables

**Excel Import:** Import `.xlsx` or `.xls` files and they'll be automatically converted to Markdown tables. Perfect for budget details, personnel lists, equipment inventories, or any tabular data.

**RFP Import:** Click **Import RFP** to create the sections a funder's request for proposals requires. Each required section is added as a checklist of the RFP's requirements, which you fill in with your project details. Choose the applicant track when the RFP offers more than one, or upload your own RFP sections file (`.json`).

## Markdown Formatting
Section content is written in Markdown and rendered in the **Preview** tab and in PDF, Markdown, and HTML exports. A few basics:

| Result | How to write it |
| --- | --- |
| **Bold** | `**bold text**` |
| *Italic* | `*italic text*` |
| `## Heading` | one to six `#` symbols, e.g. `### Subheading` |
| Bullet list | lines starting with `-` |
| Numbered list | lines starting with `1.`, `2.`, ... |
| Link | `[text](https://example.com)` |

To create a table, use pipe-separated rows with a header separator as follows

```
| Task | Lead | Due |
|------|------|-----|
| Site survey | J. Smith | May 2026 |
```

RFP-imported sections use a few conventions: `**scoring criterion — N points**` is a bold label, and each required element is a `-` bullet. When the RFP suggests a short name for an element it is kept as a bold lead-in, e.g. `- **Deliverables:** List and describe deliverables.`

## Using Snippets
Click the sidebar icon (&#9776;) to open the snippet library. You start with an empty library — add your own reusable snippets and group them by category (e.g. Organization, Deliverables, Team), or import them from `.md`, `.txt`, and `.docx` files.

Click a snippet to insert it at the cursor position in any text field; hover a snippet to edit or delete it.

## Exporting
- **PDF** - Click "⬇️ PDF" to generate a clean, professional PDF document.
- **HTML** - Click "⬇️ HTML" to download a standalone HTML file.
- **Markdown** - Click "⬇️ Markdown" button to generate a markdown file from your proposal.

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

## Map
Documents for producing a GeoLibre map can be found at the [GeoLibre.app](https://geolibre.app/) website.

1. Create the map in GeoLibre after installation or use the [Launch GeoLibre Web](https://geolibre.app/demo/) in the left side panel of the GeoLibre site.
2. Click Project/Share. Before sharing you need to get an API token. Follow the instructions for doing so.
3. Once the token is generated, click share and copy the url link to the map.
4. On the ma page click the pulldown menu under Context layer and select Shared GeoLibre project, then past the url in the box below. Click on Include map in the proposal then click the blue Save map settings button. Your map will appear on the map screen. If it has any large size layers it may take a few seconds for them to render. The map will appear in the Preview and exports. Make sure to enter a caption for the map under Figure caption (optional).

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
