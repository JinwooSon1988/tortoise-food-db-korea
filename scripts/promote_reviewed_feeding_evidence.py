#!/usr/bin/env python3
"""Promote explicitly reviewed plant evidence into the existing site evidence index.

Input is a JSON file with {"records":[{"reviewed":true,"reviewer":"...",
"scientific":"Genus species","source_url":"https://...","citation":"...",
"tortoise":"Testudo ...","type":"wild_feeding_observation",
"locator":"Table 3, page 8","plant_part":{"ko":"잎","en":"leaves"},
"finding":{"ko":"...","en":"..."},"source_class":"peer_reviewed"}]}.
Unreviewed bibliography candidates are never promoted.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ALLOWED = {"wild_feeding_observation", "captive_feeding_report", "husbandry_guidance", "nutritional_analysis", "toxicity_report"}
def valid_url(url):
    p = urlparse(url)
    return p.scheme == "https" and bool(p.netloc) and not p.username and not p.password

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--approved", default="worker-output/approved-feeding-records.json")
    p.add_argument("--index", default="data/catalog-evidence/batch-002-site-index.json")
    p.add_argument("--report", default="worker-output/promotion-report.json")
    args = p.parse_args()
    path = Path(args.approved)
    if not path.is_file():
        print("No approved records file; nothing published.")
        return
    incoming = json.loads(path.read_text(encoding="utf-8"))
    records = incoming.get("records", [])
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    idxpath = Path(args.index)
    index = json.loads(idxpath.read_text(encoding="utf-8"))
    sources = {s["source_key"]:s for s in index.get("sources", [])}
    by_name = index["by_scientific_name"]
    promoted, rejected = [], []
    for n, record in enumerate(records):
        try:
            if record.get("reviewed") is not True or not str(record.get("reviewer","")).strip():
                raise ValueError("explicit reviewer approval required")
            scientific = str(record["scientific"]).strip()
            if not re.fullmatch(r"[A-Z][a-z-]+ [a-z][a-z-]+", scientific):
                raise ValueError("exact binomial required")
            url = str(record["source_url"])
            if not valid_url(url):
                raise ValueError("HTTPS source URL required")
            if record.get("type") not in ALLOWED:
                raise ValueError("unsupported evidence type")
            for field in ("citation","tortoise","locator"):
                if len(str(record.get(field,"")).strip()) < 5:
                    raise ValueError(field + " missing")
            for field in ("plant_part","finding"):
                value = record.get(field)
                if not isinstance(value,dict) or not all(str(value.get(lang,"")).strip() for lang in ("ko","en")):
                    raise ValueError(field + " must contain ko and en")
            key = "approved_" + __import__("hashlib").sha256(url.encode()).hexdigest()[:16]
            source = {"source_key":key,"citation":record["citation"],"url":url,
                      "language":record.get("language","en"),"source_class":record.get("source_class","other"),
                      "tortoise_taxon":record["tortoise"],"context":record.get("context","unspecified"),
                      "study_id":url,"method":{"ko":"검토 승인 자료","en":"Reviewer-approved source"},
                      "read":record["locator"],"collected_by":"reviewed-import"}
            if key in sources and sources[key]["url"] != url:
                raise ValueError("source key collision")
            sources[key] = source
            entry = {"source_key":key,"reported_name":scientific,"tortoise":record["tortoise"],
                     "type":record["type"],"verification":"reviewed_source_record",
                     "context":record.get("context","unspecified"),"locator":record["locator"],
                     "plant_part":record["plant_part"],"finding":record["finding"]}
            group = by_name.setdefault(scientific.lower(), [])
            if not any(x.get("source_key")==key and x.get("locator")==entry["locator"] and x.get("type")==entry["type"] for x in group):
                group.append(entry)
                promoted.append({"scientific":scientific,"source":url})
        except (KeyError,ValueError,TypeError) as exc:
            rejected.append({"record":n,"reason":str(exc)})
    index["sources"] = sorted(sources.values(), key=lambda x:x["source_key"])
    if promoted:
        idxpath.write_text(json.dumps(index,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    report = {"promoted":len(promoted),"rejected":len(rejected),"promoted_records":promoted,"rejections":rejected,
              "warning":"Review approval must be based on original source inspection, not title/abstract matching."}
    dest = Path(args.report)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if rejected:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
