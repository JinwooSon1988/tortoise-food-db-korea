#!/usr/bin/env python3
"""Read-only catalog batch triage, including auto-extracted vs reviewer-approved separation."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "catalog-evidence"
def main():
    for path in sorted(ROOT.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or "records" not in doc:
            continue
        records = doc["records"]
        statuses = Counter(r.get("verification", "missing") for r in records)
        missing = Counter()
        for r in records:
            for field in ("source_key", "reported_name", "tortoise", "type", "verification", "locator"):
                if not r.get(field):
                    missing[field] += 1
        print(json.dumps({
            "file": path.name,
            "records": len(records),
            "verification": dict(statuses),
            "missing_required_fields": dict(missing),
            "held_not_linked": len(doc.get("held_not_linked", [])),
            "warning": "Machine extraction is not human review; feeding evidence is not a safety verdict."
        }, ensure_ascii=False))
if __name__ == "__main__":
    main()
