# Inspection findings and proposed cleaning rules

Status: recommendations only. No data has been cleaned or exported to `data/processed/`.

Evidence: `inspection_20261017T162126_340038Z/inspection.md` and its machine-readable JSON companion. All counts are from the untouched raw copy. Counts overlap and must not be added to estimate total excluded rows.

## What we found

- One sheet, `Online Retail`, contains 541,909 invoice line items and eight columns.
- Columns: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country.
- Dates span 2010-12-01 08:26 through 2011-12-09 12:50, with no missing or unparseable dates. December 2011 is only a partial month; avoid presenting it as a full month in growth comparisons.
- Missing CustomerID: 135,080 rows (about 24.9%). Missing Description: 1,454. All other columns have zero missing values under the parser's standard missing-value rules.
- Exact duplicates: 5,268 extra occurrences after the first; 10,147 total rows belong to duplicate groups. Identical rows alone do not prove an erroneous transaction.
- Quantity: 10,624 negative, zero with quantity 0; range -80,995 to 80,995.
- UnitPrice: two negative and 2,515 zero; range -11,062.06 to 38,970. These are unit prices, not calculated line revenue.
- C-prefixed invoices: 9,288 rows across 3,836 unique invoices. All have negative quantities. Another 1,336 negative-quantity rows have no C prefix.
- Distinct nonmissing values: 25,900 invoices, 4,070 StockCodes, 4,372 customers and 38 countries. StockCode count includes special codes, so it is not yet a count of sellable products.
- Identifiers are strings. Actual StockCodes include `85123A`, `POST`, and `84406B`; invoice examples include `C536379`. None of the three identifier fields has surrounding whitespace. Observed CustomerIDs contain digits only, but they remain identifiers.
- pandas types: identifiers `string`, Quantity `int64`, UnitPrice `float64`, InvoiceDate `datetime64[ns]`, Description and Country `object` (text).

## Proposed rules for the next stage

1. **Preserve provenance.** Keep raw data unchanged. Create processed outputs separately, retain original row numbers, and record a reason for every flag or exclusion. Reconcile row counts and revenue effects after each rule.
2. **Keep IDs as text.** Use string fields in pandas, text in Excel/Power BI, and VARCHAR in MySQL/MariaDB. Do not sum identifiers or remove alphabetic characters from StockCode. Preserve original values alongside any standardized versions.
3. **Review duplicates.** Inspect duplicate groups before deciding whether to keep one occurrence. Repeated invoice line items can be legitimate. If deduplication is adopted, document the assumption and retain excluded rows for audit.
4. **Separate sales and adjustments.** Flag C-prefixed invoices and all negative quantities separately. Review the 1,336 negative rows without C prefixes. Keep cancellations/returns available for a separate view; do not turn quantities positive. Do not label every negative line as a confirmed return without evidence.
5. **Define sales metrics explicitly.** A proposed positive-sales view uses Quantity > 0, UnitPrice > 0, and no cancellation flag. Report excluded adjustments separately. Net revenue needs an explicit policy for valid returns/credits; it should not silently use the positive-sales view. Calculate line revenue as Quantity times UnitPrice only after classification.
6. **Review nonpositive prices and extreme values.** Investigate the two negative prices and 2,515 zero prices; these may represent adjustments or free items. Exclude them from a paid-sales view with documented reasons, while preserving them in the full dataset. Review extreme quantities/prices; do not cap or delete them automatically.
7. **Keep anonymous sales usable.** Retain missing-customer rows for eligible sales totals. Exclude them from customer counts, repeat-customer rates and customer segmentation. Never fill all missing customer IDs with a real ID or treat all anonymous rows as one customer.
8. **Handle descriptions conservatively.** Use a display label such as `Unknown description` if needed, preserving the original. Investigate whether a StockCode maps to multiple descriptions before filling from a lookup. Review special codes such as POST before defining product rankings.
9. **Validate reporting dimensions.** Inspect country/description spellings and code mappings before standardizing. Keep invoice timestamps; derive dates/months in additional columns. Flag partial months in charts.
10. **Prepare compatible storage later.** Use VARCHAR identifiers, DATETIME timestamps, integer quantities and suitable DECIMAL types for monetary columns in MySQL/MariaDB. Avoid SQL Server-specific syntax. No database, credentials, SQL schema or Power BI dashboard is needed for this inspection stage.

The next stage should implement approved rules in a separate script, produce a cleaning audit, and validate the results before SQL, Excel summaries or Power BI work begins.
