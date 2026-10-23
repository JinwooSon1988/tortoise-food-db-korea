# Evidence discovery and local review are independent. Never deploys or merges main.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = "python"
$corpus = "worker-output/worldwide-literature.json"
$candidates = "worker-output/bibliography-taxon-candidates.json"
$triage = "worker-output/evidence-triage.json"
$approved = "worker-output/approved-feeding-records.json"

# A rate limit must not block review of already downloaded bibliography.
# The discovery script itself reads discovery-state.json/cooldown_until before making any request.
# Do not duplicate the cooldown logic here; always continue offline review.
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

# Avoid rescanning identical local documents every 30 minutes.
# New or modified source files trigger a fresh candidate scan; the approval draft is preserved otherwise.
$candidateOutput = "worker-output/evidence-candidates.json"
$draftOutput = "worker-output/approval-drafts.json"
$scanSources = @($corpus) + @(Get-ChildItem -Path "worker-output" -Filter "docs*.jsonl" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
if (Test-Path "worker-output/evidence_match.json") { $scanSources += "worker-output/evidence_match.json" }
$needCandidateScan = !(Test-Path $candidateOutput) -or !(Test-Path $draftOutput)
if (!$needCandidateScan) {
    $lastScan = (Get-Item $candidateOutput).LastWriteTimeUtc
    foreach ($source in $scanSources) {
        if ((Test-Path $source) -and (Get-Item $source).LastWriteTimeUtc -gt $lastScan) {
            $needCandidateScan = $true
            break
        }
    }
}

# Full-text and synonym-aware candidates from every saved document (no network; runs during any API cooldown).
# Writes worker-output/evidence-candidates.json and approval drafts ("reviewed": false) for a person to complete.
$docs = Get-ChildItem -Path "worker-output" -Filter "docs*.jsonl" -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }
$candArgs = @("scripts/build_evidence_candidates.py", "--bibliography", $corpus)
if ($docs) { $candArgs += @("--docs") + $docs }
if (Test-Path "worker-output/evidence_match.json") { $candArgs += @("--gbif-cache", "worker-output/evidence_match.json") }
if ($needCandidateScan) {
    & $python @candArgs
    if ($LASTEXITCODE -ne 0) { Write-Warning "Full-text candidate scan failed; bibliography triage results are still available." }
} else {
    Write-Host "Evidence candidates unchanged: preserving existing approval drafts and skipping duplicate scan."
}

if (Test-Path $approved) {
    & $python scripts/promote_reviewed_feeding_evidence.py
    if ($LASTEXITCODE -ne 0) { throw "Evidence promotion rejected input; see promotion-report.json" }
    Write-Host "Approved records are in data/catalog-evidence/reviewed-records.json. Rebuild the catalog (build_plant_catalog_v1.py) and run qa_plant_catalog_v1.py before committing."
    Write-Warning "Do not count approved records as published until the catalog shards, search index, sitemap and QA are rebuilt successfully."
} else {
    Write-Host "No reviewer-approved input. Candidates remain unverified and unpublished."
}
& $python scripts/check_evidence_coverage.py
if ($LASTEXITCODE -ne 0) { throw "Catalog coverage QA failed" }
Write-Host "Pipeline complete. Discovery and offline review are independent; no automatic deployment."
