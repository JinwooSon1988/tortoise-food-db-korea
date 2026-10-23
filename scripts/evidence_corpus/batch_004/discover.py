"""Batch 004 literature discovery: Europe PMC open-access full texts about land-tortoise diet, feeding, nutrition and
toxicity that earlier batches did not save.

Searches (all pages, cursorMark) are limited to the open-access subset with full text; each new PMCID's JATS XML is
fetched from the fullTextXML endpoint (the licensed route for machine reading). Output: <out>/meta.jsonl and
<out>/xml/PMCxxxx.xml in the layout make_docs.py reads. Requests go through polite_http (robots.txt, Europe PMC spacing,
retries, provenance in <out>/requests.jsonl); searches and downloads keep checkpoints, so a rerun resumes.
www.ebi.ac.uk asks for Crawl-delay 10 in robots.txt, so downloads run one every 10 s; new documents are ranked by
the number of topic searches they match (then newest first) and at most MAX_NEW are fetched per run.
Run: python -X utf8 -I discover.py <out dir> <existing docs.jsonl> [workers] [max new]
"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from polite_http import Checkpoint, PoliteClient, run_tasks  # noqa: E402

REST = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
TORT = ("(tortoise OR tortoises OR Testudo OR Gopherus OR Chelonoidis OR Geochelone OR Centrochelys OR Stigmochelys OR "
        "Astrochelys OR Aldabrachelys OR Kinixys OR Homopus OR Chersina OR Psammobates OR Indotestudo OR Manouria OR "
        "Malacochersus OR Pyxis OR Agrionemys OR Testudinidae OR jabuti OR tortuga)")
TOPICS = {
    "diet": "(diet OR diets OR dietary OR \"food habits\" OR \"food plants\" OR \"feeding ecology\" OR foraging)",
    "faecal": "(faecal OR fecal OR faeces OR feces OR scat OR scats OR droppings OR \"stomach contents\")",
    "herbivory": "(herbivory OR herbivore OR frugivory OR frugivore OR \"seed dispersal\" OR grazing OR browsing)",
    "captive": "(captive OR zoo OR husbandry) AND (diet OR food OR feeding OR nutrition)",
    "nutrition": "(nutrition OR nutrient OR calcium OR oxalate OR fibre OR fiber) AND (plant OR plants OR forage)",
    "toxicity": "(toxic OR toxicity OR poisoning OR intoxication) AND (plant OR plants)",
}
# Second pass: tortoise genera anywhere in the full text (not only title/abstract) with diet wording.
GENERA_FT = ("(Testudo OR Gopherus OR Chelonoidis OR Geochelone OR Centrochelys OR Stigmochelys OR Astrochelys OR "
             "Aldabrachelys OR Kinixys OR Homopus OR Chersina OR Psammobates OR Indotestudo OR Manouria OR Malacochersus OR "
             "Pyxis OR Agrionemys OR Chersobius)")
FULLTEXT_TOPICS = {"ft_diet": TOPICS["diet"], "ft_faecal": TOPICS["faecal"], "ft_herbivory": TOPICS["herbivory"]}
FIELDS = ("id", "source", "pmid", "pmcid", "doi", "title", "authorString", "pubYear", "journalInfo", "isOpenAccess", "license")


def main():
    out, existing = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    max_new = int(sys.argv[4]) if len(sys.argv) > 4 else 400
    (out / "xml").mkdir(exist_ok=True)
    client = PoliteClient(provenance=out / "requests.jsonl")
    have = {json.loads(l)["doc_id"] for l in existing.read_text(encoding="utf-8").splitlines() if l.strip()}

    scp = Checkpoint(out / "search_checkpoint.jsonl")
    def search(topic):
        q = (f"{GENERA_FT} AND {FULLTEXT_TOPICS[topic]} AND OPEN_ACCESS:y AND HAS_FT:y" if topic in FULLTEXT_TOPICS
             else f"TITLE_ABS:{TORT} AND {TOPICS[topic]} AND OPEN_ACCESS:y AND HAS_FT:y")
        cursor, hits = "*", []
        while True:
            u = REST + "search?" + urllib.parse.urlencode({"query": q, "format": "json", "pageSize": 1000, "resultType": "core",
                                                           "cursorMark": cursor})
            d, _ = client.get_json(u, purpose="europepmc tortoise literature search")
            for x in d.get("resultList", {}).get("result", []):
                if x.get("pmcid"):
                    hits.append({k: x.get(k) for k in FIELDS})
            nxt = d.get("nextCursorMark")
            if not nxt or nxt == cursor or not d.get("resultList", {}).get("result"):
                break
            cursor = nxt
        return "ok", {"query": q, "hit_count": d.get("hitCount"), "hits": hits}
    print("searches", run_tasks(((t, t) for t in list(TOPICS) + list(FULLTEXT_TOPICS)), search, scp, workers=2), flush=True)

    meta = {}
    for t, r in scp.rows.items():
        for h in r.get("hits", []):
            m = meta.setdefault(h["pmcid"], dict(h, topics=[]))
            m["topics"].append(t)
    new = sorted(set(meta) - have, key=lambda p: (-len(meta[p]["topics"]), -int(meta[p].get("pubYear") or 0), p))
    print(len(meta), "open-access hits;", len(new), "not saved before; fetching up to", max_new, flush=True)
    new = new[:max_new]

    dcp = Checkpoint(out / "download_checkpoint.jsonl")
    def download(pmcid):
        body, prov = client.get(REST + f"{pmcid}/fullTextXML", purpose="europepmc open-access full text")
        (out / "xml" / f"{pmcid}.xml").write_bytes(body)
        return "ok", {"sha256": prov["sha256"], "bytes": prov["bytes"]}
    print("downloads", run_tasks(((p, p) for p in new), download, dcp, workers=workers), flush=True)
    with (out / "meta.jsonl").open("w", encoding="utf-8") as f:
        for p in new:
            if dcp.rows.get(p, {}).get("status") == "ok":
                f.write(json.dumps(meta[p], ensure_ascii=False) + "\n")
    print(json.dumps({"hits": len(meta), "new": len(new), "downloaded": sum(1 for p in new if dcp.rows.get(p, {}).get("status") == "ok"),
                      "requests": client.stats}))


if __name__ == "__main__":
    main()
