#!/usr/bin/env python3
"""Build evidence-backed feeding-practice details for reviewed plants and GBIF candidates.

Only explicitly present fields are emitted. No missing frequency, portion, mixture,
preparation or animal species is inferred. GBIF taxonomy is NOT feeding evidence.
Run: python scripts/build_feeding_practice_index.py
"""
import json,re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))
def binomial(value):
    m=re.match(r"^([A-Z][a-z-]+) ([a-z][a-z-]+)(?=$|[^a-z])",str(value or "").strip())
    return " ".join(m.groups()).casefold() if m else ""
def details(e):
    # These are explicit metadata fields only; never interpret source title as dosage.
    aliases={"mixture":["feed_mixture","mixed_with","diet_combination"],
             "frequency":["feeding_frequency","frequency"],
             "quantity":["feeding_quantity","feeding_amount","portion"],
             "plant_part":["plant_part"],
             "presentation":["presentation","feeding_form","form"],
             "preparation":["preparation","cutting_method","processing"],
             "tortoise_taxon":["tortoise_taxon"]}
    d={}
    for label,fields in aliases.items():
        for field in fields:
            value=e.get(field)
            if isinstance(value,str) and value.strip() and value.strip().lower() not in ("unknown","not_applicable","not reported","n/a"):
                d[label]=value.strip();break
    return d
def main():
    links=read("data/plant_feeding_evidence_links.json")["records"]
    reviewed=read("data/plants.json")
    identities={p["id"]:binomial(p.get("scientific")) for p in reviewed}
    indexed=defaultdict(list)
    for item in links:
        k=identities.get(item["plant_id"])
        if not k:continue
        for e in item["evidence"]:
            if e.get("type") not in ("wild_feeding","specialist_plant_database","husbandry_feeding","zoo_diet","veterinary_feeding"):continue
            direct=binomial(e.get("plant_taxon_reported"))==k
            # Genus-level or related-species observations are contextual only.
            indexed[k].append({
                "evidence_id":e.get("evidence_id"),"source_url":e.get("source_id"),
                "evidence_type":e.get("type"),"identity_match":"species" if direct else "related_taxon",
                "observed_feeding":bool(direct and e.get("type")=="wild_feeding"),
                "practice":details(e),
                "safety_grade_inferred":False
            })
    entries=[]
    manifest=read("data/taxonomy-shards/index.json")
    if manifest.get("count")!=9995:raise ValueError("unexpected taxonomy manifest")
    for shard in manifest["shards"]:
        for row in read("data/taxonomy-shards/"+shard["file"])["records"]:
            k=binomial(row["scientific_name"])
            evidence=indexed.get(k,[])
            entries.append({"taxon_id":row["taxon_id"],"scientific_name":row["scientific_name"],
                "feeding_record_status":"record_under_review" if any(e["observed_feeding"] for e in evidence) else "not_verified",
                "evidence":evidence,"safety_grade":None})
    if len(entries)!=9995:raise ValueError("unexpected taxonomy size")
    dest=ROOT/"data/global_feeding_practice_index.json"
    dest.write_text(json.dumps({"schema_version":"1.0","scope":"source-reported practices; not feeding safety verdicts",
        "records":entries},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("records",len(entries),"with_source_context",sum(bool(e["evidence"]) for e in entries),
          "with_verified_species_wild_feeding",sum(e["feeding_record_status"]=="record_under_review" for e in entries))
if __name__=="__main__":main()
