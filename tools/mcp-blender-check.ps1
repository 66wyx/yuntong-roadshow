# Blender MCP 自检脚本 / Diagnostic
# 用法：在普通 PowerShell 里运行
#   powershell -ExecutionPolicy Bypass -File "C:\Users\YX\Documents\云台检测\tools\mcp-blender-check.ps1"
# 它只读取信息，不修改任何配置。

$ErrorActionPreference = 'Continue'
function H($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }
function OK($t) { Write-Host "  [OK]   $t" -ForegroundColor Green }
function NO($t) { Write-Host "  [MISS] $t" -ForegroundColor Red }
function IN($t) { Write-Host "  [INFO] $t" -ForegroundColor Gray }

# ---------- 1. uvx ----------
H "1. uvx"
$uvxCandidates = @(
  "$env:USERPROFILE\.local\bin\uvx.exe",
  "$env:USERPROFILE\.codex\uvx.exe"
)
$uvx = $null
foreach ($p in $uvxCandidates) {
  if (Test-Path -LiteralPath $p) {
    OK $p
    try { & $p --version 2>&1 | ForEach-Object { IN "version: $_" } } catch { NO "cannot run: $_" }
    if (-not $uvx) { $uvx = $p }
  } else {
    IN "not found: $p"
  }
}
if (-not $uvx) {
  $cmd = Get-Command uvx -ErrorAction SilentlyContinue
  if ($cmd) { $uvx = $cmd.Source; OK "found on PATH: $uvx" } else { NO "uvx not found anywhere" }
}

# ---------- 2. Blender ----------
H "2. Blender"
$blenderHits = @()
@(
  "$env:ProgramFiles\Blender Foundation",
  "${env:ProgramFiles(x86)}\Blender Foundation",
  "$env:LOCALAPPDATA\Programs\Blender Foundation",
  "$env:USERPROFILE\scoop\apps\blender"
) | ForEach-Object {
  if (Test-Path -LiteralPath $_) {
    Get-ChildItem -LiteralPath $_ -Recurse -Filter blender.exe -Depth 3 -ErrorAction SilentlyContinue |
      ForEach-Object { $blenderHits += $_.FullName }
  }
}
$steam = "C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
if (Test-Path -LiteralPath $steam) { $blenderHits += $steam }

if ($blenderHits.Count -eq 0) {
  NO "blender.exe not found in usual locations"
} else {
  $blenderHits | Select-Object -Unique | ForEach-Object {
    OK $_
    try {
      $v = (Get-Item -LiteralPath $_).VersionInfo.FileVersion
      IN "file version: $v"
    } catch {}
  }
}

# running process
$proc = Get-Process blender -ErrorAction SilentlyContinue
if ($proc) { OK "Blender is running (PID $($proc.Id -join ', '))" } else { IN "Blender is not running" }

# ---------- 3. MCP port ----------
H "3. MCP port 9876"
$conn = Get-NetTCPConnection -LocalPort 9876 -ErrorAction SilentlyContinue
if ($conn) {
  $conn | ForEach-Object { OK "listening: $($_.LocalAddress):$($_.LocalPort) state=$($_.State) pid=$($_.OwningProcess)" }
} else {
  NO "nothing listening on 9876 (server not started, or Blender addon panel not started)"
}

# ---------- 4. config files ----------
H "4. MCP config files"
$cfgCandidates = @(
  "$env:APPDATA\Claude\claude_desktop_config.json",
  "$env:LOCALAPPDATA\Claude-3p\claude_desktop_config.json",
  "$env:APPDATA\Claude-3p\claude_desktop_config.json",
  "$env:USERPROFILE\.claude.json",
  "$env:USERPROFILE\.codex\config.toml",
  "C:\Users\YX\Documents\云台检测\.mcp.json"
)
foreach ($c in $cfgCandidates) {
  if (Test-Path -LiteralPath $c) {
    OK $c
    $sz = (Get-Item -LiteralPath $c).Length
    IN "size: $sz bytes"
    try {
      $raw = Get-Content -LiteralPath $c -Raw -ErrorAction Stop
      if ($raw -match 'blender') {
        IN "contains the word 'blender'"
        # print the blender-related lines only, values masked
        ($raw -split "`n") | Where-Object { $_ -match 'blender|BLENDER_|uvx|command|args' } |
          Select-Object -First 20 | ForEach-Object { IN ($_ -replace '\s+$','') }
      } else {
        IN "no 'blender' entry"
      }
    } catch { NO "cannot read: $_" }
  } else {
    IN "absent: $c"
  }
}

# ---------- 5. installed addon ----------
H "5. Blender addon on disk"
$addonRoots = @(
  "$env:APPDATA\Blender Foundation\Blender"
)
foreach ($r in $addonRoots) {
  if (Test-Path -LiteralPath $r) {
    Get-ChildItem -LiteralPath $r -Directory -ErrorAction SilentlyContinue | ForEach-Object {
      $ver = $_.Name
      $addons = Join-Path $_.FullName "scripts\addons"
      if (Test-Path -LiteralPath $addons) {
        $hit = Get-ChildItem -LiteralPath $addons -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -match 'mcp|blender_mcp' }
        if ($hit) {
          foreach ($h in $hit) { OK "$ver : $($h.Name)" }
        } else {
          IN "$ver : no mcp addon"
        }
      }
    }
  }
}

Write-Host ""
Write-Host "自检结束。把整段输出贴回来。" -ForegroundColor Yellow
