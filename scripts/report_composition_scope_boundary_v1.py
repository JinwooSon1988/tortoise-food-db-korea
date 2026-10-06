#!/usr/bin/env python3
"""Diagnostic: mixed composition-only + animal-feeding evidence needs an explicit boundary.

A composition/identity source can establish what a plant is or what it contains,
but cannot by itself establish tortoise feeding safety or dosage. This report
flags assessments that combine such records without an obvious reader-facing
boundary phrase. It is diagnostic only and never changes verdicts.
"""
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):
    raw=json.loads((ROOT/p).read_text(encoding="utf-8"))
    return raw.get("records",raw) if isinstance(raw,dict) else raw
A=load("data/public_assessments.json")
E=load("data/public_evidence_records.json")
EM={x.get("id"):x for x in E}
boundary=re.compile(r"(성분|조성|영양|화학|동정|분류|급여.*(?:근거|시험|자료).*(?:아니|않)|(?:직접|정확한).*(?:급여량|급여비율|빈도).*(?:아니|않))",re.I)
for a in A:
    linked=[EM[i] for i in a.get("evidence_ids",[]) if i in EM]
    comp=[x for x in linked if x.get("applicability")=="composition_only"]
    animal=[x for x in linked if x.get("applicability")!="composition_only"]
    text=" ".join(str(a.get(k) or "") for k in ("why","applicability_note","limits"))
    if comp and animal and not boundary.search(text):
        print(json.dumps({"plant_id":a.get("plant_id"),"confidence":a.get("confidence"),"verdict":a.get("verdict"),"composition_ids":[x.get("id") for x in comp],"animal_ids":[x.get("id") for x in animal]},ensure_ascii=False))
