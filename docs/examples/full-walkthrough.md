# Full Walkthrough: Creating a Proposal from Scratch

This guide walks through creating a complete proposal — from a blank slate to an exported PDF.

## 1. Start a New Proposal

1. Open Propongo at [http://localhost:5000](http://localhost:5000).
2. Click **New Proposal**.
3. Enter a title (e.g. "Riparian Restoration — Smith Creek") and click **Create**.

![New proposal button](../img/examples/new-proposal.png)

You are taken to the editor with six tabs: Scope, Budget, Qualifications, Timeline, Custom Sections, and Preview.

## 2. Scope of Work

The Scope tab is where you define the project summary and deliverables.

1. **Funder / Program** — Enter the client or funding program name.
2. **Project Summary** — Write a short Markdown description of the project.
3. **Scope** — Describe the work to be done in detail.
4. **Tasks / Deliverables** — Click **Add Task** and give each task a name and description. These tasks will be referenced in the Budget and Timeline tabs.

![Scope tab](../img/examples/scope-tab.png)

> Markdown is supported in the summary, scope, and task description fields.

## 3. Budget

1. Switch to the **Budget** tab.
2. For each task, add budget items:
   - Select the task from the dropdown.
   - Enter item name, cost per unit, and number of units.
   - Click **Add Item**.
3. Set **Indirect Costs** as a percentage (e.g. 15%).
4. Optionally check **Show budget description** and add notes.

The total updates in real-time at the top of the page.

![Budget tab](../img/examples/budget-tab.png)

## 4. Qualifications

1. Switch to the **Qualifications** tab.
2. Write a Markdown description of your organization's background and relevant experience.
3. Use the **Snippets** sidebar (toggle in the top-left) to insert reusable text like "About Us" or "Mission Statement."

![Qualifications tab](../img/examples/qualifications-tab.png)

## 5. Timeline

1. Switch to the **Timeline** tab.
2. Set the **Start** and **End** month/year for the project.
3. For each task, set:
   - **Lead entity** responsible
   - **Duration** in months
   - **Recurring** options if the task repeats (monthly/quarterly/semi-annually/annually)
4. Optionally toggle **Show duration in days** or **Include budget items**.
5. Click **Update Timeline** to generate the Gantt chart.

The Gantt chart displays colored bars for each task across the project timeline.

![Timeline tab](../img/examples/timeline-tab.png)

## 6. Custom Sections

1. Switch to the **Custom Sections** tab.
2. Click **+ Add Section**, enter a title, and write Markdown content.
3. Use the **Import Excel** button to convert a spreadsheet into a Markdown table section.
4. Use **Move Up / Move Down** to reorder sections as needed.

Custom sections appear in the preview and export in the order you set.

![Custom sections](../img/examples/custom-sections.png)

## 7. Preview & Export

1. Switch to the **Preview** tab to see the full proposal rendered with all sections.
2. Click **Export** → choose **PDF**, **HTML**, or **DOCX**.
3. The PDF includes a cover page, scope, budget table grouped by task, qualifications, custom sections, and a landscape Gantt chart.

![Preview tab](../img/examples/preview-tab.png)

## Next Steps

- Save the proposal as a [template](templates.md) for future reuse.
- Once funded, use the [Project Tracker](tracker.md) to manage progress and spending.
