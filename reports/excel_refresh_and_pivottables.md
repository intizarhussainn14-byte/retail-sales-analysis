# Excel workbook refresh and manual PivotTables

The completed [Retail_Sales_Analysis.xlsx](Retail_Sales_Analysis.xlsx) is a snapshot of validated outputs, not a live database connection. It includes genuine **MonthlySalesPivot** and **CountrySalesPivot** at I5 on their corresponding sheets, created by native Excel from embedded aggregate summaries. All other formatted blocks are summary tables, not PivotTables. Refresh All refreshes embedded pivot caches; it does not rerun Python or reload source CSVs. Regenerate with `.\.venv\Scripts\python.exe src/build_excel.py --replace` to update the snapshot. This command needs installed Windows Excel Desktop and archives the existing workbook.

The manual workflow below creates **additional transaction-level/Data Model PivotTables**, not the two already included aggregate-summary pivots. It is optional and has not been executed as part of the summary workbook. Do not call these optional transaction-level pivots complete until you create them.

## Regenerate source analysis

From the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe src/analyze_sales.py
```

The script prints a new `reports/analysis_<timestamp>/` directory. Use that exact directory when regenerating the workbook. For a new cleaning run, first follow the cleaning and validation commands in README.md, then pass the corresponding `--input` to the analysis script. Never edit the raw workbook. Keep previous workbook versions.

## Exact manual PivotTable workflow (Excel for Windows with Data Model)

1. Open a copy of the analysis workbook. Choose **Data > Get Data > From File > From Text/CSV** and select the validated `data/processed/cleaning_20261017T162742_974298Z/completed_sales.csv` (or the validated replacement run).
2. Choose **Transform Data**. Remove the automatic **Changed Type** step if it converted identifiers. Set InvoiceNo, StockCode, CustomerID and Description to **Text**; InvoiceDate to **Date/Time**; Quantity and LineSalesPence to **Whole Number**. Set LineSalesGBP to **Fixed Decimal Number**. Leave blank customer IDs as null; never fill them with a fabricated customer.
3. Keep the fields above plus Country. Name the query **CompletedSales**. Add Column > Date > Month > Start of Month from InvoiceDate; name this **MonthStart**, type Date. Keep all anonymous sales.
4. Choose **Home > Close & Load > Close & Load To... > Only Create Connection** and check **Add this data to the Data Model**. This avoids displaying over 522,000 lines on a presentation sheet.
5. Choose **Insert > PivotTable > From Data Model**, place on a new sheet. Create these measures through **Power Pivot > Measures > New Measure** (table CompletedSales):

```dax
Revenue GBP := DIVIDE(SUM(CompletedSales[LineSalesPence]), 100)
Completed Orders := DISTINCTCOUNT(CompletedSales[InvoiceNo])
Units Sold := SUM(CompletedSales[Quantity])
Average Order Value GBP := DIVIDE([Revenue GBP], [Completed Orders])
Known Customers := CALCULATE(DISTINCTCOUNT(CompletedSales[CustomerID]), CompletedSales[CustomerID] <> BLANK())
```

Enter the text after `:=` as the formula in the New Measure dialog, and the name before it as Measure Name. Format revenue/AOV as GBP currency with two decimals, counts as whole numbers. AOV uses revenue divided by distinct orders, not the average line value. Count of InvoiceNo is a line count and must not replace distinct order count.

6. **Monthly PivotTable:** Rows = MonthStart; Values = Revenue GBP, Completed Orders, Units Sold. Format MonthStart as `mmm yyyy`; sort oldest first. If Excel auto-groups dates, right-click and Ungroup, retaining MonthStart. Insert a line PivotChart titled **Completed-sales revenue (GBP); Dec 2011 partial**. Add a visible note: **Dec 2010 starts on day 1; completeness unverified. Dec 2011 only through day 9.** For a second Revenue measure choose Value Field Settings > Show Values As > % Difference From > Base field MonthStart > Previous. Label this **Observed MoM; boundary comparisons unqualified**; use the Python ComparableMoMPct column for comparisons that exclude boundary pairs. Do not describe the partial December decline as business decline.
7. **Products by revenue:** new PivotTable, Rows = StockCode; Values = Revenue GBP and Units Sold. Right-click a revenue value > Sort > Largest to Smallest. StockCode filter > Value Filters > Top 10 > Top 10 Items by Revenue GBP. Use the full cleaned source, not the already limited top-ten summary. Repeat on another sheet with Top 10 by Units Sold. Product descriptions may vary per code; grouping by description could split one product. Keep StockCode as the grouping key.
8. **Country performance:** Rows = Country; Values = Revenue GBP, Completed Orders, Average Order Value GBP. Sort revenue descending. Keep anonymous-customer sales included.
9. **Customer purchases:** import the analysis run's `customer_purchases.csv` with CustomerID as Text, CompletedOrders/UnitsSold/RepeatCustomer as Whole Number and RevenueGBP as Fixed Decimal Number. This already has one row per known customer. Load it to a table named **CustomerPurchases**, then Insert > PivotTable > From Table/Range > New Worksheet. Rows = RepeatCustomer; Values = Count of CustomerID and Sum of RevenueGBP. Label 0 as **One completed order** and 1 as **Two or more completed orders**. Show a second Count of CustomerID as % of Grand Total. Because this source is one row per known ID, ordinary Count is correct here. Do not include anonymous rows as one customer or use the number of product lines as purchase frequency.

## Refresh manually created connections

For unchanged file paths, **Data > Refresh All** updates the imported queries and PivotTables. If a Python run produced new folders, **Data > Queries & Connections > right-click query > Edit > Source gear** and point to the new validated CSV, then Close & Load and Refresh All. Refresh CompletedSales and CustomerPurchases together. Confirm the date window and compare revenue, orders, units, AOV and known customers against that run's `kpis.csv`. Refreshing PivotTables does not update the separately generated snapshot summary sheets; regenerate those from the same analysis run.

If Data Model/Distinct Count is unavailable in your Excel edition, use the supplied Python summary tables for distinct-order metrics. Do not substitute an ordinary invoice count. You can still create simple revenue/quantity PivotTables, or pivot `customer_purchases.csv` as described above.

## Source and interpretation

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33 . Dataset page: https://archive.ics.uci.edu/dataset/352/online+retail . License: CC BY 4.0. The local measured coverage is 2010-12-01 08:26 to 2011-12-09 12:50.

Completed-sales revenue excludes cancellations, negative adjustments, excluded charges/vouchers and extra exact duplicates. It is not net revenue or profit. Missing IDs restrict customer analysis. Repeat purchasing describes this window, not lifetime retention. Product categories, costs and return-to-sale matches were not inferred. Observed patterns do not establish causes. The source site's missing-data metadata does not override the missing values measured in this workbook's local inspection.
