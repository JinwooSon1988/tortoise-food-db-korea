#!/usr/bin/env python3
"""A legacy alias ID shows the same nutrition state and the same sources as its canonical ID (Korean and English).

data/plant_identity_registry_v1.json canonical_aliases declares IDs that are the same plant (waterdropwort -> minari).
Nutrition records live on the canonical ID only; the legacy ID reports them through the alias. For every alias pair
and both languages this check fails when:
- the legacy ID owns nutrition records of its own (they must stay on the canonical ID);
- the nutrition section of the legacy page differs from the canonical page;
- the shown state does not follow the canonical ID's data: verified record -> value grid, reference-only records ->
  "related references" block listing every reference source URL and nothing else, neither -> "no linked data".
The three nutrition states themselves are not redefined here (scripts/qa_nutrition_three_states_v1.py).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))
SECTION = re.compile(r'<section class="card" id="nutrition">.*?</section>', re.S)
MARK = {"ko": {"verified": '<div class="nutgrid">', "reference": "관련 영양 참고자료 있음", "none": "연결된 영양자료 없음"},
        "en": {"verified": '<div class="nutgrid">', "reference": "Related nutrition references available", "none": "No linked nutrition data"}}


def main():
    errors = []
    aliases = {a["legacy_id"]: a["canonical_id"] for a in load("data/plant_identity_registry_v1.json")["canonical_aliases"]}
    verified = {r["plant_id"] for r in load("data/plant_nutrition_v56.json")["plants"] if r.get("verification_status") == "verified"}
    nutrition_owners = {r["plant_id"] for r in load("data/plant_nutrition_v56.json")["plants"]}
    refs = {}
    for r in load("data/plant_nutrition_reference_v1.json")["records"]:
        nutrition_owners.add(r["plant_id"])
        if r.get("status") == "reference_only" and r.get("feeding_verdict_use") is False:
            refs.setdefault(r["plant_id"], []).append(r)
    checked = 0
    for legacy, canonical in aliases.items():
        if legacy in nutrition_owners:
            errors.append(f"{legacy}: legacy alias owns nutrition records; they belong on {canonical}")
        expected = "verified" if canonical in verified else "reference" if refs.get(canonical) else "none"
        urls = sorted(r["source_url"] for r in refs.get(canonical, []) if (r.get("source_url") or "").startswith("https://"))
        for lang, prefix in (("ko", ""), ("en", "en/")):
            pages = {}
            for pid in (legacy, canonical):
                path = ROOT / prefix / "plant" / pid / "index.html"
                m = SECTION.search(path.read_text(encoding="utf-8")) if path.exists() else None
                if not m:
                    errors.append(f"{lang}/{pid}: nutrition section missing")
                pages[pid] = m.group(0) if m else ""
            checked += 1
            if pages[legacy] != pages[canonical]:
                errors.append(f"{lang}: nutrition section of {legacy} differs from canonical {canonical}")
            for pid, sec in pages.items():
                shown = [k for k, mark in MARK[lang].items() if mark in sec]
                if shown != [expected]:
                    errors.append(f"{lang}/{pid}: nutrition state shown {shown}, expected {expected} from {canonical}'s data")
                if expected == "reference":
                    found = sorted(set(re.findall(r'<a href="(https://[^"]+)"', sec)))
                    if found != sorted(set(urls)):
                        errors.append(f"{lang}/{pid}: nutrition reference sources {found} differ from {canonical}'s records {urls}")
    if errors:
        print("alias nutrition parity QA failed (%d):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"alias nutrition parity QA ok: {len(aliases)} legacy aliases, {checked} page pairs (Korean and English)")


if __name__ == "__main__":
    main()
