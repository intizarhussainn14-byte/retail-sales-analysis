let
    Source = fnLoadCsv("DimProduct.csv", {
        {"ProductKey", Int64.Type},
        {"StockCode", type text},
        {"Description", type text},
        {"StockCodeUTF8Hex", type text},
        {"ProductLabel", type text}
    })
in
    Source
