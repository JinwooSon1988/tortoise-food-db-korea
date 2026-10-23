# Offline evidence pipeline. Never deploys or merges main.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = "python"
# Collect a small checkpointed batch of NEW bibliography leads each cycle.
& $python scripts/discover_incremental_literature.py --queries 2 --pages 1
if ($LASTEXITCODE -ne 0) { throw "Incremental discovery failed" }
& $python scripts/match_bibliography_taxa_offline.py
if ($LASTEXITCODE -ne 0) { throw "Bibliography matching failed" }
& $python scripts/triage_bibliography_evidence_offline.py
if ($LASTEXITCODE -ne 0) { throw "Evidence triage failed" }
$approved = "worker-output/approved-feeding-records.json"
if (Test-Path $approved) {
    & $python scripts/promote_reviewed_feeding_evidence.py
    if ($LASTEXITCODE -ne 0) { throw "Evidence promotion rejected input; see promotion-report.json" }
} else {
    Write-Host "No reviewer-approved input. Candidates remain unverified and unpublished."
}
Write-Host "Offline evidence pipeline complete. Changes remain local pending review/PR."
