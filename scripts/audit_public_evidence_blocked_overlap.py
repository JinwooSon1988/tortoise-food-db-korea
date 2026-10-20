#!/usr/bin/env python3
"""Read-only bulk audit: held original-source evidence exposed in public records.

Exit 0 for a completed audit even if overlaps are found; use --strict to fail.
Does not modify data or infer feeding safety.
"""
import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root):
    data = root / "data"
    manifest = load(data / "feeding_p1_blocked_claim_manifest_20261018.json")
    public = load(data / "public_evidence_records.json")
    reverse = load(data / "reviewed_plant_reverse_evidence_index.json")
    blocked = {}
    for claim in manifest["blocked_claims"]:
        if claim.get("status") != "hold":
            continue
        for evidence_id in claim.get("evidence_ids", []):
            blocked.setdefault(evidence_id, []).append({
                "plant_id": claim.get("plant_id"),
                "reason": claim.get("reason"),
            })
    public_by_id = {record["id"]: record for record in public["records"]}
    reverse_joins = {}
    for plant in reverse["records"]:
        for source in plant.get("public_sources", []):
            reverse_joins.setdefault(source["id"], []).append(plant["plant_id"])
    findings = []
    for evidence_id in sorted(blocked):
        record = public_by_id.get(evidence_id)
        if record is None:
            continue
        findings.append({
            "evidence_id": evidence_id,
            "public_directness": record.get("directness"),
            "public_plant_ids": record.get("plant_ids", []),
            "reverse_plant_ids": sorted(set(reverse_joins.get(evidence_id, []))),
            "held_claims": blocked[evidence_id],
            "classification": "review_required_not_automatic_error",
        })
    return {
        "blocked_claim_rows": len(manifest["blocked_claims"]),
        "unique_held_evidence_ids": len(blocked),
        "public_records_checked": len(public["records"]),
        "reverse_plants_checked": len(reverse["records"]),
        "overlap_count": len(findings),
        "findings": findings,
        "note": "Held-source overlap does not prove a claim false or establish captive feeding safety.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true", help="Return exit 1 if any overlaps exist")
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.strict and result["overlap_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
