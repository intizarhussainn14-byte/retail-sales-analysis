let
    Source = fnLoadCsv("DimCountry.csv", {
        {"Country", type text}
    })
in
    Source
