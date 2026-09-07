<#
.SYNOPSIS
    Beendet die Arena-Runner.
.EXAMPLE
    .\arena-stop.ps1
    .\arena-stop.ps1 -Only Grok
#>
[CmdletBinding()]
param([string[]] $Only)
$ErrorActionPreference = 'Stop'

$pidFile = Join-Path $PSScriptRoot 'state\pids.json'
if (-not (Test-Path $pidFile)) { Write-Host "Keine laufenden Runner vermerkt."; return }

$pids = Get-Content $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json
$rest = @{}
foreach ($e in $pids.PSObject.Properties) {
    if ($Only -and ($Only -notcontains $e.Name)) { $rest[$e.Name] = $e.Value; continue }
    $p = Get-Process -Id $e.Value -ErrorAction SilentlyContinue
    if ($p) { Stop-Process -Id $e.Value -Force; Write-Host ("{0,-9} gestoppt (PID {1})" -f $e.Name, $e.Value) -ForegroundColor Yellow }
    else    { Write-Host ("{0,-9} lief nicht mehr." -f $e.Name) }
}
$rest | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
