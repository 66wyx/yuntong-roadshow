# Blender MCP 配置写入脚本 / Register MCP server
#
# 先跑 mcp-blender-check.ps1 确认 uvx 真实路径和配置文件真实位置，再跑本脚本：
#   powershell -ExecutionPolicy Bypass -File "...\mcp-blender-setup.ps1" `
#       -Config "C:\Users\YX\AppData\Roaming\Claude\claude_desktop_config.json"
#
# 加 -Force 跳过覆盖确认（无人值守时用）。
# 行为：备份 -> 读出全部已有键 -> 只增删 mcpServers.blender -> 写回（UTF8 无 BOM）。

param(
  [Parameter(Mandatory=$true)][string]$Config,
  [string]$Uvx = "$env:USERPROFILE\.local\bin\uvx.exe",
  [string]$Package = "mcp-for-blender",
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

# ---------- 前置检查 ----------
if (-not (Test-Path -LiteralPath $Uvx)) {
  throw "uvx 不存在: $Uvx —— 先跑自检脚本确认真实路径，再用 -Uvx 参数指定"
}

$dir = Split-Path -Parent $Config
if (-not (Test-Path -LiteralPath $dir)) {
  throw "配置文件的父目录不存在: $dir"
}

$exists = Test-Path -LiteralPath $Config
if ($exists) {
  $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
  $backup = "$Config.bak-$stamp"
  Copy-Item -LiteralPath $Config -Destination $backup -Force
  Write-Host "已备份: $backup" -ForegroundColor Green
} else {
  Write-Host "配置文件不存在，将新建: $Config" -ForegroundColor Yellow
  $backup = $null
}

# ---------- 读取并解析 ----------
$json = $null
if ($exists) {
  $raw = Get-Content -LiteralPath $Config -Raw -Encoding UTF8
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    try { $json = $raw | ConvertFrom-Json }
    catch { throw "现有配置不是合法 JSON，拒绝修改。备份在 $backup" }
  }
}

# ---------- 保留所有顶层键 ----------
$top = [ordered]@{}
if ($json) {
  foreach ($p in $json.PSObject.Properties) {
    if ($p.Name -ne 'mcpServers') { $top[$p.Name] = $p.Value }
  }
}

# ---------- 保留所有已有服务器 ----------
$servers = [ordered]@{}
if ($json -and ($json.PSObject.Properties.Name -contains 'mcpServers') -and $json.mcpServers) {
  foreach ($p in $json.mcpServers.PSObject.Properties) {
    $servers[$p.Name] = $p.Value
  }
}

# ---------- 覆盖确认 ----------
if ($servers.Contains('blender') -and -not $Force) {
  Write-Host ""
  Write-Host "已存在名为 'blender' 的条目，将被替换：" -ForegroundColor Yellow
  Write-Host "  command = $($servers['blender'].command)" -ForegroundColor Yellow
  Write-Host "  args    = $($servers['blender'].args -join ' ')" -ForegroundColor Yellow
  $ans = Read-Host "继续？(y/N)"
  if ($ans -ne 'y') { Write-Host "已取消，未做任何修改。" -ForegroundColor Gray; exit 0 }
}

$servers['blender'] = [ordered]@{
  command = $Uvx
  args    = @('--python','3.11',$Package)
  env     = [ordered]@{
    BLENDER_HOST = 'localhost'
    BLENDER_PORT = '9876'
  }
}

# ---------- 重建完整文档 ----------
$doc = [ordered]@{}
foreach ($k in $top.Keys) { $doc[$k] = $top[$k] }
$doc['mcpServers'] = $servers

$text = $doc | ConvertTo-Json -Depth 30
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Config, $text, $utf8)

Write-Host ""
Write-Host "已写入: $Config" -ForegroundColor Green
Write-Host "服务器列表: $($servers.Keys -join ', ')" -ForegroundColor Gray
if ($backup) { Write-Host "回滚命令:" -ForegroundColor Gray; Write-Host "  Copy-Item -LiteralPath '$backup' -Destination '$Config' -Force" -ForegroundColor Gray }
Write-Host ""
Write-Host "下一步：完全退出客户端（含托盘），重开，检查工具列表。" -ForegroundColor Cyan
