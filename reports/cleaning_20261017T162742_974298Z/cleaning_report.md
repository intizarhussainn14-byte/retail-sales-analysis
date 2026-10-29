# Cleaning report

Completed-sales revenue excludes cancellations and negative adjustments. It is not net revenue.

Money: Decimal(str(source value)), Quantity × UnitPrice, round each line to GBP 0.01
using ROUND_HALF_UP, then sum integer pence. No unit-price pre-rounding. Unvalued lines
are counted separately, never treated as zero economic impact.

Duplicate policy: remove only extra exact matches across all eight original columns, keeping
the first source row. This is an explicit analytical assumption, not proof of an error.
All duplicate-group members are audited. Repeated InvoiceNo alone is never removed.

Missing customer, description or country alone does not exclude an otherwise valid product sale.
CustomerMetricsEligible must be true for customer metrics. Missing customer IDs remain blank.

Stock-code policy: observed charge/adjustment codes are excluded via the explicit NONPRODUCT
list in src/clean_data.py. Normal five-digit product codes with alphabetic suffixes remain.
Unexpected formats are quarantined for review rather than silently classified as products.
See stock_code_review.csv and reports/stock_code_policy.md for observed descriptions.

Sequential exclusions below are disjoint; flag counts overlap. Signed amounts describe
excluded source line values, not lost revenue or confirmed returns. Removing negative lines
increases the remaining signed total. Absolute amounts show scale without offsetting signs.

| Rule | Before | Excluded | After | Excluded signed GBP | Absolute GBP | Unvalued |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| invalid_required_fields | 541909 | 0 | 541909 | 0.00 | 0.00 | 0 |
| cancellation | 541909 | 9288 | 532621 | -896812.49 | 896812.49 | 0 |
| nonpositive_quantity | 532621 | 1336 | 531285 | 0.00 | 0.00 | 0 |
| nonpositive_price | 531285 | 1181 | 530104 | -22124.12 | 22124.12 | 0 |
| nonproduct_or_unreviewed_code | 530104 | 2343 | 527761 | 395251.48 | 395251.48 | 0 |
| exact_duplicate_extra | 527761 | 5221 | 522540 | 24213.74 | 24213.74 | 0 |

```json
{
  "source": "F:\\Data Science\\Retail Sales Analysis Dashboard\\data\\raw\\Online Retail.xlsx",
  "source_sha256": "43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d",
  "raw_unchanged": true,
  "input_rows": 541909,
  "completed_sales_rows": 522540,
  "audit_rows": 155564,
  "excluded_rows": 19369,
  "completed_sales_GBP": "10247219.32",
  "retained_missing_customer_rows": 131387,
  "flag_counts": {
    "Flag_missing_InvoiceNo": 0,
    "Flag_missing_StockCode": 0,
    "Flag_missing_Description": 1454,
    "Flag_missing_Quantity": 0,
    "Flag_missing_InvoiceDate": 0,
    "Flag_missing_UnitPrice": 0,
    "Flag_missing_CustomerID": 135080,
    "Flag_missing_Country": 0,
    "Flag_conversion_failure_Quantity": 0,
    "Flag_conversion_failure_UnitPrice": 0,
    "Flag_conversion_failure_InvoiceDate": 0,
    "Flag_fractional_quantity": 0,
    "Flag_cancellation": 9288,
    "Flag_negative_quantity": 10624,
    "Flag_zero_quantity": 0,
    "Flag_nonpositive_price": 2517,
    "Flag_exact_duplicate_extra": 5268,
    "Flag_exact_duplicate_group": 10147,
    "Flag_nonproduct_code": 2946,
    "Flag_unreviewed_stock_code": 9
  },
  "stages": [
    {
      "rule": "invalid_required_fields",
      "before": 541909,
      "excluded": 0,
      "after": 541909,
      "excluded_signed_GBP": "0.00",
      "excluded_absolute_GBP": "0.00",
      "excluded_unvalued_rows": 0
    },
    {
      "rule": "cancellation",
      "before": 541909,
      "excluded": 9288,
      "after": 532621,
      "excluded_signed_GBP": "-896812.49",
      "excluded_absolute_GBP": "896812.49",
      "excluded_unvalued_rows": 0
    },
    {
      "rule": "nonpositive_quantity",
      "before": 532621,
      "excluded": 1336,
      "after": 531285,
      "excluded_signed_GBP": "0.00",
      "excluded_absolute_GBP": "0.00",
      "excluded_unvalued_rows": 0
    },
    {
      "rule": "nonpositive_price",
      "before": 531285,
      "excluded": 1181,
      "after": 530104,
      "excluded_signed_GBP": "-22124.12",
      "excluded_absolute_GBP": "22124.12",
      "excluded_unvalued_rows": 0
    },
    {
      "rule": "nonproduct_or_unreviewed_code",
      "before": 530104,
      "excluded": 2343,
      "after": 527761,
      "excluded_signed_GBP": "395251.48",
      "excluded_absolute_GBP": "395251.48",
      "excluded_unvalued_rows": 0
    },
    {
      "rule": "exact_duplicate_extra",
      "before": 527761,
      "excluded": 5221,
      "after": 522540,
      "excluded_signed_GBP": "24213.74",
      "excluded_absolute_GBP": "24213.74",
      "excluded_unvalued_rows": 0
    }
  ],
  "validation": [
    "PASS: row provenance, eligibility, missing customer preservation, duplicate policy,",
    "identifier/date completeness, multi-line invoices and integer-pence reconciliation.",
    "PASS: source hash and CSV round-trip identifiers/missing customers."
  ]
}
```

Audit includes flagged retained rows as well as excluded rows; use IncludedCompletedSales
and ExclusionReasons to distinguish them. SourceRow is the original Excel row including header.
Original numeric/date values are retained in audit columns. No categories, costs, profit,
outlier caps or return-to-sale matching were created. December 2011 is partial.

CSV import: set InvoiceNo, StockCode and CustomerID to Text in Excel/Power BI or VARCHAR
in MySQL/MariaDB; blank CustomerID means missing. LineSalesPence is the authoritative
integer money field; LineSalesGBP is an exact two-decimal display/export field.