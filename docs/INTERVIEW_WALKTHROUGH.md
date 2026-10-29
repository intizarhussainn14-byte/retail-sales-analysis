# Interview walkthrough

## Two-minute introduction

“I used the UCI Online Retail dataset to answer questions about eligible merchandise sales, monthly trends, products, countries and repeat purchasing. I began by inspecting all 541,909 rows rather than assuming the Excel file was clean.

“I wrote a reproducible pandas pipeline that preserves the raw file and records flags and exclusion reasons by original Excel row. I kept invoice and customer identifiers as strings. I separated cancellations, negative adjustments and non-product charges from a positive completed-sales view, reviewed unusual product codes and documented exact-duplicate removal as an assumption.

“The validated view contains 522,540 lines, £10,247,219.32 in completed-sales revenue and 19,773 distinct orders. Average order value is £518.24. This is not net revenue because cancellations and negative adjustments are excluded. Among 4,334 known customers, 2,829 placed multiple completed orders in the window, a 65.27% observed repeat rate. Anonymous sales remain in overall metrics.

“I reconcile monthly and country totals to the headline results, use penny-level arithmetic and test business rules. I executed all seven SQL analyses on MariaDB 10.4.32 and matched every equivalent output to Python, including 4,334 customer rows. I created a seven-sheet Excel workbook with native charts and two native summary-based PivotTables, recalculated it in Excel and checked its values and layout. I also prepared a Power BI import model, date dimension, M, DAX and filtered reference cases. Power BI engine validation and its native report remain unfinished; MySQL 8 has not been separately tested.”

## Explain the code

| File | What it does | How to defend the choice |
| --- | --- | --- |
| `src/inspect_data.py` | Reads sheets; measures missingness, duplicates, signs, dates and IDs; hashes source | Inspection gives evidence before rules are chosen; hashing checks input preservation |
| `src/clean_data.py` | Parses fields; makes independent flags; applies ordered exclusions; exports audit/sales | Independent flags preserve overlapping issues; ordered rules give disjoint count/value impacts |
| `src/analyze_sales.py` | Aggregates eligible lines into KPIs, monthly/product/country/customer results | Orders count distinct invoices, not lines; integer pence reconcile without floating-point sum drift |
| `src/prepare_powerbi.py` | Reconstructs full quality coverage, creates dimensions, exports M and filtered expectations | Sales and quality have different grains/definitions; dimensions filter both without joining facts |
| `src/project_paths.py` | Rebases current and legacy metadata paths to the present checkout | Cloning to another drive must not read a former user's absolute path; traversal outside expected folders is rejected |
| `src/run_pipeline.py` | Runs tests and stages in sequence; records outputs and compares analysis tables | One command connects fresh timestamped stages, stops on errors and checks reproducibility |
| `src/reconcile_sql.py` | Compares actual exported SQL tables with Python outputs | Semantic keys, exact decimals, NULL normalization and preserved string IDs; all seven MariaDB outputs passed |
| `src/run_sql_analysis.py` | Runs existing analysis SELECTs and exports actual results, query snapshots and evidence | Read-only after loading; it does not create/overwrite databases or accept password values in arguments |
| `src/audit_repository.py` | Checks Git candidates for large files, common secret patterns, broken links and ignore coverage | Keeps upload preparation reviewable; does not pretend a regex scan proves universal absence of secrets |

`transform()` in cleaning keeps the input separate from the derived dataframe. Each flag is a Boolean Series. Each sequential rule removes only records still eligible, preventing double counting. A row may still have multiple audit reasons. SourceRow maps the result back to Excel, where row 1 is the header. CSVs do not enforce types, so import schemas explicitly keep identifiers as text.

`analyze()` works at invoice-line grain. It groups by exact StockCode for products, calendar month for trends and CustomerID only when present. Before summing distinct-order counts across dimensions, it checks that a single invoice is not ambiguously assigned across countries/customers/months. Descriptions use a deterministic observed label, not a fabricated catalog.

## Questions to practise

**Why not remove duplicate invoice numbers?** One invoice normally contains many products. Only an identical match across all eight source fields is an exact duplicate candidate. I keep the first and audit every duplicate-group member. Identical lines could be legitimate; this assumption reduces the eligible view by 5,221 rows and £24,213.74 after earlier rules. All 5,268 source extras are flagged, including those already excluded for another reason.

