# Excel workbook validation

Workbook: [Retail_Sales_Analysis.xlsx](Retail_Sales_Analysis.xlsx). Status: **created, calculated and visually reviewed**.

- Exactly seven requested sheets, four native Excel charts and two native PivotTables.
- 359 reference-cell comparisons passed against the verified Python outputs. Those outputs had already matched all seven MariaDB result tables; local SQL export hashes and comparisons were checked again during workbook preparation.
- Microsoft Excel 16.0 ran CalculateFullRebuild. All 146 workbook formulas have calculated cached results, with zero error values. Both native PivotTable grand totals equal GBP 10,247,219.32 and 19,773 orders.
- All nine rendered print pages across the seven sheets were inspected. Chart clipping, missing axis labels and page scaling discovered in the first draft were corrected. Final page PNGs are pixel-identical to the inspected corrected previews. Preview files and intermediate/backup workbooks are ignored under reports/excel_qa/.
- [Machine-readable evidence](excel_validation.json) records source hashes, workbook hash, checked cells, formula count, engine and native object counts.

The workbook preserves the completed-sales definition, GBP line-rounding policy, boundary-month warnings and known-customer repeat-rate denominator. No source rows were cleaned again or modified.

Native **MonthlySalesPivot** and **CountrySalesPivot** at I5 on their corresponding sheets summarize embedded verified aggregate data. They do not provide transaction-level drill-through, and their filters do not alter Overview KPI formulas. The other blocks are summary tables, not PivotTables. Month/country sums of completed orders are valid because invoice attribution checks passed. The country chart explicitly displays the top ten non-UK markets for readability, while the table and pivot include all countries.

## Reproduce

```powershell
.\.venv\Scripts\python.exe src/build_excel.py --replace
```

The Python builder uses the existing openpyxl dependency (explicitly authorized) and calls [finalize_excel.ps1](../src/finalize_excel.ps1) for native Excel calculation, PivotTables, charts and preview export. Requirements: Windows, installed Excel Desktop, PowerShell and the project's virtual environment. Existing output is archived before --replace installs the new validated workbook. Use --analysis and --sql-evidence only with a matching verified run.

For optional preview rasterization, run [render_excel_pdf.ps1](../src/render_excel_pdf.ps1) with the generated QA folder. It uses Windows' native PDF renderer; no extra Python PDF packages were installed. Recheck visually after changing source lengths, column widths, chart ranges or sheet layout.

**Refresh All is not a Python rerun or CSV reload.** Regenerate the snapshot for new data. Sources includes exact native-pivot recreation and refresh steps. Additional transaction-level/Data Model pivots are optional manual work described in [the Excel guide](excel_refresh_and_pivottables.md); they are not included or claimed as complete.

Completed-sales revenue is **not net revenue**. The 65.27% repeat rate uses 2,829 repeat known customers / 4,334 known customers with eligible sales in this window. Nothing was staged, committed or pushed.

## Portfolio finalization review: 29 October 2026

Excel is the primary visual deliverable for the completed Python/SQL/Excel portfolio. Read-only reinspection confirmed the current workbook SHA-256 matches the recorded validation hash, and all seven reference analysis CSV hashes match the recorded inputs. The saved XLSX package contains four charts, MonthlySalesPivot at I5:K19, CountrySalesPivot at I5:K44, 146 formulas and zero cached error cells. The workbook was not rewritten or recalculated in this review; the earlier native Excel calculation evidence remains applicable to the unchanged file.

All nine saved final Excel-rendered PNG pages across the seven sheets were reviewed again. Labels, monetary formats, chart axes, product rankings, country-chart scope and boundary warnings are legible in those previews. Country Performance and Sources each span two print pages. This review reused the saved previews; it did not perform a new live Excel interaction test. The README now supplies a practical opening and exploration walkthrough. Pivot filters are local and do not control the four summary charts or Overview KPIs. No workbook redesign or new dashboard framework is needed. Power BI remains an optional pending extension.
