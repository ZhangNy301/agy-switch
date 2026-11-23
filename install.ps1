# agy-switch installer for Windows — usage (PowerShell):
#   irm https://raw.githubusercontent.com/ZhangNy301/agy-switch/main/install.ps1 | iex
# or, from a cloned repo:  .\install.ps1
$ErrorActionPreference = 'Stop'

$RepoRaw = if ($env:AGY_SWITCH_REPO_RAW) { $env:AGY_SWITCH_REPO_RAW } else { 'https://raw.githubusercontent.com/ZhangNy301/agy-switch/main' }
$Root = Join-Path $env:LOCALAPPDATA 'agy-switch'
$BinDir = Join-Path $Root 'bin'
$Script = Join-Path $Root 'agy-switch.py'

Write-Host 'agy-switch installer'

# --- requirement: python >= 3.7 -------------------------------------------
# The `py` launcher is preferred: the launchers below keep working after a
# Python upgrade, where a stored python.exe path would go stale.
$PyCommand = $null
$Python = $null
foreach ($cand in @(@('py', '-3'), @('python'), @('python3'))) {
    $exe = $cand[0]
    $pre = @($cand | Select-Object -Skip 1)
    $cmd = Get-Command $exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cmd) { continue }
    try {
        # no quotes inside: Windows PowerShell 5.1 mangles them in native arguments
        $out = & $cmd.Source @pre -c 'import sys; print(sys.executable * (sys.version_info[:2] >= (3, 7)))' 2>$null
    } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $out -and (Test-Path $out)) {
        $Python = "$out".Trim()
        $PyCommand = if ($exe -eq 'py') { @($cmd.Source) + $pre } else { @($Python) }
        break
    }
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

# .cmd files are read in the console code page, which can't hold every
# character (e.g. C:\Users\José): use the 8.3 short path for such paths.
function Get-CmdSafePath([string]$Path) {
    if ($Path -match '^[\x20-\x7e]*$') { return $Path }
    try {
        $fso = New-Object -ComObject Scripting.FileSystemObject
        $short = if (Test-Path -PathType Container $Path) { $fso.GetFolder($Path).ShortPath } else { $fso.GetFile($Path).ShortPath }
        if ($short -match '^[\x20-\x7e]*$') { return $short }
    } catch {}
    return $Path
}

$PyExe = '"' + (Get-CmdSafePath $PyCommand[0]) + '"'
$PyArgs = ($PyCommand | Select-Object -Skip 1) -join ' '
$Cmd = "@echo off`r`n$PyExe $PyArgs `"$(Get-CmdSafePath $Script)`" %*`r`nexit /b %ERRORLEVEL%`r`n"
foreach ($name in 'agy-switch', 'asw') {
    [IO.File]::WriteAllText((Join-Path $BinDir "$name.cmd"), $Cmd, [Text.Encoding]::ASCII)
}
Write-Host "  installed: $BinDir\agy-switch.cmd (+ asw alias)"

# --- PATH -------------------------------------------------------------------
# Read and write the registry value directly: [Environment]::Get/SetEnvironmentVariable
# expand %VARS% on read and save a plain string, flattening entries like
# %USERPROFILE%\... for good.
$EnvKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
$Raw = [string]$EnvKey.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
$Kind = if ($EnvKey.GetValueNames() -contains 'Path') { $EnvKey.GetValueKind('Path') } else { [Microsoft.Win32.RegistryValueKind]::ExpandString }
$Parts = @($Raw -split ';' | Where-Object { $_ })
if ($Parts -notcontains $BinDir) {
    $EnvKey.SetValue('Path', (@($Parts) + $BinDir) -join ';', $Kind)
    # tell Explorer and new terminals that the environment changed
    if (-not ('AgySwitch.EnvNotify' -as [type])) {
        Add-Type -Namespace AgySwitch -Name EnvNotify -MemberDefinition @'
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
'@
    }
    $result = [UIntPtr]::Zero
    [void][AgySwitch.EnvNotify]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$result)
    $env:Path = "$env:Path;$BinDir"
    Write-Host "  added $BinDir to your user PATH (open a new terminal to pick it up)"
}
$EnvKey.Close()

Write-Host ''
Write-Host 'done. next steps:'
Write-Host '  agy-switch login    # add your first account'
Write-Host '  asw                 # interactive switcher'
