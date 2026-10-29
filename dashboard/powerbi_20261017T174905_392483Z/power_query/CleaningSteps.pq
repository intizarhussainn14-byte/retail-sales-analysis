let
    Source = fnLoadCsv("CleaningSteps.csv", {
        {"Step", Int64.Type},
        {"ExclusionRule", type text},
        {"BeforeRows", Int64.Type},
        {"ExcludedRows", Int64.Type},
        {"AfterRows", Int64.Type},
        {"ExcludedSignedGBP", Currency.Type},
        {"ExcludedAbsoluteGBP", Currency.Type},
        {"UnvaluedRows", Int64.Type}
    })
in
    Source
