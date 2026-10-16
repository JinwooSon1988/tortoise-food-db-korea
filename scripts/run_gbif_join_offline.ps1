param([string]$RunId = "38837601795")
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$dest = "research/generated/gbif_batches"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
gh run download $RunId --repo JinwooSon1988/tortoise-food-db-korea --pattern "gbif-global-taxonomy-candidates-*" --dir $dest
if ($LASTEXITCODE -ne 0) { throw "Artifact download failed" }
$files = @(Get-ChildItem $dest -Recurse -Filter gbif_global_taxa_sample.json -File | ForEach-Object FullName)
if ($files.Count -eq 0) { throw "No candidate files" }
python scripts/join_gbif_candidates_with_evidence.py --batches $files --out research/generated/gbif_candidate_evidence_join.json
if ($LASTEXITCODE -ne 0) { throw "Join failed" }
python -c "import json; p=json.load(open('research/generated/gbif_candidate_evidence_join.json',encoding='utf-8')); print(p['summary'])"
