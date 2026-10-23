#!/usr/bin/env python3
"""Offline evidence triage; lexical indicators are leads, never safety verdicts."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

POSITIVE = re.compile(r"\b(consum(?:e[ds]?|ption)|ingest(?:ed|ion)?|eat(?:en|ing|s)?|fed|feed(?:ing)?|forag(?:e|ed|ing)|graz(?:e|ed|ing)|diet(?:ary)?|stomach contents|fecal|faecal)\b", re.I)
NEGATIVE = re.compile(r"\b(toxic(?:ity)?|poison(?:ing|ous)?|oxalate|alkaloid|fatal|mortality|avoid|contraindicat(?:ed|ion)|not consumed|refus(?:ed|al))\b", re.I)
TORTOISE = re.compile(r"\b(tortoises?|testudo|gopherus|centrochelys|stigmochelys|geochelone|astrochelys|aldabrachelys|chelonoidis|kinixys|indotestudo|manouria|pyxis|homopus|chersina|psammobates|malacochersus|agrionemys)\b", re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="worker-output/bibliography-taxon-candidates.json")
    ap.add_argument("--output", default="worker-output/evidence-triage.json")
    args = ap.parse_args()
    source = json.loads(Path(args.input).read_text(encoding="utf-8"))
    records = []
    tally = Counter()
    for item in source.get("candidates", []):
        text = item.get("context_excerpt") or ""
        feeding = sorted({m.group(0).lower() for m in POSITIVE.finditer(text)})
        risks = sorted({m.group(0).lower() for m in NEGATIVE.finditer(text)})
        tortoise = sorted({m.group(0).lower() for m in TORTOISE.finditer(text)})
        # Abstract context may mention separate taxa and events; never infer a direct feeding relation.
        priority = ("high_context_review" if feeding and tortoise else
                    "risk_context_review" if risks else
                    "medium_context_review" if feeding else "identity_only_review")
        tally[priority] += 1
        records.append({**item, "triage_priority": priority,
                        "feeding_terms": feeding, "risk_terms": risks, "tortoise_terms": tortoise,
                        "review_state": "unverified_text_cooccurrence",
                        "safe_to_feed": None, "verified_feeding_evidence": False})
    records.sort(key=lambda r: ({"high_context_review":0,"risk_context_review":1,"medium_context_review":2,"identity_only_review":3}[r["triage_priority"]],str(r.get("scientific")),str(r.get("work_id"))))
    output = {"warning":"Keyword co-occurrence cannot prove tortoise consumption or safety; human/source review required.",
              "total_candidates":len(records),"priority_counts":dict(tally),"records":records}
    out = Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"total_candidates":len(records),"priority_counts":dict(tally),"output":str(out)},ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
