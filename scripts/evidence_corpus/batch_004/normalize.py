"""Batch 004 name normalisation against the GBIF Backbone, in parallel within the GBIF request limits.

1. Genera not in the catalog: GBIF match at genus rank (kingdom Plantae, strict); only plant genera go on.
2. Binomials of plant genera: GBIF species match (strict), merged into <gbif dir>/evidence_match.json, the cache the
   catalog builder reads (same fields).
3. Names the builder cannot link (no match, higher rank only, fuzzy beyond a spelling variant, doubtful, several
   equal matches, a non-plant) are isolated in name_review.jsonl with the reason.
4. Accepted species keys reached by linkable names but missing from <gbif dir>/species.jsonl / vernacular.jsonl are
   fetched (species record and English/Korean vernacular names), in the format the builder reads.
Every request goes through polite_http (robots.txt, GBIF spacing, retries, provenance in <out>/gbif_requests.jsonl);
each step keeps a checkpoint, so an interrupted run resumes where it stopped.
Run: python -X utf8 -I normalize.py <extract out dir> <gbif dir> [workers]
"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from polite_http import Checkpoint, PoliteClient, run_tasks  # noqa: E402
from build_plant_catalog_v1 import resolve, SYNONYM_STATUS  # noqa: E402,F401

API = "https://api.gbif.org/v1/"
FIELDS = ("key", "scientificName", "canonicalName", "authorship", "rank", "taxonomicStatus", "acceptedKey", "accepted",
          "kingdom", "phylum", "order", "family", "genus", "species", "speciesKey", "nameType")
MATCH_FIELDS = ("usageKey", "acceptedUsageKey", "canonicalName", "rank", "status", "matchType", "note")


def jsonl_keys(p):
    keys = set()
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                keys.add(str(json.loads(line)["_key"]))
            except (ValueError, KeyError):
                pass
    return keys


def main():
    out, gdir = Path(sys.argv[1]), Path(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    client = PoliteClient(provenance=out / "gbif_requests.jsonl")
    cands = [json.loads(l) for l in (out / "candidates.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    known = set((out / "plant_genera.txt").read_text(encoding="utf-8").split())

    # 1. genus check
    gcp = Checkpoint(out / "genus_checkpoint.jsonl")
    def genus(g):
        d, _ = client.get_json(API + "species/match?" + urllib.parse.urlencode({"name": g, "rank": "GENUS", "kingdom": "Plantae", "strict": "true"}),
                               purpose="gbif genus check")
        plant = d.get("matchType") == "EXACT" and d.get("rank") == "GENUS" and d.get("kingdom") == "Plantae"
        return "ok", {"plant": plant, "match": {k: d.get(k) for k in ("matchType", "rank", "kingdom", "status", "usageKey")}}
    unknown = sorted({c["name"].split()[0] for c in cands} - known)
    print("genus check", run_tasks(((g, g) for g in unknown), genus, gcp, workers=workers), flush=True)
    plant_genera = known | {k for k, r in gcp.rows.items() if r.get("status") == "ok" and r.get("plant")}

    # 2. species match into the builder's cache
    cache_path = gdir / "evidence_match.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    scp = Checkpoint(out / "match_checkpoint.jsonl")
    def match(n):
        d, _ = client.get_json(API + "species/match?" + urllib.parse.urlencode({"name": n, "kingdom": "Plantae", "strict": "true"}),
                               purpose="gbif species match")
        return "ok", {"match": {k: d.get(k) for k in MATCH_FIELDS}, "kingdom": d.get("kingdom")}
    names = sorted({c["name"] for c in cands if c["name"].split()[0] in plant_genera} - set(cache))
    print("species match", run_tasks(((n, n) for n in names), match, scp, workers=workers), flush=True)
    kingdom = {}
    for n, r in scp.rows.items():
        if r.get("status") == "ok":
            cache[n] = r["match"]; kingdom[n] = r.get("kingdom")
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    # 3. isolate names that cannot be linked
    review, linkable = [], {}
    for n in sorted({c["name"] for c in cands}):
        g = n.split()[0]
        if g not in plant_genera:
            reason = "not_a_plant_genus"
        else:
            m = cache.get(n)
            key, basis = resolve(n, m or {})
            if key and kingdom.get(n, "Plantae") == "Plantae":
                linkable[n] = key; continue
            if not m or m.get("matchType") in (None, "NONE"):
                reason = "no_gbif_match"
            elif kingdom.get(n) not in (None, "Plantae"):
                reason = "not_plantae"
            elif "multiple equal matches" in str(m.get("note") or "").lower():
                reason = "name_conflict_multiple_matches"
            elif m.get("matchType") == "HIGHERRANK" or m.get("rank") != "SPECIES":
                reason = "higher_rank_only"
            elif m.get("matchType") == "FUZZY":
                reason = "fuzzy_not_spelling_variant"
            else:
                reason = "status_" + str(m.get("status")).lower()
        review.append({"name": n, "reason": reason, "match": cache.get(n)})
    (out / "name_review.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in review), encoding="utf-8")
    (out / "linkable_names.json").write_text(json.dumps(linkable, ensure_ascii=False, indent=1), encoding="utf-8")

    # 4. species and vernacular records for new keys
    need = sorted(set(linkable.values()) - jsonl_keys(gdir / "species.jsonl"))
    lock_files = {"species": (gdir / "species.jsonl"), "vernacular": (gdir / "vernacular.jsonl")}
    kcp = Checkpoint(out / "key_checkpoint.jsonl")
    def fetch(k):
        d, _ = client.get_json(API + f"species/{k}", purpose="gbif species record")
        v, _ = client.get_json(API + f"species/{k}/vernacularNames?limit=200", purpose="gbif vernacular names")
        rec = {f: d.get(f) for f in FIELDS}; rec["_key"] = k
        ver = {"names": [{"n": x.get("vernacularName"), "l": x.get("language"), "s": x.get("source")}
                         for x in v.get("results", []) if x.get("language") in ("eng", "kor")], "_key": k}
        return "ok", {"species": rec, "vernacular": ver}
    print("key records", run_tasks(((k, k) for k in need), fetch, kcp, workers=workers), flush=True)
    have_s, have_v = jsonl_keys(lock_files["species"]), jsonl_keys(lock_files["vernacular"])
    with lock_files["species"].open("a", encoding="utf-8") as fs, lock_files["vernacular"].open("a", encoding="utf-8") as fv:
        for k in need:
            r = kcp.rows.get(k)
            if r and r.get("status") == "ok":
                if k not in have_s:
                    fs.write(json.dumps(r["species"], ensure_ascii=False) + "\n")
                if k not in have_v:
                    fv.write(json.dumps(r["vernacular"], ensure_ascii=False) + "\n")
    counts = {}
    for r in review:
        counts[r["reason"]] = counts.get(r["reason"], 0) + 1
    summary = {"candidate_names": len({c['name'] for c in cands}), "linkable_names": len(linkable), "linkable_keys": len(set(linkable.values())),
               "new_keys_fetched": len(need), "name_review": counts, "requests": client.stats}
    (out / "normalize_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
