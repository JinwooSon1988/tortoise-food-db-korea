"""Group stage-2 mentions by paper for manual review, leaving out papers already used by earlier batches."""
import json, sys, collections, glob
M = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
blob = ""
for f in ["../b3-wt/data/catalog_feeding_evidence_fulltext_20261020.json", "../b3-wt/data/feeding_record_fulltext_extracts_v1.json"] + \
         glob.glob("../b3-wt/data/catalog-evidence/batch-00?-*.json"):
    blob += open(f, encoding="utf-8").read()
by = collections.defaultdict(list)
for m in M:
    if m.get("text") and (m["tortoise_near"] or m["paper_about_tortoises"]):
        by[m["pmcid"]].append(m)
rank = []
for p, ms in by.items():
    used = p in blob or (ms[0].get("doi") and ms[0]["doi"] in blob)
    strong = sum(1 for m in ms if m["tortoise_near"] and m["feeding_near"])
    rank.append((used, -strong, -len({m["taxon_id"] for m in ms}), p))
rank.sort()
out = []
for used, s, n, p in rank:
    ms = by[p]
    out.append(f"#### {p} {'USED' if used else 'NEW'} strong={-s} taxa={-n} | {ms[0]['title']} ({ms[0].get('year')}) doi={ms[0].get('doi')}")
    if used:
        continue
    for m in ms[: int(sys.argv[2]) if len(sys.argv) > 2 else 12]:
        out.append(f"   [{m['scientific']}] {m['locator']} :: {m['text'][:260]}" + (f"  || cap: {m['caption'][:140]}" if m.get('caption') else ""))
print("\n".join(out))
