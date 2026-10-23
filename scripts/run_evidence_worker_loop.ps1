param(
  [int]$IntervalMinutes = 30,
  [switch]$Once
)
$ErrorActionPreference = "Stop"
$repo = "D:\\GEOBUKBAP-WORKER"
$logDir = Join-Path $repo "worker-output\\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$lock = Join-Path $repo "worker-output\\pipeline.lock"
while ($true) {
  $now = Get-Date
  $log = Join-Path $logDir ("pipeline-" + $now.ToString("yyyyMMdd-HHmmss") + ".log")
  if (Test-Path $lock) {
    $age = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalHours
    if ($age -lt 2) {
      Write-Host "Another pipeline run is active; skipping this cycle."
      if ($Once) { break }
      Start-Sleep -Seconds ([Math]::Max(60,$IntervalMinutes*60))
      continue
    }
    Remove-Item $lock -Force
  }
  try {
    Set-Content -Path $lock -Value "$PID $($now.ToString('o'))"
    Push-Location $repo
    try {
      & powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_offline_evidence_pipeline.ps1 *>&1 |
        Tee-Object -FilePath $log
      if ($LASTEXITCODE -ne 0) { Write-Warning "Pipeline exit code: $LASTEXITCODE" }
    } finally { Pop-Location }
  } catch {
    Write-Warning $_
    $_ | Out-File -Append -FilePath $log
  } finally {
    Remove-Item $lock -Force -ErrorAction SilentlyContinue
  }
  if ($Once) { break }
  Start-Sleep -Seconds ([Math]::Max(60,$IntervalMinutes*60))
}
