#!/usr/bin/env python3
"""Rank evidence review queues by source provenance, never assign feeding verdicts."""
import json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
assessments = json.loads((ROOT / "data/public_assessments.json").read_text(encoding="utf-8"))
evidence = {e["id"]: e for e in json.loads((ROOT / "data/public_evidence_records.json").read_text(encoding="utf-8"))["records"]}
rows = []
for a in assessments:
    sources = [evidence[i] for i in a.get("evidence_ids", []) if i in evidence]
    ttt = [s for s in sources if "thetortoisetable.org.uk" in (s.get("url") or "").lower()]
    others = [s for s in sources if s not in ttt]
    source_types = sorted({s.get("source_type", "unknown") for s in others})
    # These are provenance labels, NOT an assertion that original papers have been verified.
    academic_types = {"academic_study", "peer_reviewed", "peer_reviewed_plant_composition"}
    veterinary_types = {"veterinary_guidance", "veterinary_manual_peer_reviewed", "veterinary_manual_table", "specialist_veterinary_review"}
    has_academic = any(s.get("source_type") in academic_types for s in others)
    has_vet = any(s.get("source_type") in veterinary_types for s in others)
    if ttt and not others:
        priority = "P0_TTT_ONLY"
    elif ttt and not (has_academic or has_vet):
        priority = "P1_TTT_PLUS_NONACADEMIC"
    elif ttt:
        priority = "P2_TTT_PLUS_RESEARCH_OR_VET_LABEL"
    elif not sources:
        priority = "P0_NO_EVIDENCE"
    else:
        priority = "P3_OTHER_SOURCES"
    rows.append({"plant_id": a["plant_id"], "scientific": plants.get(a["plant_id"], {}).get("scientific"),
                 "animal_taxon": a.get("animal_taxon"), "current_verdict": a.get("verdict"),
                 "priority": priority, "ttt_count": len(ttt),
                 "non_ttt_count": len(others), "non_ttt_source_types": source_types,
                 "non_ttt_urls": [s.get("url") for s in others],
                 "verification_status": "original_source_not_checked_by_this_audit"})
order = {"P0_NO_EVIDENCE":0, "P0_TTT_ONLY":1, "P1_TTT_PLUS_NONACADEMIC":2,
         "P2_TTT_PLUS_RESEARCH_OR_VET_LABEL":3, "P3_OTHER_SOURCES":4}
rows.sort(key=lambda r:(order[r["priority"]],r["plant_id"]))
out = ROOT / "research/generated/ttt_independent_evidence_review_queue.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"summary":dict(Counter(r["priority"] for r in rows)),
    "warning":"Source-type classification is a review priority, not a scientific validity verdict.",
    "rows":rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(Counter(r["priority"] for r in rows)),ensure_ascii=False))
