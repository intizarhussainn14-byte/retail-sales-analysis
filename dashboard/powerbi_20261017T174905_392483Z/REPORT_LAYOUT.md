# Desktop page construction plan (not a rendered report)

Use a custom 1440 x 900 canvas on every page. Coordinates below are x, y, width,
height in pixels under Format > General > Properties. Import retail_theme.json
using Import theme (Design ribbon in recent releases; View > Themes in others).
Titles: Segoe UI 20, chart labels 11+, body notes 12. White canvas, navy headings,
teal revenue, amber coverage notes. GBP values: £#,##0.00;(£#,##0.00); counts: #,##0;
rates: 0.00%. Disable K/M display units on cards. These are manual placement
instructions, not an importable report definition or checked native visuals.

Shared on ALL pages: title (24,16,1392,42); Between date slicer DimDate[Date]
(24,70,880,65), with InObservationWindow = 1; country dropdown DimCountry[Country]
(928,70,488,65). Sync both slicers on all pages. Initial dates 01 Dec 2010–09 Dec
2011, all countries. Footnote (24,842,1392,42): “Completed-sales revenue (GBP)
excludes cancellations and negative adjustments; it is not net revenue.”

## Sales Overview

- Four cards at y=153, h=108, w=330, x=24/378/732/1086: Revenue GBP,
  Completed Orders, Units Sold, Average Order Value GBP. Titles include GBP
  on revenue and AOV.
- Line chart (24,282,880,320): DimDate[MonthLabel] categorical X; Revenue GBP Y;
  tooltips Completed Orders, Month Coverage, Comparable MoM Percent.
- Customer cards (928,282,488,100), (928,394,488,100), (928,506,488,96):
  Known Customers, Repeat Customers, Repeat Customer Rate.
- Monthly table (24,622,1000,200): MonthLabel, Revenue GBP, Completed Orders,
  Comparable MoM Change GBP, Comparable MoM Percent. Sort MonthLabel ascending
  by YearMonthSort; growth totals blank.
- Note (1048,622,368,200): “Repeat rate = customers with 2+ distinct completed
  orders / known customers with sales in the current date/country/product
  selection. Not lifetime retention. Dec 2010 boundary completeness unverified;
  Dec 2011 partial through 9 Dec. Qualified MoM omits boundary/cut months and
  compares with the preceding full calendar month, even outside the date slicer.”

## Products and Markets

- Revenue bar (24,153,684,330): Y DimProduct[ProductLabel], X Revenue GBP,
  visual filter Show Top 10 Revenue = 1. Sort revenue descending.
- Units bar (732,153,684,330): same Y, X Units Sold,
  visual filter Show Top 10 Quantity = 1. Sort units descending.
- Country bar (24,505,684,315): Y DimCountry[Country], X Revenue GBP; sort revenue
  descending. All countries, scroll for smaller markets. Tooltip Completed Orders.
- Country table (732,505,684,315): Country, Revenue GBP, Completed Orders,
  Units Sold, Average Order Value GBP. Use scrolling rather than tiny labels.
- Full ProductLabel in tooltips; original StockCode may merge displayed case,
  so use collision-safe ProductLabel for axes. Do not use a static top-ten CSV.
- Edit interactions: date/country slicers FILTER all dynamic visuals. Country
  bar/table FILTER both product bars. Set each product bar's interaction with
  the other product bar and country visuals to NONE. This preserves independent
  revenue/quantity top tens and country context. Country slicer remains the
  cross-page market selection. Confirm top-ten membership after changing it.

## Data Quality

- Six cards, 3 columns x 2 rows; x=24/496/968, w=448, h=85, y=153/250:
  Raw Lines, Excluded Lines, Exclusion Rate, Raw Missing Customer Lines,
  Raw Missing Customer Rate, Retained Missing Customer Lines.
- Exclusion bar (24,355,684,255): Y QualityRows[ExclusionRule], X Excluded Lines;
  visual filter QualityRows[IsIncluded] = 0. Title “Disjoint exclusions — selected
  dates and country”. Counts sum to Excluded Lines.
- Table (732,355,684,255): Cancellation Lines, Negative Quantity Lines,
  Nonpositive Price Lines, Exact Duplicate Extras, Conversion Failure Lines,
  Missing Description Lines. Title “Overlapping source flags — do not add”.
- Limitations text (24,630,1392,190): “Source: Chen (2015), Online Retail, UCI,
  doi:10.24432/C5BW33, CC BY 4.0. Anonymous eligible sales remain in revenue;
  only customer metrics exclude missing IDs. Exact-row deduplication is an
  assumption, repeated invoices are retained. No categories/costs/profit or
  return matches. Boundary months limit comparisons; large lines can dominate.
  Data-quality flags describe all original lines and are not sales metrics.”
- Optional global CleaningSteps table on a separate tooltip/reference view:
  label “Global cleaning reference — unaffected by slicers”; never add its
  totals to dynamic QualityRows metrics. Do not join it to any table.

## Completion gate

Create all six relationships from model_spec.json; mark DimDate[Date] as the
date table. Follow ../POWER_BI_DESKTOP.md for types, measures and sorting.
Run validate_measures.dax in DAX Query view, compare all six scenarios and the
top-ten reference CSV. Inspect the three pages at 100% zoom, tooltips, long
product labels, slicer interactions and cut-month MoM blanks. Save a genuine
PBIX only after these checks. This package has NOT performed those steps.
