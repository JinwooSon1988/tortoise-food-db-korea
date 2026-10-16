#!/usr/bin/env python3
"""Connect all GBIF taxonomy candidates to evidence without treating names as feeding safety.
Run: python scripts/join_global_taxonomy_evidence.py
Requires data/global_taxonomy_candidates.json and data/plant_feeding_evidence_links.json.
"""
import json,re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/name).read_text(encoding="utf-8"))
def taxon(name):
    m=re.match(r"^([A-Z][a-z-]+) ([a-z][a-z-]+)(?:\\b|$)",str(name or ""))
    return (m.group(1)+" "+m.group(2)).casefold() if m else ""
def main():
    payload=load("data/global_taxonomy_candidates.json")
    rows=payload["records"]
    if payload.get("record_count")!=len(rows):raise SystemExit("count mismatch")
    reviewed=load("data/plants.json")
    links=load("data/plant_feeding_evidence_links.json")["records"]
    plants={p["id"]:p for p in reviewed}
    known=defaultdict(list)
    for p in reviewed:
        if taxon(p.get("scientific")):known[taxon(p["scientific"])].append(p["id"])
    linked={x["plant_id"]:x["evidence"] for x in links}
    out=[];audits=[];seen=set()
    for row in rows:
        name=row["scientific_name"];k=taxon(name)
        if not k or k in seen:raise SystemExit("duplicate or invalid species: "+name)
        seen.add(k)
        ids=known.get(k,[])
        if len(ids)>1:
            audits.append({"scientific_name":name,"reason":"multiple reviewed plant identities","plant_ids":ids})
        matched=ids[0] if len(ids)==1 else None
        source_evidence=linked.get(matched,[]) if matched else []
        # The existence of a nutrition, toxicology or genus-level citation is
        # NOT evidence of observed feeding by a tortoise.
        feeding=[e for e in source_evidence if e.get("type")=="wild_feeding" and taxon(e.get("plant_taxon_reported"))==k and e.get("source_id")]
        item={**row,"matched_reviewed_plant_id":matched,
            "feeding_record_status":"record_under_review" if feeding else "not_verified",
            "feeding_record_evidence":[{"evidence_id":e["evidence_id"],"source_id":e["source_id"],"tortoise_taxon":e.get("tortoise_taxon"),"plant_part":e.get("plant_part")} for e in feeding],
            "feeding_safety_status":"not_assessed","safety_grade":None}
        out.append(item)
    dest=ROOT/"data/global_taxonomy_evidence_join.json"
    dest.write_text(json.dumps({"schema_version":"1.0","record_count":len(out),"records":out},ensure_ascii=False,separators=(",",":"))+"\\n",encoding="utf-8")
    (ROOT/"data/global_taxonomy_evidence_join_audit.json").write_text(json.dumps({"input_records":len(rows),"matched_reviewed_plants":sum(bool(x["matched_reviewed_plant_id"]) for x in out),"feeding_record_under_review":sum(x["feeding_record_status"]=="record_under_review" for x in out),"ambiguous_matches":audits},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    print("joined",len(out),"feeding records under review",sum(x["feeding_record_status"]=="record_under_review" for x in out))
if __name__=="__main__":main()
