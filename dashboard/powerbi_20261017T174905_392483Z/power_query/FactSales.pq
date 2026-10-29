let
    Source = fnLoadCsv("FactSales.csv", {
        {"SourceRow", Int64.Type},
        {"InvoiceNo", type text},
        {"StockCode", type text},
        {"Quantity", Int64.Type},
        {"InvoiceDate", type datetime},
        {"SaleDate", type date},
        {"UnitPrice", type number},
        {"CustomerID", type text},
        {"Country", type text},
        {"LineSalesPence", Int64.Type},
        {"LineSalesGBP", Currency.Type},
        {"CustomerMetricsEligible", Int64.Type},
        {"ProductKey", Int64.Type}
    })
in
    Source
