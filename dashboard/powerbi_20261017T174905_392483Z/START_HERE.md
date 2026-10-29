# Power BI Desktop import package

No native PBIX was created. These are validated preparation assets and unexecuted M queries. The native Power BI report is pending and optional.

For publication, large generated `data/` imports and the machine-specific `pDataFolder.pq` stay local and are excluded from Git. Regenerate them using the Python workflow below before attempting a future Desktop build. The Excel workbook is the completed visual deliverable.
Follow [the Desktop build guide](../POWER_BI_DESKTOP.md) and use the M queries in `power_query/`.
The shared `pDataFolder` points to this package's `data/` directory. Use all six CSV files as specified.
The `expected_filter_totals.csv` and `expected_filtered_top10.csv` files are reconciliation references,
not preaggregated fact tables. DAX measure definitions are in `../measures.dax`.

This package also includes `model_spec.json` (implementation specification, NOT
a native PBIP model), `REPORT_LAYOUT.md` (three-page manual construction plan),
`retail_theme.json`, a frozen `measures.dax` snapshot, and `validate_measures.dax`
for DAX Query view after creating the measures. Use the snapshot for this run.
Run `src/validate_powerbi.py dashboard/POWERBI_RUN` for additional Python-side
reconciliation against completed SQL/Excel evidence; this does not execute DAX.

[Python-side validation passed](validation.json) for all seven reference tables,
six scenarios and twelve top-ten lists. [First manual step](../FIRST_STEP.md).

Refresh All rereads this package; it does not rerun Python. To package a new validated run:
`.\.venv\Scripts\python.exe src/prepare_powerbi.py --analysis reports/analysis_TIMESTAMP`
then update the pDataFolder query in Desktop and reconcile before saving the PBIX.
