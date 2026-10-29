# Retail workbook inspection

Source: `data\raw\Online Retail.xlsx`
SHA-256: `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`

Read-only inspection; no rows removed or values changed.

Sheets: Online Retail

## Online Retail

```json
{
  "row_count": 541909,
  "columns": [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country"
  ],
  "dtypes": {
    "InvoiceNo": "string",
    "StockCode": "string",
    "Description": "object",
    "Quantity": "int64",
    "InvoiceDate": "datetime64[ns]",
    "UnitPrice": "float64",
    "CustomerID": "string",
    "Country": "object"
  },
  "missing_values": {
    "InvoiceNo": 0,
    "StockCode": 0,
    "Description": 1454,
    "Quantity": 0,
    "InvoiceDate": 0,
    "UnitPrice": 0,
    "CustomerID": 135080,
    "Country": 0
  },
  "exact_duplicate_extra_rows": 5268,
  "all_rows_in_duplicate_groups": 10147,
  "unique_nonmissing": {
    "InvoiceNo": 25900,
    "StockCode": 4070,
    "CustomerID": 4372,
    "Country": 38
  },
  "date_range": {
    "min": "2010-12-01 08:26:00",
    "max": "2011-12-09 12:50:00",
    "invalid_nonmissing": 0
  },
  "Quantity": {
    "negative": 10624,
    "zero": 0,
    "min": -80995.0,
    "max": 80995.0,
    "invalid_nonmissing": 0
  },
  "UnitPrice": {
    "negative": 2,
    "zero": 2515,
    "min": -11062.06,
    "max": 38970.0,
    "invalid_nonmissing": 0
  },
  "cancellations": {
    "rows": 9288,
    "unique_invoices": 3836,
    "examples": [
      "C536379",
      "C536383",
      "C536391",
      "C536506",
      "C536543"
    ],
    "negative_quantity_without_C": 1336,
    "C_with_nonnegative_quantity": 0
  },
  "identifier_checks": {
    "InvoiceNo": {
      "examples": [
        "536365",
        "536366",
        "536367",
        "536368",
        "536369",
        "536370",
        "536371",
        "536372"
      ],
      "surrounding_whitespace_rows": 0,
      "nonnumeric_examples": [
        "C536379",
        "C536383",
        "C536391",
        "C536506",
        "C536543",
        "C536548",
        "C536606",
        "C536622",
        "C536625",
        "C536642",
        "C536734",
        "C536737"
      ]
    },
    "StockCode": {
      "examples": [
        "85123A",
        "71053",
        "84406B",
        "84029G",
        "84029E",
        "22752",
        "21730",
        "22633"
      ],
      "surrounding_whitespace_rows": 0,
      "nonnumeric_examples": [
        "85123A",
        "84406B",
        "84029G",
        "84029E",
        "POST",
        "82494L",
        "85099C",
        "84997B",
        "84997C",
        "84519A",
        "85183B",
        "85071B"
      ]
    },
    "CustomerID": {
      "examples": [
        "17850",
        "13047",
        "12583",
        "13748",
        "15100",
        "15291",
        "14688",
        "17809"
      ],
      "surrounding_whitespace_rows": 0,
      "nonnumeric_examples": []
    }
  }
}
```

Source checksum verified unchanged.

Counts refer to invoice line items, not orders. Unique counts exclude missing values.
Duplicate count means extra identical rows after the first. Dates are timezone-naive source values.
Identifiers are loaded as strings, not measures. No whitespace or case normalization is applied.