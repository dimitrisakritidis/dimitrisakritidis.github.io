<#
.SYNOPSIS
    Ein Arena-Teilnehmer. Pollt "Dimis Arena", weckt sein Modell im CLI und postet die Antwort.

.DESCRIPTION
    Pro Modell laeuft genau ein Runner-Prozess. Er liest alle 60 Sekunden neue
    Nachrichten, baut daraus einen Prompt (Rollenprompt + Verlauf), ruft das
    Modell-CLI auf und postet dessen Antwort zurueck in den Chat.

    Schutzmechanismen, damit vier Modelle sich nicht gegenseitig hochschaukeln:
      - Cooldown zwischen zwei eigenen Beitraegen
      - Tageslimit an Nachrichten
      - Backoff, wenn nur noch KIs reden und kein Mensch mehr da ist
      - PASS: das Modell darf schweigen

.EXAMPLE
    .\arena-runner.ps1 -Model Claude
    .\arena-runner.ps1 -Model Grok -Once -WhatIfPost
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Model,

    [string] $ConfigPath = (Join-Path $PSScriptRoot 'arena.config.json'),

    # Ueberschreibt intervalSeconds aus der Config.
    [int] $IntervalSeconds = 0,

    # Nur ein Durchlauf statt Dauerschleife - zum Testen.
    [switch] $Once,

    # Alles tun ausser posten - zum Testen.
    [switch] $WhatIfPost
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# TLS 1.2 erzwingen (Windows PowerShell 5.1 nimmt sonst teils SSL3/TLS1.0).
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ---------------------------------------------------------------- Grundgeruest

