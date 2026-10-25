param([string]$RepoPath = "D:\GEOBUKBAP-WORKER")
$ErrorActionPreference = "Stop"
Write-Host "Geobukbap worker diagnostic (read-only)"
Write-Host "Requested repository: $RepoPath"
if (!(Test-Path $RepoPath)) {
  Write-Host "NOT FOUND: $RepoPath"
  Write-Host "Find repository: Get-ChildItem D:\ -Directory -ErrorAction SilentlyContinue | Select-Object FullName"
  exit 2
}
Set-Location $RepoPath
if (!(Test-Path "scripts/run_offline_evidence_pipeline.ps1")) { throw "Pipeline script not found; wrong repository directory" }
Write-Host "Python:"; & python --version
Write-Host "Git:"; & git status --short --branch
Write-Host "Relevant processes:"
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|powershell|pwsh' -and $_.CommandLine -match 'evidence|worker|discovery|geobukbap' } | Select-Object ProcessId,Name,CommandLine | Format-List
$lock = "worker-output/pipeline.lock"
if (Test-Path $lock) {
  $item = Get-Item $lock
  Write-Host ("Lock exists; age (minutes): " + [math]::Round(((Get-Date)-$item.LastWriteTime).TotalMinutes,1))
  Get-Content $lock
} else { Write-Host "No pipeline lock." }
$logs = "worker-output/logs"
if (Test-Path $logs) {
  Get-ChildItem $logs -File | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length | Format-Table
} else { Write-Host "No worker logs directory." }
Write-Host "Diagnostic complete. No files changed."
