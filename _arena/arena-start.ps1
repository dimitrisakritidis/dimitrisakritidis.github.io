<#
.SYNOPSIS
    Startet alle Arena-Runner dauerhaft im Hintergrund.
.EXAMPLE
    .\arena-start.ps1
    .\arena-start.ps1 -Only Claude,Grok -IntervalSeconds 60
#>
[CmdletBinding()]
param(
    [string[]] $Only,
    [int] $IntervalSeconds = 60,
    [switch] $ShowWindows
)
$ErrorActionPreference = 'Stop'

$cfg   = Get-Content (Join-Path $PSScriptRoot 'arena.config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$state = Join-Path $PSScriptRoot 'state'
if (-not (Test-Path $state)) { New-Item -ItemType Directory -Path $state -Force | Out-Null }
$pidFile = Join-Path $state 'pids.json'

$targets = if ($Only) { $cfg.models | Where-Object { $Only -contains $_.name } } else { $cfg.models }
if (-not $targets) { throw "Keine passenden Modelle in der Config gefunden." }

# Vorab pruefen, damit nicht vier Prozesse starten und drei sofort sterben.
$fehler = @()
foreach ($m in $targets) {
    if (-not (Get-Command $m.engine.cmd -ErrorAction SilentlyContinue)) {
        $fehler += "  $($m.name): CLI '$($m.engine.cmd)' nicht im PATH gefunden."
    }
    if (-not [Environment]::GetEnvironmentVariable($m.arenaKeyEnv)) {
        $fehler += "  $($m.name): Umgebungsvariable $($m.arenaKeyEnv) ist nicht gesetzt."
    }
}
if ($fehler) {
    Write-Host "`nSo startet das nicht:`n" -ForegroundColor Red
    $fehler | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Write-Host "`nJedes Modell braucht einen EIGENEN Arena-Key - der Anzeigename haengt am Key.`n"
    throw "Vorpruefung fehlgeschlagen."
}

$running = @{}
if (Test-Path $pidFile) {
    (Get-Content $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties |
        ForEach-Object { $running[$_.Name] = $_.Value }
}

$pwsh   = (Get-Process -Id $PID).Path
$style  = if ($ShowWindows) { 'Normal' } else { 'Hidden' }
$result = @{}

foreach ($m in $targets) {
    $alt = $running[$m.name]
    if ($alt -and (Get-Process -Id $alt -ErrorAction SilentlyContinue)) {
        Write-Host ("{0,-9} laeuft bereits (PID {1}) - uebersprungen." -f $m.name, $alt) -ForegroundColor Yellow
        $result[$m.name] = $alt
        continue
    }
    $args = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        (Join-Path $PSScriptRoot 'arena-runner.ps1'),
        '-Model', $m.name, '-IntervalSeconds', $IntervalSeconds
    )
    $p = Start-Process -FilePath $pwsh -ArgumentList $args -WindowStyle $style -PassThru
    $result[$m.name] = $p.Id
    Write-Host ("{0,-9} gestartet (PID {1}), Takt {2}s" -f $m.name, $p.Id, $IntervalSeconds) -ForegroundColor Green
    Start-Sleep -Milliseconds 700   # versetzt starten, damit nicht alle gleichzeitig posten
}

$result | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
Write-Host "`nLogs: $(Join-Path $PSScriptRoot 'logs')`nStoppen: .\arena-stop.ps1`n"
