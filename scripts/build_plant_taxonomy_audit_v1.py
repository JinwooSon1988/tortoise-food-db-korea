#!/usr/bin/env python3
"""Check every scientific name in data/plants.json against three taxonomic authorities.

Sources (all queried through their public APIs; responses are cached so the audit can be rebuilt offline):
  * GBIF Backbone Taxonomy      https://api.gbif.org/v1/species/match
  * Kew WCVP (the checklist behind Plants of the World Online), as published on GBIF
                                https://api.gbif.org/v1/species?datasetKey=f382f0ce-323a-4091-bb9f-add557f3a9a2
    (powo.science.kew.org itself sits behind a Cloudflare challenge and is not accessed; each WCVP record carries
    its POWO URL, which is kept as the citation.)
  * World Flora Online          https://list.worldfloraonline.org/matching_rest.php  (robots.txt: crawl-delay 10 s)

The script never edits data/plants.json. It writes data/plant_taxonomy_audit_v1.json; disagreements between the
sources are recorded, not resolved.

Usage:
  python scripts/build_plant_taxonomy_audit_v1.py --cache <dir> [--offline]
"""
import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "plant_taxonomy_audit_v1.json"
UA = "tortoise-food-db-korea-data-audit/1.0 (+https://github.com/JinwooSon1988/tortoise-food-db-korea)"
WCVP_KEY = "f382f0ce-323a-4091-bb9f-add557f3a9a2"
DELAY = {"api.gbif.org": 0.4, "list.worldfloraonline.org": 10.0}
_last = {}

RANK_MARKERS = ("var.", "subsp.", "f.", "ssp.")


def parse_name(raw):
    """Split a plants.json scientific name into the canonical query string and its taxonomic level."""
    s = raw.strip()
    if re.search(r"\bspp\.?$", s):
        return s.split()[0], "genus"
    level = "species"
    if s.endswith(" agg."):
        s, level = s[:-5].strip(), "aggregate"
    tokens = s.split()
    out = [tokens[0]]
    i = 1
    if i < len(tokens) and tokens[i] == "×":
        out.append("×")
        i += 1
        level = "hybrid"
    if i < len(tokens):
        out.append(tokens[i])
        i += 1
    while i < len(tokens):
        if tokens[i] in RANK_MARKERS and i + 1 < len(tokens):
            out += [tokens[i], tokens[i + 1]]
            level = "infraspecific"
            i += 2
            break
        i += 1  # authorship
    return " ".join(out), level


