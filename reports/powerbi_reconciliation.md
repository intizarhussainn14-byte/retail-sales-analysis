# Power BI handoff validation — 17 October 2026

**Python-side preparation and reconciliation PASS. Native report NOT built;
Power Query, DAX, visuals and interactions NOT executed in Power BI.**

## Available tools

[Read-only installation evidence](powerbi_availability.json) found no PBIDesktop,
pbi-tools or dotnet on PATH, neither common Desktop executable, no Power BI
Store package, no uninstall-registry entry and no running PBIDesktop process.
Store and registry checks completed without unreadable entries. No callable
Power BI authoring connector was exposed. A portable or other-user installation
is not ruled out. No software was installed.

This delivery therefore uses the requested Desktop handoff route. There is no
PBIX/PBIP or built report. model_spec.json and REPORT_LAYOUT.md are implementation
specifications, not native Power BI file formats. Theme import remains unchecked.

## Prepared imports and executed checks

[Current package](../dashboard/powerbi_20261017T174905_392483Z/START_HERE.md) ·
[Machine-readable validation](../dashboard/powerbi_20261017T174905_392483Z/validation.json).

| Import | Rows | Grain |
| --- | ---: | --- |
| FactSales | 522,540 | Eligible product line |
| QualityRows | 541,909 | Original source row, exactly once |
| DimDate | 730 | Continuous dates, full calendar years 2010–2011 |
| DimProduct | 4,070 | Exact source stock code with numeric technical key |
| DimCountry | 38 | Country |
| CleaningSteps | 6 | Disconnected global cleaning rule |

Serialized imports were reloaded and all seven analysis tables recomputed with
the existing validated Python analysis function. Every value and deterministic
row ordering matched, including all 4,334 customer rows. All reference hashes
agree with the separately executed MariaDB and Excel validation evidence.
This verifies data transfer and definitions, not a separate DAX implementation.

Additional checks passed: six dimension-to-fact foreign keys; date continuity;
date-only relationship keys; integer-pence/GBP equivalence; nullable customer
eligibility; no invoice/customer text-case collisions; stock-code UTF-8 round-trip;
case-safe product labels; all raw flags and disjoint exclusion counts/amounts;
six date/country scenarios and twelve top-ten lists using numeric keys.
All ten existing automated tests passed.

SHA-256 checks confirmed the raw workbook, cleaned sales, audit and completed
Excel workbook still match their recorded hashes. Python, SQL and Excel results
were preserved. No database changes or Git staging/commit/push were performed.

## Reconciled Python references for Desktop

| Selection | Revenue GBP | Orders | Units | Known customers | Repeat customers | Repeat rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All observed dates/countries | £10,247,219.32 | 19,773 | 5,561,387 | 4,334 | 2,829 | 65.27% |
| United Kingdom | £8,724,443.67 | 17,901 | 4,639,114 | 3,916 | 2,563 | 65.45% |
| January 2011, all countries | £670,380.24 | 1,081 | 386,738 | 739 | 147 | 19.89% |
| January 2011, France | £16,174.12 | 28 | 9,112 | 24 | 2 | 8.33% |
| November 2011, Germany | £24,195.36 | 64 | 13,280 | 43 | 13 | 30.23% |
| December 2011 through day 9 — partial | £614,490.92 | 816 | 312,647 | 614 | 105 | 17.10% |

Full-range AOV is £518.24. QualityRows has 19,369 excluded rows and 135,080
missing-customer rows; completed sales retain 131,387 missing-customer rows.
Quality references remain separate from sales. Flags overlap; first applicable
exclusion rules are disjoint. Excluded signed value is not lost revenue.

Repeat rate = known customers with two or more distinct eligible invoices /
known customers with eligible sales in the **same active date/country/product
selection**. Multiple lines on one invoice do not establish repeat purchasing.
This is not lifetime retention; filters change numerator and denominator.

Completed-sales revenue excludes cancellations and negative adjustments and is
**not net revenue**. No categories, costs, profit or return matches were added.

## Qualifications and outstanding checks

December 2010 starts on day 1 but completeness is unverified. December 2011 ends
on day 9 and is partial. Qualified GBP and percentage MoM require an entire
selected current calendar month and both months to be interior months. Prior
revenue uses the preceding full calendar month, retaining country/product
context even outside the date slicer. Observed changes are diagnostics only.

The first validator compared money strings literally (1.2 versus 1.20) and
Series storage dtypes literally; these checks were corrected to compare exact
Decimal values and identifier contents. No monetary discrepancy or data change
was found. All final checks passed.

Desktop checks still required: M type conversion/refresh, relationship engine
behavior, DAX totals, slicer responses, top-ten membership, cut-month MoM blanks,
long labels, chart layout and notes. validate_measures.dax provides six engine
queries; expected CSVs support separate visual checks. Actual dashboard
reconciliation is **pending**.

## Reproduce and finish

```powershell
# Execution-policy override applies only to this process:
powershell -NoProfile -ExecutionPolicy Bypass -File src/check_powerbi.ps1
.\.venv\Scripts\python.exe src/prepare_powerbi.py --analysis reports/analysis_20261017T165141_531793Z
# Substitute the new package folder printed above:
.\.venv\Scripts\python.exe src/validate_powerbi.py dashboard/POWERBI_RUN
```

Packaging creates a new directory, preserving previous runs. The validator also
requires existing SQL/Excel evidence and the unchanged workbook. Desktop refresh
rereads CSVs; it never runs Python. Regenerate all six imports together, update
pDataFolder, refresh and reconcile; numeric product keys are package-specific.

Start with [the first manual step](../dashboard/FIRST_STEP.md), then follow the
model and three-page instructions. Save an actual PBIX after Desktop checks pass.
