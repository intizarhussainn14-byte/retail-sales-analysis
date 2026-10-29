# Start the Power BI Desktop build

**Status:** validated import package only. No native report exists. M, DAX,
visuals and interactions have not run in Desktop. Local checks found no Desktop
executable, Store installation, uninstall entry, process or supported CLI tool.
A portable installation or another user's installation is not ruled out.

## First manual step

Open **Power BI Desktop** from Windows Start. If absent, install it using
[Microsoft's official instructions](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop),
then open a **Blank report**. This project has not installed software.

1. Choose **Home > Transform data** to open Power Query Editor. If prompted for
   a source first, choose **Get data > Blank query**.
2. In the editor, choose **Home > New Source > Blank Query**. Rename the query
   **pDataFolder** (exact spelling).
3. Open **Home > Advanced Editor**, replace its contents with the single quoted
   path below, then select **Done**:

   ```powerquery
   "F:/Data Science/Retail Sales Analysis Dashboard/dashboard/powerbi_20261017T174905_392483Z/data"
   ```

4. The preview should display that folder path as a text value. If the project
   moved, use the actual package's `data` folder.

Continue with [the import/model guide](POWER_BI_DESKTOP.md), section 2: create
**fnLoadCsv**, then the six table queries from the package's `power_query` folder.
Helpers are not model tables. Close & Apply after all six table previews show
the expected names and types.

Use [the current package](powerbi_20261017T174905_392483Z/START_HERE.md) and its
[page layout plan](powerbi_20261017T174905_392483Z/REPORT_LAYOUT.md), model_spec.json,
measures.dax and retail_theme.json. The layout and model specifications are
manual instructions, not native Power BI formats.

## Desktop acceptance checks

After creating relationships and measures, open **DAX Query view > New query**,
paste the package's `validate_measures.dax`, and choose **Run**. Compare its six
rows with `expected_filter_totals.csv` by Scenario: counts exactly, GBP and
percentage points to two decimals. The query sets its own filters; it does not
test UI slicer interactions.

Separately set each date/country scenario on the report pages. Compare the cards
and both product charts with the expected totals and top-ten CSVs. Confirm country
choices filter both product charts, and product bar selections leave the other
top-ten chart independent as specified in REPORT_LAYOUT.md.

A mid-month cut must blank qualified MoM. December 2011 and January 2011 versus
the December 2010 boundary must also be blank. With all countries and no product
selection, February 2011 should show GBP -162,580.37 and -24.25%; November 2011
GBP 348,801.73 and 31.61%. Clear chart selections before comparing.

Inspect all pages at 100% zoom, long product tooltips, GBP labels and coverage
notes. Record actual results and save a genuine PBIX after checks pass. Until
then the Power BI deliverable remains a prepared handoff.