def fetch(url, cache, offline):
    path = cache / (hashlib.sha1(url.encode("utf-8")).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if offline:
        raise SystemExit("not cached (offline): " + url)
    host = urllib.parse.urlsplit(url).netloc
    wait = DELAY.get(host, 5.0) - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
    _last[host] = time.time()
    data = json.loads(body)
    path.write_bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    return data


def q(s):
    return urllib.parse.quote(s)


def gbif(name, cache, offline):
    m = fetch("https://api.gbif.org/v1/species/match?kingdom=Plantae&verbose=true&name=" + q(name), cache, offline)

    def row(x):
        r = {"usage_key": x.get("usageKey"), "name": x.get("scientificName"), "rank": x.get("rank"),
             "status": x.get("status"), "match_type": x.get("matchType")}
        key = x.get("acceptedUsageKey")
        if key:
            a = fetch("https://api.gbif.org/v1/species/%d" % key, cache, offline)
            r["accepted_name"] = a.get("scientificName")
            r["accepted_canonical"] = a.get("canonicalName")
        elif x.get("status") == "ACCEPTED":
            r["accepted_name"] = x.get("scientificName")
            r["accepted_canonical"] = x.get("canonicalName")
        return r

    res = {"url": "https://api.gbif.org/v1/species/match?kingdom=Plantae&name=" + q(name), "match": row(m)}
    if m.get("matchType") in ("HIGHERRANK", "NONE"):
        res["ambiguous"] = True
        res["alternatives"] = [row(a) for a in m.get("alternatives", [])
                               if a.get("matchType") == "EXACT" and a.get("canonicalName", "").lower() == strip_x(name).lower()]
    return res


def strip_x(name):
    return name.replace("× ", "").replace("×", "")


def wcvp(name, cache, offline):
    rows = []
    seen = set()
    for variant in dict.fromkeys([name, strip_x(name)]):
        d = fetch("https://api.gbif.org/v1/species?datasetKey=%s&limit=50&name=%s" % (WCVP_KEY, q(variant)), cache, offline)
        for x in d.get("results", []):
            if x.get("key") in seen:
                continue
            seen.add(x.get("key"))
            rows.append({"name": x.get("scientificName"), "rank": x.get("rank"), "status": x.get("taxonomicStatus"),
                         "accepted_name": x.get("accepted") or (x.get("scientificName") if x.get("taxonomicStatus") == "ACCEPTED" else None),
                         "powo_url": x.get("references")})
    return {"records": rows}


def wfo_parse(c):
    placement = c.get("placement") or ""
    left, _, right = placement.partition("$")
    segs = left.split("/")
    # The path may contain subfamily/tribe levels; the accepted name starts at the last capitalised segment (genus).
    gen = max((i for i, s in enumerate(segs) if s[:1].isupper()), default=None)
    accepted = " ".join(segs[gen:]) if gen is not None and gen > 2 else None
    return {"wfo_id": c.get("wfo_id"), "name": c.get("full_name_plain"), "role": "synonym" if right else ("accepted" if placement else "unplaced"),
            "accepted_path": accepted or None, "url": "https://list.worldfloraonline.org/" + (c.get("wfo_id") or "")}


def wfo(name, cache, offline):
    d = fetch("https://list.worldfloraonline.org/matching_rest.php?input_string=" + q(name), cache, offline)
    res = {"classification_version": (d.get("params") or {}).get("classificationVersion")}
    if d.get("match"):
        res["match"] = wfo_parse(d["match"])
    else:
        res["candidates"] = [wfo_parse(c) for c in d.get("candidates") or []]
    return res


def canon(s):
    """Lower-cased name without authors, rank markers or hybrid sign, for comparing sources."""
    if not s:
        return None
    s = s.replace("×", " ")
    out = []
    for t in s.split():
        if t in RANK_MARKERS:
            continue
        if out and (t[0].isupper() or t[0] in "(&") :
            break
        out.append(t.lower())
    return " ".join(out)


def author_of(raw, query):
    """Authorship written in plants.json after the name (e.g. 'Lamium album L.' -> 'L.'), or ''."""
    rest = raw.strip()
    for tok in query.split():
        rest = rest.replace(tok, "", 1).strip()
    return "" if rest in ("spp.", "spp", "agg.") else rest


def same_author(name, author):
    squash = lambda x: x.replace(" ", "").lower()
    return not author or squash(name or "").endswith(squash(author))


def summarise(query, level, g, w, f, author=""):
    """Reduce the three answers to accepted-name sets and a status flag.

    Several authors may have published the same binomial (homonyms). When plants.json states the authorship, only
    the records with that authorship are compared; otherwise every homonym is reported."""
    qn = canon(query)
    acc = {}
    gm = g["match"]
    if g.get("ambiguous"):
        acc["gbif"] = sorted({canon(a.get("accepted_canonical") or a.get("accepted_name")) for a in g.get("alternatives", [])
                              if a.get("accepted_name") and same_author(a.get("name"), author)})
    else:
        acc["gbif"] = [canon(gm.get("accepted_canonical") or gm.get("accepted_name"))] if gm.get("accepted_name") else []
    exact_w = [r for r in w["records"] if canon(r["name"]) == qn and same_author(r["name"], author)]
    acc["wcvp"] = sorted({canon(r["accepted_name"]) for r in exact_w if r.get("accepted_name")})
    cands = [f["match"]] if f.get("match") else f.get("candidates", [])
    cands = [c for c in cands if canon(c["name"]) == qn and same_author(c["name"], author)]
    acc["wfo"] = sorted({canon(c["accepted_path"]) for c in cands if c.get("accepted_path")})
    flags = []
    for src, names in acc.items():
        if not names:
            flags.append(src + "_no_match")
        elif len(names) > 1:
            flags.append(src + "_homonym_ambiguous")
        elif names[0] != qn:
            flags.append(src + "_treats_as_synonym")
    sets = [tuple(v) for v in acc.values() if v]
    if len(set(sets)) > 1:
        flags.append("sources_disagree")
    if level == "genus":
        flags.append("genus_level_record")
    if level == "aggregate":
        flags.append("aggregate_record")
    return acc, flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    plants = json.loads((ROOT / "data" / "plants.json").read_text(encoding="utf-8"))
    rows = []
    for n, p in enumerate(plants, 1):
        query, level = parse_name(p["scientific"])
        g = gbif(query, cache, args.offline)
        w = wcvp(query, cache, args.offline)
        f = wfo(query, cache, args.offline)
        author = author_of(p["scientific"], query)
        acc, flags = summarise(query, level, g, w, f, author)
        rows.append({"plant_id": p["id"], "ko": p["ko"], "db_scientific": p["scientific"], "db_family": p["family"],
                     "query_name": query, "db_authorship": author or None, "level": level, "accepted_by_source": acc, "flags": flags,
                     "gbif": g, "wcvp": w, "wfo": f})
        print("%3d/%d %-22s %-38s %s" % (n, len(plants), p["id"], query, ",".join(flags) or "ok"), flush=True)
    counts = {}
    for r in rows:
        for fl in r["flags"]:
            counts[fl] = counts.get(fl, 0) + 1
    report = {
        "schema_version": "1.0",
        "purpose": "Record how GBIF, Kew WCVP (POWO) and World Flora Online treat each scientific name in data/plants.json. "
                   "Descriptive only: no name, identity or feeding verdict is changed by this file.",
        "sources": {
            "gbif": "GBIF Backbone Taxonomy via api.gbif.org/v1/species/match",
            "wcvp": "The World Checklist of Vascular Plants (Royal Botanic Gardens, Kew) as published on GBIF, dataset " + WCVP_KEY + "; powo_url is the Plants of the World Online page for the same record",
            "wfo": "World Flora Online Plant List via list.worldfloraonline.org/matching_rest.php",
        },
        "plant_count": len(rows),
        "flag_counts": dict(sorted(counts.items())),
        "plants": rows,
    }
    OUT.write_bytes((json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
