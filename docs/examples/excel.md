# Excel Import Guide

Propongo supports importing Excel files in two places: the Budget tab and the Custom Sections tab.

## Importing a Budget

1. Switch to the **Budget** tab.
2. Click **Import Excel**.
3. Your spreadsheet must have these four columns (header names are case-insensitive):

   | Column | Description | Example |
   |---|---|---|
   | **Task** | Task name (creates new tasks if needed) | "Field Surveys" |
   | **Item** | Line item name | "Field Technician" |
   | **Cost/Unit** | Cost per unit | 45.00 |
   | **Units** | Number of units | 80 |

4. Select your `.xlsx` or `.xls` file and upload.

All items are created under their respective tasks. Existing tasks are reused; new tasks are auto-created.

### Download a Template

Click **Download Template** on the Budget tab to get a sample `.xlsx` with the correct columns.

## Importing a Spreadsheet as a Custom Section

1. Switch to the **Custom Sections** tab.
2. Click **Import Excel**.
3. Select any `.xlsx` or `.xls` file.
4. The spreadsheet is converted to a Markdown table and added as a new custom section.

This is useful for presenting data tables directly in the proposal.

## Requirements

- Install `pandas` and `openpyxl` if not already present:
  ```bash
  pip install pandas openpyxl tabulate
  ```
- These are included when you `pip install propongo`.
