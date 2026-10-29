(FileName as text, Types as list) as table =>
let
    Raw = Csv.Document(File.Contents(pDataFolder & "/" & FileName),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, Types, "en-GB"),
    NullCustomer = if Table.HasColumns(Typed, "CustomerID") then
        Table.TransformColumns(Typed, {{"CustomerID", each if _ = "" then null else _, type nullable text}})
        else Typed
in
    NullCustomer
