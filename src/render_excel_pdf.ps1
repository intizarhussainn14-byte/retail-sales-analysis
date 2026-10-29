param([Parameter(Mandatory=$true)][string]$WorkDir)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime] | Out-Null
$asyncMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Count -eq 1 -and
    $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
$actionMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
} | Select-Object -First 1
function Wait-WinRT($Operation, [Type]$ResultType) {
    $task = $asyncMethod.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}
foreach ($pdf in Get-ChildItem -LiteralPath $WorkDir -Filter '*.pdf' -File) {
    $file = Wait-WinRT ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdf.FullName)) ([Windows.Storage.StorageFile])
    $document = Wait-WinRT ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
    for ($pageIndex = 0; $pageIndex -lt $document.PageCount; $pageIndex++) {
        $page = $document.GetPage($pageIndex)
        $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
        $task = $actionMethod.Invoke($null, @($page.RenderToStreamAsync($stream)))
        $task.Wait()
        $stream.Seek(0)
        $read = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
        $png = Join-Path $pdf.DirectoryName ($pdf.BaseName + '_' + ($pageIndex+1) + '.png')
        $output = [IO.File]::Create($png)
        try { $read.CopyTo($output) } finally { $output.Dispose(); $read.Dispose(); $page.Dispose() }
        Write-Output $png
    }
}
