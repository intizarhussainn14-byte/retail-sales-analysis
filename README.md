# Retail Sales Analysis | Python, SQL and Excel

A completed analytics portfolio using Python/pandas for data preparation and analysis, SQL executed on MariaDB for independent reconciliation, and Excel as the main visual deliverable. Preserved Power BI preparation assets are an optional extension; the native Power BI report is pending. Power BI Desktop is not required to open, explore or publish this portfolio.

**Verified result: £10,247,219.32 in completed-sales revenue across 19,773 orders.** This excludes cancellations and negative adjustments and is **not net revenue or profit**.

## Open and explore the Excel deliverable

1. Download [Retail_Sales_Analysis.xlsx](reports/Retail_Sales_Analysis.xlsx). On GitHub, open the file and use **Download raw file**, then open the downloaded `.xlsx` in Microsoft Excel Desktop. GitHub does not run its charts or PivotTables. No Python, database server or Power BI installation is needed to view the saved workbook.
2. Start on **Overview** for reconciled KPIs and metric definitions. Use the worksheet tabs along the bottom; scroll horizontally if a PivotTable is off-screen.
3. Open **Monthly Sales** for the revenue line chart and observed versus comparable monthly changes. December 2011 is partial; December 2010 completeness is unverified.
4. Open **Top Products** for separate revenue and units top-ten bar charts. **Country Performance** includes all countries in its table and a chart of the top ten non-UK markets for readability.
5. Explore the native PivotTables at **Monthly Sales!I5** and **Country Performance!I5**. Click inside one, choose **PivotTable Analyze > Field List**, and inspect the Month/Country row field and summed revenue/orders. Right-click a value to sort. To filter, drag Month or Country into the Filters area in a working copy; restore **(All)** afterwards. These pivots summarize embedded aggregates and do not provide transaction-level drill-through.
6. Read **Customer Analysis** for the known-customer denominator, **Data Quality** for exclusions and overlapping flags, and **Sources** for provenance and refresh instructions.

The four charts reference nearby summary tables, not the PivotTables. Pivot filters do not control the charts or full-dataset Overview KPIs. Table filters are local to their tables; this workbook has no connected slicer dashboard. **Data > Refresh All** refreshes embedded pivot caches only. It does not reload CSVs or rerun Python. Explore a copy and leave the published snapshot unfiltered.

## Completion status

| Deliverable | Verified status |
| --- | --- |
| Python inspection, cleaning, audit and analysis | Executed and validated; full workflow rerun successfully |
| Automated tests | Ten tests passed, including SQL comparison checks |
| MySQL/MariaDB schema and seven analysis queries | **Executed on MariaDB 10.4.32; all seven results match Python.** See [SQL reconciliation](reports/sql_reconciliation.md). MySQL 8 not separately engine-tested |
| Power BI data model exports, M, DAX and build guide | Python-side reconciled: seven analysis tables, six filter scenarios, twelve top-ten checks. **M/DAX unexecuted; native report not built**. [Evidence](reports/powerbi_reconciliation.md) |
| Excel workbook, native PivotTables and charts | **Created and validated:** seven sheets, four native charts, two native PivotTables, 146 calculated formulas and 359 reference-cell checks |
| Screenshots | No published dashboard screenshots; workbook layout previews were inspected locally in ignored QA files |

## Business questions

- What are completed-sales revenue, order count, units and average order value?
- How do monthly sales vary when partial boundary periods are identified?
- Which product codes and countries lead revenue and units?
- How many known customers place multiple completed orders within the observed window?
- How do missing IDs, cancellation flags, unusual codes and duplicate assumptions affect the analysis?

## Dataset, attribution and usage terms

**Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository.** [Dataset and download](https://archive.ics.uci.edu/dataset/352/online+retail) · [DOI](https://doi.org/10.24432/C5BW33).

UCI distributes the dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Give attribution, link the license, indicate changes and do not imply endorsement when sharing adaptations. This project creates a modified analytical view through documented exclusions. Dataset terms do not automatically license original project code; no code license has been selected.

The local workbook has **541,909 rows and eight columns**, covering **1 December 2010 08:26–9 December 2011 12:50**. SHA-256: `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`. Measured missing values take precedence over generic source-site metadata.

Download `Online Retail.xlsx` into `data/raw/`. Raw files and large generated line-level outputs are excluded from Git; the original local workbook remains unchanged.

## Structure

| Folder | Purpose |
| --- | --- |
| `data/raw/` | Untouched input workbook; ignored except placeholder |
| `data/processed/` | Generated completed-sales and audit CSVs; ignored |
| `src/` | Inspection, cleaning, analysis, packaging, tests and audits |
| `sql/` | Schema, equivalent analysis queries and execution guide |
| `reports/` | Inspection/cleaning evidence, aggregate results and review |
| `dashboard/` | Power BI preparation package, M/DAX and Desktop guide |
| `docs/` | Interview walkthrough and resume bullets |

## Setup and execution

Tested on Windows with **Python 3.12.10**. Dependencies are pinned in `requirements.txt`. Viewing the saved workbook requires Excel; rerunning Python requires the pinned environment. Rebuilding native workbook features requires installed Windows Excel Desktop. Re-executing SQL requires a compatible database server. Power BI Desktop is only needed for the optional pending report.

After downloading the source workbook, run from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe src/run_pipeline.py
```

The runner executes tests, inspection, cleaning, analysis and Power BI packaging in order, connecting newly created timestamped folders automatically. It prints their paths and saves `reports/reproduction_<timestamp>.json`. Existing outputs are preserved. Run one pipeline at a time. **Do not use Python `-O`**, which disables validation assertions. Download/install needs network access; execution uses local files.

To use another location for the same UCI workbook, pass `--input "path/to/Online Retail.xlsx"`. This is a tested dataset-specific workflow, not a generic retail ETL service. Paths used to connect generated analysis and packaging stages are repository-relative. Historical source-location notes can contain the original drive path; SQL imports and Power Query's folder parameter must be regenerated or edited after moving the project.

Individual checks/stages:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src -p "test_*.py" -v
.\.venv\Scripts\python.exe src/inspect_data.py
.\.venv\Scripts\python.exe src/clean_data.py
# Substitute the folders printed by those stages:
.\.venv\Scripts\python.exe src/analyze_sales.py --input data/processed/CLEANING_RUN/completed_sales.csv --inspection reports/INSPECTION_RUN/inspection.json
.\.venv\Scripts\python.exe src/prepare_powerbi.py --analysis reports/ANALYSIS_RUN
.\.venv\Scripts\python.exe src/audit_repository.py
```

## Cleaning decisions

`src/clean_data.py` reads the workbook without saving it and writes separate sales/audit outputs. It retains Excel row provenance, original values, flags and reasons. See the [stock-code policy](reports/stock_code_policy.md).

1. Keep InvoiceNo, StockCode and CustomerID as strings; preserve missing customer IDs. Parse dates/numeric fields and report failures; actual conversion failures were zero.
2. Exclude invalid required fields, cancellations, nonpositive quantities and nonpositive prices. A negative quantity is not assumed to be a confirmed return.
3. Exclude reviewed charges, adjustments, samples and gift vouchers; retain recognized unusual merchandise and valid alphabetic suffixes; quarantine unresolved formats.
4. Remove later **exact matches across all eight source fields**, retaining the first. This is an analytical assumption. Never deduplicate InvoiceNo alone: invoices contain multiple product lines.
5. Retain otherwise valid anonymous sales for overall metrics. Exclude missing IDs only from customer-specific metrics. Missing descriptions alone do not invalidate recognized merchandise.
6. Calculate Quantity × UnitPrice with Decimal arithmetic, **ROUND_HALF_UP to GBP 0.01 after multiplication**, then sum integer pence. Do not pre-round unit prices.

Sequential exclusions removed **19,369 rows**, leaving **522,540**. There were **5,268 extra exact copies** in the source; after earlier rules, the duplicate rule removed **5,221 rows worth £24,213.74**. Flags overlap, while sequential rule counts are disjoint. The audit contains flagged retained records too; do not append it directly to completed sales.

## Metrics and verified results

| Metric | Definition | Result |
| --- | --- | ---: |
| Completed-sales revenue (GBP) | Eligible line-rounded sales pence / 100 | £10,247,219.32 |
| Completed orders | Distinct InvoiceNo with eligible product lines | 19,773 |
| Units sold | Sum of eligible Quantity | 5,561,387 |
| Average order value (GBP) | Revenue / completed orders | £518.24 |
| Known customers | Distinct nonmissing eligible CustomerID | 4,334 |
| Repeat customers | Known IDs with at least two distinct completed invoices in the window | 2,829 |
| Repeat-customer rate | Repeat customers / known customers | 65.27% |

Rank products by exact StockCode, not description, with metric descending and code ascending as tie-break. Monthly and country revenue/order totals reconcile with overall figures. Invoice attribution checks found no cleaned invoice spanning different countries, customers or months.

Monthly outputs include observed MoM and a separate qualified comparison. Qualified comparisons exclude boundary pairs. December 2010 begins on day 1 but completeness is unverified; December 2011 is partial through day 9. Interior-month calendar coverage is not independent proof of completeness.

## Findings and practical recommendations

**Observed:** November 2011 had the highest interior-month revenue, **£1,452,115.98**. The United Kingdom contributed **£8,724,443.67** across **17,901 orders**. Product **22423**, REGENCY CAKESTAND 3 TIER, led revenue at **£174,156.54**; product **23843** led units at **80,995**. Of **135,080 raw lines** missing CustomerID, **131,387 eligible anonymous lines** remain in overall sales. **224 stock codes** participate in case-insensitive collisions; the Power BI package preserves these with technical keys and distinct labels.

**Recommendations:** investigate leading products/markets, review exceptional quantities before planning from rankings, label boundary periods, and report known-customer coverage beside repeat metrics. These are suggestions for further investigation, not measured improvements. The data do not establish promotion effects, seasonality, intent or other causes.

[Computed findings](reports/analysis_20261017T163159_486015Z/findings.md) · [Headline table](reports/analysis_20261017T163159_486015Z/kpis.csv) · [Monthly table](reports/analysis_20261017T163159_486015Z/monthly.csv) · [Cleaning evidence](reports/cleaning_20261017T162742_974298Z/cleaning_report.md).

## Optional Power BI extension: native report pending

**FactSales** holds eligible product lines; **QualityRows** holds every original source line once. **DimDate**, **DimProduct** and **DimCountry** each have active one-to-many, single-direction relationships to both facts. **CleaningSteps** is disconnected global evidence. No fact-to-fact relationship is used.

DimDate has 730 consecutive dates across 2010–2011 with coverage labels. Numeric ProductKey avoids case-insensitive text collisions; original codes remain strings. Customer IDs stay nullable fact attributes. No categories, costs or profit are introduced.

**Pending, outside the completed portfolio scope:** no native PBIX exists yet. Desktop installation is deferred because of limited storage. Completing Power BI is not a publication prerequisite. If pursued later, follow [dashboard/README.md](dashboard/README.md) and the [Desktop build guide](dashboard/POWER_BI_DESKTOP.md): generate imports, paste M, create relationships, mark the date table, add [DAX measures](dashboard/measures.dax), and build Sales Overview, Products and Markets, and Data Quality pages. Test date/country slicers and dynamic top tens against the package's six reference scenarios before saving a real PBIX. M/DAX remain unexecuted in a Power BI engine.

The latest [Power BI handoff](dashboard/powerbi_20261017T174905_392483Z/START_HERE.md) includes exact M, model specification, measure snapshot, theme, pixel placement plan for all three pages and a DAX Query-view validation script. Model/layout specifications are instructions, not native PBIP/PBIR artifacts. Read-only checks found no Desktop installation or supported authoring engine in checked locations; see [availability evidence](reports/powerbi_availability.json). The [first manual Desktop step](dashboard/FIRST_STEP.md) is retained for a future optional build. The [reconciliation report](reports/powerbi_reconciliation.md) separates completed Python-side checks from outstanding Desktop execution and visual checks. Raw, cleaned, audit and validated Excel hashes remain unchanged.

## Excel viewing

Open [reports/Retail_Sales_Analysis.xlsx](reports/Retail_Sales_Analysis.xlsx) in Excel Desktop. It contains Overview, Monthly Sales, Top Products, Country Performance, Customer Analysis, Data Quality and Sources. GBP formats, coverage warnings, filters, frozen headers and native charts are included. Two genuine native PivotTables sit at I5 on Monthly Sales and Country Performance; they summarize embedded monthly/country aggregates, not transaction-level facts. Other blocks are labeled summary tables. The full-dataset Overview values do not change when summary-table or PivotTable filters change.

The workbook was authored with the explicitly authorized openpyxl fallback and finalized in installed Microsoft Excel 16.0. Excel recalculated 146 formulas with zero errors; 359 reference-cell checks and both PivotTable grand totals matched the verified outputs. Four chart layouts and all seven sheets were inspected using native Excel PDF/PNG previews. [Validation evidence](reports/excel_validation.json) records the workbook hash and input hashes. No cleaning rules or metric definitions changed. Completed-sales revenue remains **not net revenue**; the repeat rate denominator is the 4,334 known customers with eligible sales in this window.

Regenerate from the project root (requires the pinned Python environment, Windows PowerShell and installed Excel Desktop):

```powershell
.\.venv\Scripts\python.exe src/build_excel.py --replace
```

`--replace` archives the existing workbook before replacement. `src/build_excel.py` uses `src/finalize_excel.ps1` for native pivots, charts, cached formula calculation and PDF export. Optional visual QA regeneration: `powershell -NoProfile -File src/render_excel_pdf.ps1 -WorkDir reports/excel_qa/RUN_FOLDER`. Earlier drafts and previews remain in the ignored QA directory. For another analysis, pass `--analysis reports/ANALYSIS_RUN --sql-evidence reports/SQL_RECONCILIATION.json`; these must refer to the same verified data.

**Refresh All does not rerun Python or reload CSV files.** It refreshes embedded PivotTable caches only; regenerate for new inputs. Sources explains refresh, native pivot scope and exact manual recreation steps. The [transaction-level Excel/PivotTable guide](reports/excel_refresh_and_pivottables.md) covers optional Power Query/Data Model imports; those additional transaction-level pivots have not been created in this summary workbook.

## SQL viewing and execution

[sql/README.md](sql/README.md) covers VARCHAR identifiers, DATETIME dates, DECIMAL money and the seven analysis queries. After the user started XAMPP, a read-only check confirmed `retail_sales_analysis` was absent. Only that dedicated database was created and loaded; pre-existing databases were preserved. **All seven SQL result tables executed on MariaDB 10.4.32 and matched Python**, including all 4,334 customer rows. No value discrepancies were found; expected SQL NULL versus CSV blank differences were normalized. [The reconciliation report](reports/sql_reconciliation.md) includes actual results and machine-readable evidence. MySQL 8 has not been separately engine-tested.

The database now exists: **do not repeat CREATE/LOAD**. Use the [execution checklist](sql/EXECUTION_CHECKLIST.md) for a fresh-server setup or run the read-only export/comparison script against this loaded database:

```powershell
.\.venv\Scripts\python.exe src/run_sql_analysis.py
```

The current local connection needed no password. If another account requires one, use `--user YOUR_LOCAL_USER --prompt-password` and enter it only at the database client's hidden prompt, never in code or command values. Two comparison regression tests passed alongside the original eight tests; actual engine reconciliation is recorded separately from those tests.

## Limitations

- Completed sales are not net revenue, cash receipts or profit.
- Duplicate and stock-code decisions are assumptions affecting totals; case-distinct codes were not assumed equivalent.
- Missing IDs limit customer analysis. Repeat rates are window-based, filter-dependent and not lifetime retention.
- The last month is partial; other months' completeness is unverified. Large retained transactions can dominate rankings.
- Descriptions vary. No categories, costs, return matches or causal explanations were invented.
- SQL equivalence is verified on MariaDB 10.4.32 only. Excel is validated in Excel 16.0; MySQL 8 and Power BI M/DAX remain unverified, and the native Power BI report is unbuilt.

## Interview and GitHub readiness

[Interview walkthrough and code explanation](docs/INTERVIEW_WALKTHROUGH.md) · [Resume bullets](docs/RESUME_BULLETS.md) · [Review evidence](reports/project_review.md).

Publication target: [intizarhussainn14-byte/retail-sales-analysis](https://github.com/intizarhussainn14-byte/retail-sales-analysis). Raw workbooks, generated facts, local SQL exports, virtual environments and common secret files are ignored. Aggregate evidence and code are available for review. Run `src/audit_repository.py` and inspect files before staging; its pattern-based secret scan cannot guarantee detection of every possible secret. Select an original-code license before granting reuse rights; dataset terms remain separate. A temporary Windows Git ownership issue was resolved without changing global trust settings.

## Before publishing

- Open the workbook on the machine you will use to present it and practise the tab/chart/PivotTable walkthrough above. The recorded native Excel validation and current hash review are in [Excel validation](reports/excel_validation.md).
- Optionally add selected real Excel screenshots for readers without Excel. Current QA previews are ignored and are not part of the public repository.
- Decide whether to grant reuse rights to original code and, if so, select and add an appropriate code license. Keep the existing dataset attribution and modification notes.
- Run `.\.venv\Scripts\python.exe src/audit_repository.py`, review `git status --short`, then review the exact files and staged diff when you choose to stage. Include the analysis workbook and aggregate evidence; keep raw data, generated line-level data, environments, credentials and QA intermediates excluded.
- For future updates, review the staged changes before committing and push without force-pushing. Power BI completion, MySQL 8 testing and optional transaction-level Excel pivots are future extensions, not requirements for publishing the completed Python/SQL/Excel work.

Publication includes the latest Power BI preparation package plus historical manifests and entry-point notes; redundant older package outputs stay local. Both small analysis snapshots remain as original-reference and reproduced-run evidence because documentation, workbook provenance and validation reports refer to them. Raw and line-level data are regenerated locally.
