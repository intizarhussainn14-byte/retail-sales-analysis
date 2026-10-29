param([Parameter(Mandatory=$true)][string]$WorkDir)
$ErrorActionPreference = 'Stop'
$excelApp = $null
$workbook = $null
$workPath = (Resolve-Path -LiteralPath $WorkDir).Path
$draft = Join-Path $workPath 'draft.xlsx'
$ready = Join-Path $workPath 'ready.xlsx'
if (Test-Path -LiteralPath $ready) { throw 'Staged ready.xlsx already exists; preserve it and use a new build run' }
try {
    $excelApp = New-Object -ComObject Excel.Application
    $excelApp.Visible = $false
    $excelApp.DisplayAlerts = $false
    $excelApp.AskToUpdateLinks = $false
    $excelApp.AutomationSecurity = 3
    $workbook = $excelApp.Workbooks.Open($draft, 0, $false)
    $excelApp.Calculation = -4105
    $excelApp.CalculateFullRebuild()
    $gbpFormat = ([char]0x00A3) + '#,##0.00;[Red](' + ([char]0x00A3) + '#,##0.00)'
    $monthly = $workbook.Worksheets.Item('Monthly Sales')
    $monthCache = $workbook.PivotCaches().Create(1, "'Monthly Sales'!R5C1:R18C3")
    $monthPivot = $monthCache.CreatePivotTable($monthly.Range('I5'), 'MonthlySalesPivot')
    $monthPivot.PivotFields('Month').Orientation = 1
    $monthPivot.PivotFields('Month').Position = 1
    $monthPivot.PivotFields('Month').NumberFormat = 'mmm yyyy'
    $monthRevenue = $monthPivot.AddDataField($monthPivot.PivotFields('Revenue GBP'), 'Revenue GBP (sum)', -4157)
    $monthRevenue.NumberFormat = $gbpFormat
    $monthOrders = $monthPivot.AddDataField($monthPivot.PivotFields('Completed orders'), 'Completed orders (sum)', -4157)
    $monthOrders.NumberFormat = '#,##0'
    $monthPivot.TableStyle2 = 'PivotStyleMedium9'
    $monthPivot.RowAxisLayout(1)
    $monthCache.RefreshOnFileOpen = $false
    $country = $workbook.Worksheets.Item('Country Performance')
    $countryCache = $workbook.PivotCaches().Create(1, "'Country Performance'!R5C1:R43C3")
    $countryPivot = $countryCache.CreatePivotTable($country.Range('I5'), 'CountrySalesPivot')
    $countryPivot.PivotFields('Country').Orientation = 1
    $countryPivot.PivotFields('Country').Position = 1
    $countryRevenue = $countryPivot.AddDataField($countryPivot.PivotFields('Revenue GBP'), 'Revenue GBP (sum)', -4157)
    $countryRevenue.NumberFormat = $gbpFormat
    $countryOrders = $countryPivot.AddDataField($countryPivot.PivotFields('Completed orders'), 'Completed orders (sum)', -4157)
    $countryOrders.NumberFormat = '#,##0'
    $countryPivot.PivotFields('Country').AutoSort(2, 'Revenue GBP (sum)')
    $countryPivot.TableStyle2 = 'PivotStyleMedium9'
    $countryPivot.RowAxisLayout(1)
    $countryCache.RefreshOnFileOpen = $false
    $sources = $workbook.Worksheets.Item('Sources')
    $sources.Range('A44').Value2 = 'Native Excel PivotTables created: MonthlySalesPivot (Monthly Sales!I5) and CountrySalesPivot (Country Performance!I5). Both summarize embedded verified aggregate rows, not transaction-level facts.'
    foreach ($sheet in $workbook.Worksheets) {
        $sheet.UsedRange.Font.Name = 'Calibri'
        $sheet.Activate()
        $excelApp.ActiveWindow.Zoom = 85
        foreach ($pivot in $sheet.PivotTables()) {
            $pivot.TableRange2.Font.Size = 10
            $pivot.TableRange2.Rows.Item(1).WrapText = $true
        }
    }
    foreach ($s in @($monthly, $country)) {
        $s.Columns.Item('I').ColumnWidth = 25
        $s.Columns.Item('J').ColumnWidth = 24
        $s.Columns.Item('K').ColumnWidth = 26
        $s.Columns.Item('L').ColumnWidth = 3
    }
    function Add-AnalysisChart($sheet, $title, $categories, $values, $anchor, $widthRange, $height, $kind) {
        $origin = $sheet.Range($anchor)
        $obj = $sheet.ChartObjects().Add($origin.Left, $origin.Top, $sheet.Range($widthRange).Width, $height)
        $chart = $obj.Chart
        $chart.ChartType = if ($kind -eq 'line') { 4 } else { 57 }
        $chart.HasLegend = $false
        $chart.HasTitle = $true
        $chart.ChartTitle.Text = $title
        $chart.ChartTitle.Font.Size = 12
        $chart.ChartArea.Font.Name = 'Calibri'
        $chart.ChartArea.Font.Size = 10
        $chart.ChartArea.Format.Line.Visible = 0
        $chart.ChartArea.Format.Fill.ForeColor.RGB = 0xFFFFFF
        $series = $chart.SeriesCollection().NewSeries()
        $series.Name = $title
        $series.XValues = $sheet.Range($categories)
        $series.Values = $sheet.Range($values)
        $categoryAxis = $chart.Axes(1)
        $valueAxis = $chart.Axes(2)
        $categoryAxis.TickLabelPosition = 4
        $valueAxis.TickLabelPosition = 4
        $categoryAxis.TickLabels.Font.Color = 0
        $valueAxis.TickLabels.Font.Color = 0
        $categoryAxis.TickLabels.Font.Size = 10
        $valueAxis.TickLabels.Font.Size = 10
        $valueAxis.MinimumScale = 0
        $valueAxis.TickLabels.NumberFormat = if ($title -like '*GBP*') { ([char]0x00A3) + '#,##0' } else { '#,##0' }
        $valueAxis.HasMajorGridlines = $true
        $valueAxis.MajorGridlines.Format.Line.ForeColor.RGB = 0xE6E6E6
        if ($kind -eq 'line') {
            $categoryAxis.CategoryType = 3
            $categoryAxis.BaseUnit = 1
            $categoryAxis.MajorUnit = 1
            $categoryAxis.MajorUnitScale = 1
            $categoryAxis.TickLabels.NumberFormat = 'mmm yy'
            $series.Smooth = $false
            $series.MarkerStyle = 8
            $series.MarkerSize = 4
            $series.Format.Line.ForeColor.RGB = 0x8B7E08
            $series.Format.Line.Weight = 2
        } else {
            $categoryAxis.ReversePlotOrder = $true
            $categoryAxis.Crosses = 2
            $series.Format.Fill.Solid()
            $series.Format.Fill.ForeColor.RGB = 0x8B7E08
            $series.Format.Line.Visible = 0
        }
    }
    Add-AnalysisChart $monthly 'Monthly sales (GBP) - Dec 2011 partial' 'A6:A18' 'B6:B18' 'A24' 'A24:G24' 250 'line'
    $products = $workbook.Worksheets.Item('Top Products')
    Add-AnalysisChart $products 'Top products by revenue (GBP)' 'B6:B15' 'E6:E15' 'G5' 'G5:L5' 300 'bar'
    Add-AnalysisChart $products 'Top products by units' 'B24:B33' 'D24:D33' 'G23' 'G23:L23' 300 'bar'
    Add-AnalysisChart $country 'Top 10 non-UK markets (GBP)' 'A7:A16' 'B7:B16' 'A49' 'A49:G49' 300 'bar'
    $excelApp.CalculateFullRebuild()
    $excelApp.CalculateBeforeSave = $true
    $workbook.Worksheets.Item('Overview').Activate()
    $workbook.SaveAs($ready, 51)
    $pivotCount = 0
    $chartCount = 0
    $rendered = @()
    foreach ($sheet in $workbook.Worksheets) {
        $pivotCount += $sheet.PivotTables().Count
        $chartCount += $sheet.ChartObjects().Count
        $pdfPath = Join-Path $workPath (($sheet.Name -replace ' ', '_') + '.pdf')
        $sheet.ExportAsFixedFormat(0, $pdfPath)
        $rendered += $pdfPath
    }
    $result = @{ ExcelVersion=$excelApp.Version; PivotTables=$pivotCount; Charts=$chartCount;
        Calculation='CalculateFullRebuild'; PDFs=$rendered; NativePivotSource='Verified embedded monthly/country summary rows' }
    $result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $workPath 'excel_engine.json') -Encoding UTF8
    Write-Output ('Excel finalized: ' + $ready)
    Write-Output ('Native pivots: ' + $pivotCount + '; charts: ' + $chartCount)
}
finally {
    if ($null -ne $workbook) { $workbook.Close($false) }
    if ($null -ne $excelApp) {
        $excelApp.Quit()
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($excelApp)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
