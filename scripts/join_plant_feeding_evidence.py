#!/usr/bin/env python3
"""Join source-grounded feeding observations to plant taxa without promoting genus matches.
Output is evidence metadata only, never an A-D safety verdict.
"""
import json, re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))
def key(s):
    return re.sub(r"\s+"," ",str(s or "").strip()).casefold()
def binomial(s):
    match=re.match(r"^([A-Z][a-z-]+\s+[a-z][a-z-]+)\b",str(s or ""))
    return key(match.group(1)) if match else ""
def main():
    plants=load("data/plants.json")
    wild=load("data/wild_feeding_evidence.json").get("records",[])
    evidence=load("data/public_evidence_records.json").get("records",[])
    by_id={p["id"]:p for p in plants}
    by_species=defaultdict(list)
    for p in plants:
        b=binomial(p.get("scientific"))
        if b:by_species[b].append(p["id"])
    result=defaultdict(list); quarantined=[]
    for w in wild:
        taxon=w.get("plant_taxon_reported") or w.get("plant_taxon_accepted")
        b=binomial(taxon)
        exact=by_species.get(b,[]) if b else []
        pid=w.get("plant_id")
        # A genus-only mention cannot be promoted to a species record.
        if not b or (pid and pid in by_id and pid not in exact):
            quarantined.append({"id":w.get("id"),"reason":"taxon identity mismatch or unresolved","reported":taxon,"plant_id":pid})
            continue
        if len(exact)!=1 or not w.get("source_id") or not w.get("tortoise_taxon"):
            quarantined.append({"id":w.get("id"),"reason":"ambiguous match or incomplete source","reported":taxon})
            continue
        result[exact[0]].append({"evidence_id":w.get("id"),"type":"wild_feeding","tortoise_taxon":w["tortoise_taxon"],"plant_taxon_reported":taxon,"plant_part":w.get("plant_part") or "unspecified","method":w.get("study_method") or "unspecified","source_id":w["source_id"],"review_state":"source_record_requires_original_crosscheck","feeding_safety":"not_established"})
    # Existing public evidence is linked only by explicit plant_ids, with applicability retained.
    for e in evidence:
        ids=e.get("plant_ids") or []
        if not isinstance(ids,list):continue
        for pid in ids:
            if pid not in by_id:continue
            result[pid].append({"evidence_id":e.get("id"),"type":e.get("source_type") or "source","tortoise_taxon":e.get("animal_taxon") or "unspecified","plant_taxon_reported":e.get("plant_taxon") or "unspecified","plant_part":e.get("plant_part_state") or "unspecified","source_id":e.get("doi") or e.get("url") or "","directness":e.get("directness") or "unspecified","applicability":e.get("applicability") or "unspecified","review_state":"existing_public_evidence","feeding_safety":"not_inferred"})
    output={"schema_version":"1.0","purpose":"source-to-plant join, not a safety verdict","records":[{"plant_id":pid,"scientific_name":by_id[pid].get("scientific"),"evidence":entries} for pid,entries in sorted(result.items())],"quarantined_wild_records":quarantined}
    dest=ROOT/"data/plant_feeding_evidence_links.json"
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("plants with linked evidence:",len(result),"quarantined wild:",len(quarantined))
if __name__=="__main__":main()
