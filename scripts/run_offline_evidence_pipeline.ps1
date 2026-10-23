# Evidence discovery and local review are independent. Never deploys or merges main.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = "python"
$corpus = "worker-output/worldwide-literature.json"
$candidates = "worker-output/bibliography-taxon-candidates.json"
$triage = "worker-output/evidence-triage.json"
$approved = "worker-output/approved-feeding-records.json"

# A rate limit must not block review of already downloaded bibliography.
& $python scripts/discover_incremental_literature.py --queries 2 --pages 1
if ($LASTEXITCODE -ne 0) { Write-Warning "Discovery failed; continuing offline review of existing corpus." }

# Recompute only when source data changed or derived files do not exist.
$needMatch = !(Test-Path $candidates)
if ((Test-Path $corpus) -and (Test-Path $candidates)) {
    $needMatch = (Get-Item $corpus).LastWriteTimeUtc -gt (Get-Item $candidates).LastWriteTimeUtc
}
if ($needMatch) {
    & $python scripts/match_bibliography_taxa_offline.py
    if ($LASTEXITCODE -ne 0) { throw "Bibliography matching failed" }
} else {
    Write-Host "Bibliography unchanged: reusing previous taxon matches."
}

$needTriage = !(Test-Path $triage)
if ((Test-Path $candidates) -and (Test-Path $triage)) {
    $needTriage = (Get-Item $candidates).LastWriteTimeUtc -gt (Get-Item $triage).LastWriteTimeUtc
}
if ($needTriage) {
    & $python scripts/triage_bibliography_evidence_offline.py
    if ($LASTEXITCODE -ne 0) { throw "Evidence triage failed" }
} else {
    Write-Host "Candidate matches unchanged: reusing previous review queue."
}

if (Test-Path $approved) {
    & $python scripts/promote_reviewed_feeding_evidence.py
    if ($LASTEXITCODE -ne 0) { throw "Evidence promotion rejected input; see promotion-report.json" }
} else {
    Write-Host "No reviewer-approved input. Candidates remain unverified and unpublished."
}
Write-Host "Pipeline complete. Discovery and offline review are independent; no automatic deployment."
