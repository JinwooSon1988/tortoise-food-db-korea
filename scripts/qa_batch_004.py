#!/usr/bin/env python3
"""QA for the batch 004 automatic extraction (data/catalog-evidence/batch-004-*.json).

Every record: a source with citation, http(s) URL and study id; verification full_text_auto_extracted (never counted
as checked in the original); a typed feeding record (no nutrition/toxicity/safety claims, no grade field); bilingual
finding; a binomial name; a quote (<= 25 words, containing the printed name) in
research/evidence-queue/batch-004/records_with_quotes.jsonl.gz. No keeper or community source. No duplicate plant x
tortoise x source x type. Held records carry a reason. In the catalog, entries whose only records are batch 004 show
the research status evidence_auto_extracted.
"""
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
files = sorted((ROOT / "data/catalog-evidence").glob("batch-004-*.json"))
if len(files) != 1:
    print(f"FAIL batch 004: expected one batch-004 file, found {len(files)}"); sys.exit(1)
b = json.loads(files[0].read_text(encoding="utf-8"))
src = {s["source_key"]: s for s in b["sources"]}
qpath = ROOT / "research/evidence-queue/batch-004/records_with_quotes.jsonl.gz"
quotes = {}
with gzip.open(qpath, "rt", encoding="utf-8") as f:
    for line in f:
        q = json.loads(line)
        quotes[(q["source_key"], q["reported_name"], q["tortoise"], q["type"])] = q
seen = Counter()
for r in b["records"]:
    s = src.get(r["source_key"])
    tag = f"{r['reported_name']} / {r['source_key']}"
    if not s or not s.get("citation") or not str(s.get("url") or "").startswith("http") or not s.get("study_id"):
        errors.append(f"{tag}: source lacks citation, URL or study id")
    elif s.get("source_class") in ("keeper_community",):
        errors.append(f"{tag}: keeper/community source in the automatic batch")
    if r["verification"] != "full_text_auto_extracted":
        errors.append(f"{tag}: verification {r['verification']}")
    if r["type"] not in ("wild_feeding_observation", "captive_feeding_record"):
        errors.append(f"{tag}: type {r['type']} is not a feeding record")
    if any(k in r for k in ("grade", "safety_grade", "verdict", "nutrition", "toxicity")):
        errors.append(f"{tag}: carries a grade, verdict, nutrition or toxicity field")
    if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+", r["reported_name"]):
        errors.append(f"{tag}: not a binomial")
    if not (r.get("finding") or {}).get("ko") or not (r.get("finding") or {}).get("en"):
        errors.append(f"{tag}: finding not in Korean and English")
    if r.get("plant_part") and not (r["plant_part"].get("ko") and r["plant_part"].get("en")):
        errors.append(f"{tag}: plant part not bilingual")
    key = (r["source_key"], r["reported_name"], r["tortoise"], r["type"])
    seen[key] += 1
    q = quotes.get(key)
    if not q:
        errors.append(f"{tag}: no stored quote")
    elif len(q["quote"].split()) > 25 or q["printed"].casefold() not in " ".join(q["quote"].split()).casefold():
        errors.append(f"{tag}: quote longer than 25 words or without the printed name")
errors += [f"duplicate record {k}" for k, n in seen.items() if n > 1]
errors += [f"held record without a reason: {h}" for h in b["held_not_linked"] if not h.get("reason")]

auto_only = 0
for f in sorted((ROOT / "data/plant-catalog").glob("taxa-*.json")):
    for r in json.loads(f.read_text(encoding="utf-8"))["records"]:
        levels = {e["verification"] for e in r["feeding_evidence"]}
        if levels == {"full_text_auto_extracted"}:
            auto_only += 1
            if r["research"]["status"] != "evidence_auto_extracted":
                errors.append(f"{r['id']}: only automatic records but status {r['research']['status']}")
if errors:
    print("FAIL batch 004:")
    for e in errors[:40]:
        print(" -", e)
    sys.exit(1)
print(f"PASS batch 004: {len(b['records'])} records from {len(src)} sources, {len(b['held_not_linked'])} held; "
      f"{auto_only} catalog entries supported only by automatic extraction (status evidence_auto_extracted)")
