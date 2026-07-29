# Timeline & Gantt Chart Guide

The Timeline tab lets you schedule tasks across months and generates an interactive Gantt chart.

## Setting Up the Timeline

1. Switch to the **Timeline** tab.
2. Set **Project Start** and **Project End** month/year using the dropdowns.
3. Each task (from the Scope tab) appears in the task list with scheduling options:

   - **Lead entity** — who is responsible
   - **Duration** — how many months the task spans (auto-calculated from start/end, or set manually)
   - **Recurring** — check this for repeating tasks and set the interval (monthly, quarterly, semi-annually, annually)

## Budget Items in the Timeline

Toggle **Include budget items** to show individual budget line items in the timeline. Each item can have its own start, lead, and duration independent of the parent task.

## Display Options

- **Show duration in days** — switches bar labels from months to days.
- **Update Timeline** — re-renders the Gantt chart after changes.

## Gantt Chart

The chart displays:

- A **year row** with gray year labels
- **Month columns** (Jan, Feb, Mar...)
- **Task bars** — colored horizontal bars positioned by start month with length equal to duration
- **Budget sub-item bars** — lighter indented bars (when budget items are included)
- **Recurring bars** — multiple bars at regular intervals

The chart is interactive — changes to task scheduling update the chart in real-time.

## In Preview & Export

The Gantt chart renders on a landscape page in PDF exports, showing all tasks and budget items across the full project timeline.
