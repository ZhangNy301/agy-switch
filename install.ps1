# agy-switch installer for Windows — usage (PowerShell):
#   irm https://raw.githubusercontent.com/elhassu/agy-switch/main/install.ps1 | iex
# or, from a cloned repo:  .\install.ps1
$ErrorActionPreference = 'Stop'

$RepoRaw = if ($env:AGY_SWITCH_REPO_RAW) { $env:AGY_SWITCH_REPO_RAW } else { 'https://raw.githubusercontent.com/elhassu/agy-switch/main' }
$Root = Join-Path $env:LOCALAPPDATA 'agy-switch'
$BinDir = Join-Path $Root 'bin'
$Script = Join-Path $Root 'agy-switch.py'

Write-Host 'agy-switch installer'

# --- requirement: python >= 3.7 -------------------------------------------
$Python = $null
foreach ($cand in @(@('py', '-3'), @('python'), @('python3'))) {
    $exe = $cand[0]
    $pre = @($cand | Select-Object -Skip 1)
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    try {
        # no quotes inside: Windows PowerShell 5.1 mangles them in native arguments
        $out = & $exe @pre -c 'import sys; print(sys.executable * (sys.version_info[:2] >= (3, 7)))' 2>$null
    } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $out -and (Test-Path $out)) { $Python = "$out".Trim(); break }
}
if (-not $Python) {
    Write-Error "Python 3.7+ is required but was not found.`n  install it with: winget install Python.Python.3.12"
}
Write-Host "  python: $Python"

New-Item -ItemType Directory -Force $BinDir | Out-Null

# --- install the script -----------------------------------------------------
$Local = if ($PSScriptRoot) { Join-Path $PSScriptRoot 'bin\agy-switch' } else { $null }
if ($Local -and (Test-Path $Local)) {
    Copy-Item $Local $Script -Force
} else {
    Invoke-WebRequest -UseBasicParsing "$RepoRaw/bin/agy-switch" -OutFile $Script
}

$Cmd = "@echo off`r`n`"$Python`" `"$Script`" %*`r`nexit /b %ERRORLEVEL%`r`n"
foreach ($name in 'agy-switch', 'asw') {
    [IO.File]::WriteAllText((Join-Path $BinDir "$name.cmd"), $Cmd, [Text.Encoding]::ASCII)
}
Write-Host "  installed: $BinDir\agy-switch.cmd (+ asw alias)"

# --- PATH -------------------------------------------------------------------
$UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$Parts = @($UserPath -split ';' | Where-Object { $_ })
if ($Parts -notcontains $BinDir) {
    [Environment]::SetEnvironmentVariable('Path', (@($Parts) + $BinDir) -join ';', 'User')
    $env:Path = "$env:Path;$BinDir"
    Write-Host "  added $BinDir to your user PATH (open a new terminal to pick it up)"
}

Write-Host ''
Write-Host 'done. next steps:'
Write-Host '  agy-switch login    # add your first account'
Write-Host '  asw                 # interactive switcher'
