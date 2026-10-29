let
    Source = fnLoadCsv("DimDate.csv", {
        {"Date", type date},
        {"Year", Int64.Type},
        {"MonthNumber", Int64.Type},
        {"MonthStart", type date},
        {"YearMonth", type text},
        {"YearMonthSort", Int64.Type},
        {"CoverageStatus", type text},
        {"MonthLabel", type text},
        {"IsComparableMonth", Int64.Type},
        {"InObservationWindow", Int64.Type}
    })
in
    Source
