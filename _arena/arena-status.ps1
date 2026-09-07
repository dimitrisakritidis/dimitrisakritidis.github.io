<#
.SYNOPSIS
    Zeigt, welcher Runner laeuft, was er zuletzt getan hat und wo er im Chat steht.
#>
[CmdletBinding()]
param([int] $LogLines = 3)

$cfg     = Get-Content (Join-Path $PSScriptRoot 'arena.config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$pidFile = Join-Path $PSScriptRoot 'state\pids.json'
$pids    = if (Test-Path $pidFile) { Get-Content $pidFile -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }

foreach ($m in $cfg.models) {
    $procId = if ($pids -and ($pids.PSObject.Properties.Name -contains $m.name)) { $pids.$($m.name) } else { $null }
    $live   = $procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)
    $stFile = Join-Path $PSScriptRoot ("state\{0}.json" -f $m.name.ToLower())
    $st     = if (Test-Path $stFile) { Get-Content $stFile -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }

    $farbe = if ($live) { 'Green' } else { 'DarkGray' }
    Write-Host ("`n{0,-9} {1,-8} PID {2,-8} lastId={3,-6} heute={4}" -f `
        $m.name, $(if ($live) {'LAEUFT'} else {'AUS'}), ($procId, '-')[!$procId],
        $(if ($st) { $st.lastId } else { '-' }), $(if ($st) { $st.postedToday } else { '-' })) -ForegroundColor $farbe

    $log = Join-Path $PSScriptRoot ("logs\{0}.log" -f $m.name.ToLower())
    if (Test-Path $log) { Get-Content $log -Tail $LogLines | ForEach-Object { Write-Host "   $_" -ForegroundColor DarkGray } }
}
Write-Host ""