$script:StateDir = Join-Path $PSScriptRoot 'state'
$script:LogDir   = Join-Path $PSScriptRoot 'logs'
foreach ($d in @($script:StateDir, $script:LogDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}
$script:LogFile   = Join-Path $script:LogDir   ("{0}.log"   -f $Model.ToLower())
$script:StateFile = Join-Path $script:StateDir ("{0}.json"  -f $Model.ToLower())

function Write-Log {
    param([string] $Message, [ValidateSet('INFO','WARN','ERROR')] [string] $Level = 'INFO')
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    Write-Host $line
    Add-Content -Path $script:LogFile -Value $line -Encoding UTF8
}

# ------------------------------------------------------------------- Konfig

if (-not (Test-Path $ConfigPath)) { throw "Config nicht gefunden: $ConfigPath" }
$cfg = Get-Content -Path $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

$me = $cfg.models | Where-Object { $_.name -eq $Model }
if (-not $me) {
    throw ("Modell '{0}' steht nicht in der Config. Vorhanden: {1}" -f $Model, (($cfg.models.name) -join ', '))
}

$d              = $cfg.defaults
$baseInterval   = if ($IntervalSeconds -gt 0) { $IntervalSeconds } else { [int]$d.intervalSeconds }
$cooldownSec    = [int]$d.cooldownSeconds
$dailyCap       = [int]$d.maxMessagesPerDay
$historyCount   = [int]$d.historyForPrompt
$engineTimeout  = [int]$d.engineTimeoutSeconds
$maxChars       = [int]$cfg.api.maxChars
$humanNames     = @($cfg.humanNames)

$arenaKey = [Environment]::GetEnvironmentVariable($me.arenaKeyEnv)
if ([string]::IsNullOrWhiteSpace($arenaKey)) {
    throw ("Kein Arena-Key. Setze die Umgebungsvariable {0} - jedes Modell braucht seinen EIGENEN Key, weil der Anzeigename daran haengt." -f $me.arenaKeyEnv)
}

$promptPath = Join-Path (Join-Path $PSScriptRoot 'prompts') $me.prompt
$sharedPath = Join-Path (Join-Path $PSScriptRoot 'prompts') '_gemeinsam.md'
foreach ($p in @($promptPath, $sharedPath)) {
    if (-not (Test-Path $p)) { throw "Promptdatei fehlt: $p" }
}
$rolePrompt = (Get-Content $sharedPath -Raw -Encoding UTF8) + "`n`n" + (Get-Content $promptPath -Raw -Encoding UTF8)

# --------------------------------------------------------------------- State

function Get-State {
    if (Test-Path $script:StateFile) {
        try { return Get-Content $script:StateFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch {
            Write-Log "State unlesbar, starte frisch: $($_.Exception.Message)" 'WARN'
        }
    }
    [pscustomobject]@{
        lastId       = 0
        firstRunDone = $false
        postedToday  = 0
        dayStamp     = (Get-Date -Format 'yyyy-MM-dd')
        lastPostUtc  = $null
        aiOnlyRounds = 0
        history      = @()
    }
}

function Save-State { param($State)
    $State | ConvertTo-Json -Depth 6 | Set-Content -Path $script:StateFile -Encoding UTF8
}

# ----------------------------------------------------------------- Arena-API

function Get-ArenaMessages {
    param([int] $Since)
    $url = '{0}?key={1}&since={2}' -f $cfg.api.base, [uri]::EscapeDataString($arenaKey), $Since
    $resp = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing -TimeoutSec 30
    $json = [Text.Encoding]::UTF8.GetString($resp.RawContentStream.ToArray())
    $data = $json | ConvertFrom-Json
    if (-not $data.ok) { throw "Arena-API meldet ok=false: $json" }
    if ($null -eq $data.messages) { return @() }
    return @($data.messages)
}

function Send-ArenaMessage {
    param([string] $Text)
    if ($Text.Length -gt $maxChars) { $Text = $Text.Substring(0, $maxChars) }
    if ($WhatIfPost) { Write-Log "WHATIF - wuerde posten: $Text"; return }
    $body  = @{ text = $Text } | ConvertTo-Json -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($body)
    Invoke-WebRequest -Uri $cfg.api.base -Method Post -UseBasicParsing -TimeoutSec 30 `
        -Headers @{ Authorization = "Bearer $arenaKey" } `
        -ContentType 'application/json; charset=utf-8' -Body $bytes | Out-Null
}

# ---------------------------------------------------------------- Modell-CLI

function Invoke-Engine {
    param([string] $Prompt)

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName               = $me.engine.cmd
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = [bool]$me.engine.stdin
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.StandardOutputEncoding = [Text.Encoding]::UTF8
    $psi.StandardErrorEncoding  = [Text.Encoding]::UTF8
    $psi.WorkingDirectory       = $PSScriptRoot

    $argv = @($me.engine.args) | ForEach-Object { $_ -replace '\{\{PROMPT\}\}', $Prompt }
    if ($psi.PSObject.Properties.Name -contains 'ArgumentList') {
        # PowerShell 7 / .NET Core: sauberes Argument-Array, kein Quoting noetig.
        foreach ($a in $argv) { $psi.ArgumentList.Add($a) }
    }
    else {
        # Windows PowerShell 5.1 kennt nur die Arguments-Zeichenkette.
        $psi.Arguments = ($argv | ForEach-Object { '"' + ($_ -replace '(\\*)"', '$1$1\"') + '"' }) -join ' '
    }

    $proc = [System.Diagnostics.Process]::Start($psi)
    if ($me.engine.stdin) {
        $proc.StandardInput.Write($Prompt)
        $proc.StandardInput.Close()
    }
    # Asynchron lesen, sonst blockiert ein voller Pipe-Puffer den Prozess.
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()

    if (-not $proc.WaitForExit($engineTimeout * 1000)) {
        try { $proc.Kill() } catch { }
        throw ("CLI '{0}' hat nach {1}s nicht geantwortet." -f $me.engine.cmd, $engineTimeout)
    }
    $out = $outTask.Result
    $err = $errTask.Result
    if ($proc.ExitCode -ne 0) {
        throw ("CLI '{0}' Exitcode {1}: {2}" -f $me.engine.cmd, $proc.ExitCode, $err.Trim())
    }
    return $out.Trim()
}

# ------------------------------------------------------------ Prompt-Aufbau

function Format-History {
    param($Messages)
    ($Messages | ForEach-Object { '[{0}] {1}: {2}' -f $_.id, $_.name, $_.text }) -join "`n"
}

function Build-Prompt {
    param($History, $NewMessages, [switch] $Intro, [switch] $Remind)

    $sb = New-Object Text.StringBuilder
    [void]$sb.AppendLine($rolePrompt)
    [void]$sb.AppendLine()
    [void]$sb.AppendLine('=========================================================')
    [void]$sb.AppendLine(('Dein Name im Chat ist: {0}. Heute ist {1}.' -f $Model, (Get-Date -Format 'dd.MM.yyyy HH:mm')))
    [void]$sb.AppendLine('=========================================================')
    [void]$sb.AppendLine()

    if ($History.Count -gt 0) {
        [void]$sb.AppendLine('--- BISHERIGER VERLAUF (nur zum Verstehen, nicht beantworten) ---')
        [void]$sb.AppendLine((Format-History $History))
        [void]$sb.AppendLine()
    }

    if ($Intro) {
        [void]$sb.AppendLine('--- DEINE AUFGABE ---')
        [void]$sb.AppendLine('Du betrittst den Kanal gerade zum ersten Mal. Stelle dich in HOECHSTENS')
        [void]$sb.AppendLine('drei Saetzen vor: wer du bist und welche Rolle du hier uebernimmst.')
        [void]$sb.AppendLine('Beziehe dich auf den Verlauf oben, falls dort etwas steht.')
    }
    else {
        [void]$sb.AppendLine('--- NEUE NACHRICHTEN, AUF DIE DU ANTWORTEST ---')
        [void]$sb.AppendLine((Format-History $NewMessages))
        [void]$sb.AppendLine()
        [void]$sb.AppendLine('--- DEINE AUFGABE ---')
        [void]$sb.AppendLine('Antworte als naechster Beitrag in diesem Chat.')
    }

    [void]$sb.AppendLine()
    [void]$sb.AppendLine('AUSGABEFORMAT - streng einhalten:')
    [void]$sb.AppendLine('  * Gib AUSSCHLIESSLICH den Nachrichtentext aus. Kein Vorspann, keine')
    [void]$sb.AppendLine(('    Anfuehrungszeichen, kein Markdown-Codeblock, kein "{0}:" davor.' -f $Model))
    [void]$sb.AppendLine(('  * Hoechstens {0} Zeichen, Richtwert 400-900.' -f $maxChars))
    [void]$sb.AppendLine('  * Sprich mindestens einen Teilnehmer beim Namen an.')
    [void]$sb.AppendLine('  * PFLICHT: Der letzte Satz ist eine Frage an ein anderes, namentlich')
    [void]$sb.AppendLine('    genanntes Modell (Claude, Gemini, Grok, ChatGPT) oder an Dimi.')
    [void]$sb.AppendLine('  * Hast du nichts beizutragen, gib exakt das Wort PASS aus - sonst nichts.')
    [void]$sb.AppendLine('  * Gib niemals einen API-Key oder ein Token aus.')

    if ($Remind) {
        [void]$sb.AppendLine()
        [void]$sb.AppendLine('!! Dein letzter Versuch endete NICHT mit einer Frage an einen anderen')
        [void]$sb.AppendLine('   Teilnehmer. Schreibe die Nachricht neu und haenge die Frage an.')
    }
    return $sb.ToString()
}

function Test-EndsWithQuestion {
    param([string] $Text)
    if ($Text -notmatch '\?') { return $false }
    # Die Frage muss jemanden adressieren, sonst reden alle ins Leere.
    return ($Text -match '(?i)\b(Claude|Gemini|Grok|ChatGPT|Dimi)\b')
}

function Remove-Wrapping {
    param([string] $Text)
    $t = $Text.Trim()
    $t = $t -replace '(?s)^\s*```[a-zA-Z]*\s*', '' -replace '(?s)\s*```\s*$', ''
    $t = $t -replace ('(?i)^\s*{0}\s*:\s*' -f [regex]::Escape($Model)), ''
    return $t.Trim()
}

# ------------------------------------------------------------------- Schleife

Write-Log ("Runner gestartet | Modell={0} | CLI='{1}' | Intervall={2}s | Cooldown={3}s | Tageslimit={4}" -f `
    $Model, $me.engine.cmd, $baseInterval, $cooldownSec, $dailyCap)

$state    = Get-State
$interval = $baseInterval

do {
    try {
        # Tageszaehler zuruecksetzen
        $today = Get-Date -Format 'yyyy-MM-dd'
        if ($state.dayStamp -ne $today) {
            $state.dayStamp    = $today
            $state.postedToday = 0
            Write-Log "Neuer Tag - Nachrichtenzaehler zurueckgesetzt."
        }

        $msgs = Get-ArenaMessages -Since ([int]$state.lastId)

        if ($msgs.Count -gt 0) {
            $state.lastId  = ($msgs | Measure-Object -Property id -Maximum).Maximum
            $state.history = @(@($state.history) + @($msgs)) | Select-Object -Last $historyCount
        }

        $others = @($msgs | Where-Object { $_.name -ne $Model })
        $isIntro = ((-not $state.firstRunDone) -and $me.introOnFirstRun)

        if ($others.Count -eq 0 -and -not $isIntro) {
            Write-Log ("Nichts Neues (lastId={0})." -f $state.lastId)
        }
        else {
            $humanSpoke = @($others | Where-Object { $humanNames -contains $_.name }).Count -gt 0

            # Backoff: reden nur noch KIs, wird der Takt langsamer statt lauter.
            if ($humanSpoke) { $state.aiOnlyRounds = 0; $interval = $baseInterval }
            else             { $state.aiOnlyRounds = [int]$state.aiOnlyRounds + 1 }

            if ([int]$state.aiOnlyRounds -gt [int]$d.idleBackoff.afterAiOnlyRounds) {
                $interval = [Math]::Min([int]$d.idleBackoff.maxIntervalSeconds, $interval * 2)
                Write-Log ("Nur KI-Verkehr seit {0} Runden - Takt auf {1}s gedrosselt." -f $state.aiOnlyRounds, $interval) 'WARN'
            }

            $cooling = $false
            if ($state.lastPostUtc) {
                $since = ([datetime]::UtcNow - [datetime]::Parse($state.lastPostUtc)).TotalSeconds
                $cooling = $since -lt $cooldownSec
            }

            if ([int]$state.postedToday -ge $dailyCap) {
                Write-Log ("Tageslimit {0} erreicht - heute wird nichts mehr gepostet." -f $dailyCap) 'WARN'
            }
            elseif ($cooling) {
                Write-Log "Cooldown laeuft noch - diese Runde ausgesetzt."
            }
            else {
                $ctx   = @($state.history | Select-Object -Last $historyCount)
                $reply = Remove-Wrapping (Invoke-Engine (Build-Prompt -History $ctx -NewMessages $others -Intro:$isIntro))

                if ([string]::IsNullOrWhiteSpace($reply) -or $reply -eq 'PASS') {
                    Write-Log "Modell sagt PASS - keine Nachricht."
                }
                else {
                    if (-not (Test-EndsWithQuestion $reply) -and -not $isIntro) {
                        Write-Log "Antwort ohne adressierte Frage - ein Nachfassversuch." 'WARN'
                        $reply = Remove-Wrapping (Invoke-Engine (Build-Prompt -History $ctx -NewMessages $others -Remind))
                    }
                    if ([string]::IsNullOrWhiteSpace($reply) -or $reply -eq 'PASS') {
                        Write-Log "Nachfassversuch ergab PASS - keine Nachricht."
                    }
                    elseif (-not (Test-EndsWithQuestion $reply)) {
                        Write-Log "Auch der zweite Versuch stellt keine Frage - verworfen." 'WARN'
                    }
                    else {
                        Send-ArenaMessage $reply
                        $state.postedToday = [int]$state.postedToday + 1
                        $state.lastPostUtc = ([datetime]::UtcNow).ToString('o')
                        Write-Log ("Gepostet ({0}/{1} heute): {2}" -f $state.postedToday, $dailyCap, ($reply -replace '\s+', ' '))
                    }
                }
            }
            $state.firstRunDone = $true
        }

        Save-State $state
    }
    catch {
        Write-Log $_.Exception.Message 'ERROR'
        # Bei Fehlern langsamer weitermachen statt sterben.
        Start-Sleep -Seconds ([Math]::Min(300, $interval * 2))
    }

    if (-not $Once) { Start-Sleep -Seconds $interval }
}
while (-not $Once)

Write-Log "Runner beendet."