**Why retain missing customer IDs?** A missing ID does not invalidate an otherwise eligible sale. Dropping those lines would understate sales. I retain 131,387 eligible anonymous lines and omit them only from customer metrics; I never combine them into one invented customer.

**Why is revenue not net revenue?** The chosen view requires positive quantity, positive unit price, no cancellation flag and a reviewed product code. Cancellations and adjustments are excluded, not matched to sales. I cannot claim net returns, cash collection or profit.

**Why not use float for money?** I multiply Decimal representations of source values, round each line to pennies with ROUND_HALF_UP, then sum integer pence. For example, three units at 0.335 gives 1.005 before rounding, or £1.01. Rounding unit price first would give a different result. SQL uses DECIMAL; the Power BI ranking helper uses integer pence.

**Why review alphabetic product codes?** Actual codes include merchandise such as 85123A and PADS, as well as POST and fees. Letters are not proof of invalidity. Explicit reviewed exclusions and quarantines are more defensible than deleting every nonnumeric code.

**What is the Power BI case issue?** Its text comparison can combine case-distinct StockCodes that Python treats separately. I found 224 source codes participating in these collisions. Technical numeric ProductKey relationships and collision-safe labels preserve groups without asserting those variants are the same product. Keys are package-specific, so refresh all related files together.

**What does 65.27% mean?** Of the 4,334 known IDs with eligible sales, 2,829 had at least two distinct completed invoices within the observation window. Multiple lines on one invoice do not count as repeat purchases. This is not lifetime retention or a causal measure; it changes with the selected time/country/product context.

**Why not call December's decline a business problem?** December 2011 ends on day 9. Comparing it directly with a full November would be misleading. December 2010 starts on day 1 but first-day/source completeness remains unverified. Qualified MoM comparisons exclude both boundary pairs.

**What are the most useful observations?** November leads interior-month revenue at £1,452,115.98; the UK contributes £8,724,443.67; 22423 leads product revenue at £174,156.54. I recommend investigating concentration and unusually large orders. I have not measured the impact of any action or established why these patterns occurred.

**How did you validate?** Ten tests cover eligibility, conversion failures, rounding, provenance, multi-line invoices, customer denominators, boundary months, invoice attribution, product case safety, portable paths and SQL comparison safeguards. Full-data assertions reconcile row/money totals and hashes. The Python rerun reproduced seven reference tables byte-for-byte. Separately, the actual MariaDB queries executed and all seven result tables matched Python. Unit tests themselves do not execute SQL, M or DAX.

**What would you do next?** SQL import/comparison and the Excel summary workbook are complete. The completed portfolio is ready to present through Excel. Before publication I would practise the workbook walkthrough, review the upload set and code-license choice, and optionally add real Excel screenshots. Power BI remains an optional pending extension because Desktop installation is deferred for storage reasons. I could separately test MySQL 8 compatibility and sensitivity to duplicate/code assumptions. I would not claim causal explanations without an appropriate study design.

## Evidence to open in an interview

1. README for the scope, metric definitions and honest completion status.
2. `reports/cleaning_20261017T162742_974298Z/cleaning_report.md` for disjoint rule counts and values.
3. `reports/analysis_20261017T163159_486015Z/kpis.csv` and `monthly.csv` for actual results.
4. A reproduction manifest and `reports/project_review.md` for review evidence.
5. `reports/Retail_Sales_Analysis.xlsx` as the main visual deliverable: show Overview, the monthly chart and boundary warning, the two product charts, and the country chart. Click Monthly Sales!I5 or Country Performance!I5 to inspect native PivotTable fields and sort/filter in a copy. Explain that these are aggregate-based pivots, and their filters do not control the charts or Overview KPIs.
6. `reports/excel_validation.md` for native Excel calculation and visual-review evidence. Power BI assets can be discussed separately as optional preparation; the native report is pending.

Do not present CSVs as an Excel workbook, summary tables as native PivotTables or prepared DAX as a working dashboard. SQL execution/reconciliation can now be claimed specifically for MariaDB 10.4.32, supported by reports/sql_reconciliation.md.
