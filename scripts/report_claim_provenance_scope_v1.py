#!/usr/bin/env python3
"""Diagnostic audit: compare reader-facing direct-feeding claims with linked evidence scope.

Flags potentially broad phrases such as 'directly observed in tortoises' when the
linked evidence is species/taxon-specific. This is diagnostic only; it never
rewrites assessments because a broad phrase can be intentionally qualified in
the surrounding sentence.
"""
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path):
    raw=json.loads((ROOT/path).read_text(encoding="utf-8"))
    return raw.get("records",raw) if isinstance(raw,dict) else raw

assessments=load("data/public_assessments.json")
evidence=load("data/public_evidence_records.json")
em={e.get("id"):e for e in evidence}

# Only flag affirmative broad claims. Explicit limitations such as
# "직접 시험이 아니다" must not be treated as positive feeding claims.
affirmative_broad_re=re.compile(
    r"(?:야생\\s+(?:육지거북|거북류)\\s+[^.]{0,80}(?:섭식|먹이|먹었다|관찰)|"
    r"(?:육지거북|거북류)에서\\s+[^.]{0,80}(?:직접\\s+(?:관찰|섭식|급여)|실제\\s+섭식)|"
    r"(?:육지거북|거북류)의\\s+[^.]{0,80}(?:직접\\s+(?:섭식|급여)|실제\\s+섭식))"
)
negated_broad_re=re.compile(
    r"(?:육지거북|거북류).{0,100}(?:직접\\s*(?:시험|자료|근거).{0,30}(?:아니|않)|"
    r"(?:직접|실제).{0,30}(?:자료|근거).{0,30}(?:아니|않))"
)
hits=[]
for a in assessments:
    text=" ".join(str(a.get(k) or "") for k in ("why","applicability_note","limits"))
    linked=[em[i] for i in a.get("evidence_ids",[]) if i in em]
    taxa=sorted({str(e.get("animal_taxon")) for e in linked if e.get("animal_taxon")})
    if affirmative_broad_re.search(text) and not negated_broad_re.search(text) and any(e.get("applicability") in {"exact_taxon","species"} for e in linked):
        hits.append({"plant_id":a.get("plant_id"),"claim":text[:900],"linked_taxa":taxa,"evidence_ids":a.get("evidence_ids",[])})

print(f"Potential provenance-scope review candidates: {len(hits)}")
for h in hits:
    print(json.dumps(h,ensure_ascii=False))
