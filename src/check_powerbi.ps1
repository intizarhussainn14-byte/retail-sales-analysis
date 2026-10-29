# Read-only local capability check; does not launch, install or change software.
param([string]$OutputPath = 'reports/powerbi_availability.json')
$commands = @('PBIDesktop','pbi-tools','dotnet') | ForEach-Object {
    $command = Get-Command $_ -ErrorAction SilentlyContinue
    if ($command) { [pscustomobject]@{Name=$_;Path=$command.Source} }
}
$executables = @('C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe',
    'C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe') |
    Where-Object {Test-Path -LiteralPath $_}
$storeErrors = @()
$store = @(Get-AppxPackage -Name '*PowerBI*' -ErrorAction SilentlyContinue -ErrorVariable storeErrors |
    Select-Object Name,InstallLocation)
$installed = @()
$registryErrors = @()
foreach ($hive in @([Microsoft.Win32.Registry]::LocalMachine,[Microsoft.Win32.Registry]::CurrentUser)) {
    foreach ($branch in @('SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
            'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall')) {
        $base = $hive.OpenSubKey($branch)
        if ($base) {
            foreach ($name in $base.GetSubKeyNames()) {
                try {
                    $item = $base.OpenSubKey($name)
                    $display = $item.GetValue('DisplayName')
                    if ($display -match 'Power BI') {
                        $installed += [pscustomobject]@{Name=$display;InstallLocation=$item.GetValue('InstallLocation')}
                    }
                    if ($item) {$item.Close()}
                } catch {$registryErrors += $name}
            }
            $base.Close()
        }
    }
}
$processes = @(Get-Process PBIDesktop -ErrorAction SilentlyContinue | Select-Object ProcessName,Id)
$result = 'No supported native authoring/validation engine detected in checked locations; a portable or other-user installation is not ruled out.'
if (@($commands).Count -gt 0 -or @($executables).Count -gt 0 -or $store.Count -gt 0 -or $installed.Count -gt 0 -or $processes.Count -gt 0) {
    $result = 'Potential tools or installation detected; inspect entries and verify native authoring support before use.'
}
[ordered]@{
    CheckedAtUTC=[DateTime]::UtcNow.ToString('o')
    Commands=@($commands);CommonExecutablePaths=@($executables);StorePackages=$store
    UninstallRegistryEntries=$installed;RunningProcesses=$processes
    RegistryUnreadableEntryCount=$registryErrors.Count;StoreQueryErrorCount=$storeErrors.Count
    Result=$result
    NativeReportCreated=$false;SoftwareInstalledOrModified=$false
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Get-Content -LiteralPath $OutputPath
