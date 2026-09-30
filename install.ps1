# 手动安装 sanyi-manhua-review（Windows PowerShell）
# 用法：powershell -ExecutionPolicy Bypass -File install.ps1 [all|claude|agents]
param([string]$Target = "all")
$Name = "sanyi-manhua-review"
$Src  = Join-Path $PSScriptRoot "skills\$Name"
function Install-To($Dir) {
  New-Item -ItemType Directory -Force -Path $Dir | Out-Null
  $Dest = Join-Path $Dir $Name
  if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
  Copy-Item -Recurse $Src $Dest
  Write-Host "✓ 已安装到 $Dest"
}
if ($Target -in @("all","claude")) { Install-To (Join-Path $HOME ".claude\skills") }
if ($Target -in @("all","agents")) { Install-To (Join-Path $HOME ".agents\skills") }
Write-Host "完成。请重启 Claude Code / Codex / Kimi Code（Kimi 可用 /reload）后生效。"
