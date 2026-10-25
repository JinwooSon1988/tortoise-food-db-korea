#!/usr/bin/env python3
"""Read-only, species-level semantic evidence audit. Does not alter catalog or verdicts."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "plant-catalog"
POSITIVE = {"wild_feeding_observation", "captive_feeding_record", "video_observation", "community_report"}
NEGATIVE = {"wild_diet_not_detected", "offered_not_eaten"}
CONTEXT = {"husbandry_recommendation", "toxicity", "nutrition"}
SOURCE_CHECKED = {"full_text_verified", "review_full_text_verified", "guideline_full_text_verified"}

def classify(records):
    kinds = {str(e.get("type", "")) for e in records}
    positive = any(t in POSITIVE for t in kinds)
    verified_positive = any(e.get("type") in POSITIVE and e.get("verification") in SOURCE_CHECKED for e in records)
    return {
        "any_record": bool(records),
        "positive_record": positive,
        "verified_positive_record": verified_positive,
        "negative_only": bool(records) and kinds.issubset(NEGATIVE),
        "context_or_negative_only": bool(records) and not positive,
        "unknown_types": sorted(kinds - POSITIVE - NEGATIVE - CONTEXT),
    }

def main():
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    counts = Counter()
    unknown = Counter()
    samples = []
    seen = set()
    for shard in index["shards"]:
        data = json.loads((ROOT / shard["file"]).read_text(encoding="utf-8"))
        for plant in data["records"]:
            pid = plant["id"]
            if pid in seen:
                raise ValueError("Duplicate catalog plant ID: " + pid)
            seen.add(pid)
            status = classify(plant.get("feeding_evidence") or [])
            for field in ("any_record", "positive_record", "verified_positive_record", "negative_only", "context_or_negative_only"):
                counts[field] += int(status[field])
            for t in status["unknown_types"]:
                unknown[t] += 1
            if status["negative_only"] and len(samples) < 20:
                samples.append({"id": pid, "scientific": plant.get("scientific")})
    counts["total_species"] = len(seen)
    counts["no_record"] = counts["total_species"] - counts["any_record"]
    if counts["total_species"] != index["count"]:
        raise ValueError("Catalog index count mismatch")
    if counts["any_record"] != index["counts"]["with_feeding_evidence"]:
        raise ValueError("Linked-record count mismatch")
    target = (counts["total_species"] * 9 + 9) // 10
    report = {
        "definitions": {
            "any_record": "Any linked record, including non-detection and reference material",
            "positive_record": "At least one reported feeding/consumption observation; not proof of safety",
            "verified_positive_record": "Positive observation with a source-checked verification status",
            "context_or_negative_only": "No positive feeding observation",
        },
        "counts": dict(sorted(counts.items())),
        "target_90_percent": target,
        "remaining_verified_positive_to_target": max(0, target - counts["verified_positive_record"]),
        "unknown_evidence_types": dict(sorted(unknown.items())),
        "negative_only_examples": samples,
        "warning": "These categories are reporting-only. They do not change public safety grades or approve machine-extracted leads.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
