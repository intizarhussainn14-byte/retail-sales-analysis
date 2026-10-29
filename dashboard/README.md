# Power BI preparation: native report pending

**Portfolio status:** Python, SQL and Excel are complete. The [Excel workbook](../reports/Retail_Sales_Analysis.xlsx) is the main visual deliverable. Power BI Desktop installation is deferred due to limited storage; a native report is optional future work and is not required to publish. Existing assets are preserved.

For a future build, start with [POWER_BI_DESKTOP.md](POWER_BI_DESKTOP.md). It contains the model, exact import steps, measure-creation instructions, three page specifications and reconciliation checklist.

The latest validated package is [powerbi_20261017T174905_392483Z/START_HERE.md](powerbi_20261017T174905_392483Z/START_HERE.md). Its `data/` directory contains six import-ready CSV tables; `power_query/` contains exact M queries. It also includes model_spec.json, retail_theme.json, [three-page layouts](powerbi_20261017T174905_392483Z/REPORT_LAYOUT.md), a measure snapshot and validate_measures.dax for DAX Query view. Model/layout specifications are not native PBIP files.

**Optional future step:** [first manual Desktop step](FIRST_STEP.md). No supported Desktop authoring engine was detected. [Reconciliation evidence](../reports/powerbi_reconciliation.md) records seven matching analysis tables, six filtered scenarios and twelve top-ten checks. Raw, cleaned, audit and Excel hashes were preserved.

No native PBIX or interactive dashboard exists yet. M and DAX have not run in a Power BI engine. The remaining Desktop steps are import, relationships, date-table settings, measures, visuals, slicer checks and Save As PBIX. Python-side checks passed and filtered expected results are included in the package.

Regenerate without replacing earlier packages:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src -p test_prepare_powerbi.py -v
.\.venv\Scripts\python.exe src/prepare_powerbi.py
# Substitute the newly printed package folder:
.\.venv\Scripts\python.exe src/validate_powerbi.py dashboard/POWERBI_RUN
```

Use the newly printed package path after regeneration and update `pDataFolder` in Desktop. Never mix tables from different packages because ProductKey is package-specific.
