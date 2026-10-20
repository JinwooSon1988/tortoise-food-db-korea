"""Extract candidate plant-feeding statements from tortoise papers (JATS XML from Europe PMC, and pdftotext output).

Nothing here links evidence. It writes candidates for manual review:
  papers.json     one row per tortoise-focused paper: tortoise taxa named, diet tables, counts
  candidates.json table rows of diet tables and feeding sentences that name a plant binomial
Plant names are resolved later against GBIF; here every binomial-looking name is kept with the paper's abbreviation map.
"""
import json, pathlib, re, sys, collections
import xml.etree.ElementTree as ET

HERE = pathlib.Path.cwd()  # the scratch directory holding xml/, ft/xml/ and oa/txt/
REPO = pathlib.Path(sys.argv[1])
TORT_GENERA = ["Testudo", "Agrionemys", "Gopherus", "Xerobates", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys", "Aldabrachelys",
               "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria", "Malacochersus", "Pyxis", "Cylindraspis"]
TORT = re.compile(r"\b(tortoises?|" + "|".join(TORT_GENERA) + r")\b")
TORT_SP = re.compile(r"\b(" + "|".join(TORT_GENERA) + r") ([a-z]{3,})(?: ([a-z]{4,}))?\b")
NOISE = re.compile(r"tortoise beetle|Cassida|Chrysomelidae|tortoiseshell|Aglais|tortoise shell|plastron extract|Testudinis", re.I)
DIET_CAP = re.compile(r"\b(diet|dietary|food|foods|eaten|eat|consum|ingest|fa?ecal|fa?eces|scats?|droppings|dung|stomach|gut content|forag|bites?|selected|selection|preferen|browse|graz|fed\b|feeding|seeds? (dispersed|recovered|found)|dispers|frugivor)", re.I)
FEED_SENT = re.compile(r"\b(ate|eaten|eat|eats|eating|consum\w*|fed on|feed on|feeds on|feeding on|foraged|browsed|grazed|ingest\w*|bit|bites|in (the )?(fa?eces|scats?|droppings|stomach)|fa?ecal|scats? contained|diet (consisted|included|was dominated|comprised))\b", re.I)
NEG = re.compile(r"\b(not (eaten|consumed|observed)|never|avoid\w*|absent from|not found in|not detected|rejected|refused)\b", re.I)
BINOM = re.compile(r"\b([A-Z][a-z]{2,}) ([a-z][a-z-]{2,})\b")
ABBR = re.compile(r"\b([A-Z])\. ([a-z][a-z-]{2,})\b")
STOP_EPITHETS = {"and", "the", "with", "from", "were", "was", "for", "spp", "sp", "species", "were", "that", "this", "are", "had", "has", "plants", "plant", "leaves",
                 "flowers", "fruits", "seeds", "et", "al", "in", "of", "on"}

catalog = {r[1] for r in json.load(open(REPO / "data/plant-catalog/search.json", encoding="utf-8"))["rows"]}
genera_known = {n.split()[0] for n in catalog}
T = lambda e: re.sub(r"\s+", " ", "".join(e.itertext())).strip() if e is not None else ""
sentences = lambda p: re.split(r"(?<=[.!?])\s+(?=[A-Z(])", p)


def names_in(text, abbr, strict=True):
    out = set()
    for g, sp in BINOM.findall(text):
        if (g in genera_known or not strict) and sp not in STOP_EPITHETS and g not in TORT_GENERA:
            out.add(f"{g} {sp}")
    for gi, sp in ABBR.findall(text):
        g = abbr.get(gi)
        if g and sp not in STOP_EPITHETS:
            out.add(f"{g} {sp}")
    return out


def abbr_map(full):
    # initial -> genus, only when exactly one plant genus with that initial is written out in the paper
    by = collections.defaultdict(set)
    for g, sp in BINOM.findall(full):
        if g in genera_known and g not in TORT_GENERA:
            by[g[0]].add(g)
    return {k: next(iter(v)) for k, v in by.items() if len(v) == 1}


def tortoise_taxa(text):
    c = collections.Counter()
    for g, sp, ssp in TORT_SP.findall(text):
        if sp in STOP_EPITHETS or sp in ("spp", "and"):
            continue
        c[f"{g} {sp}"] += 1
    return c.most_common(6)


def from_xml(path, meta):
    root = ET.parse(path).getroot()
    title = T(root.find(".//article-meta/title-group/article-title")) or meta.get("title") or ""
    abstract = T(root.find(".//abstract")) or re.sub("<[^>]+>", "", meta.get("abstractText") or "")
    body = root.find(".//body")
    if body is None:
        return None, []
    full = T(body)
    focus = bool(TORT.search(title + " " + abstract)) and not NOISE.search(title + " " + abstract)
    if not focus:
        return None, []
    abbr = abbr_map(full)
    cands, tables = [], []

    def walk(e, sec):
        for c in e:
            tag = c.tag.split("}")[-1]
            if tag == "sec":
                walk(c, (sec + " > " if sec else "") + T(c.find("title")))
            elif tag == "p":
                para = T(c)
                for s in sentences(para):
                    if FEED_SENT.search(s) and (TORT.search(s) or TORT.search(para)):
                        for n in names_in(s, abbr):
                            cands.append({"kind": "sentence", "locator": sec or "body", "name": n, "text": s[:700], "negative": bool(NEG.search(s))})
            elif tag == "table-wrap":
                lab, cap = T(c.find("label")), T(c.find("caption"))
                foot = T(c.find("table-wrap-foot"))
                head = " | ".join(T(x) for x in c.iter() if x.tag.split("}")[-1] == "th")[:400]
                diet = bool(DIET_CAP.search(cap + " " + head))
                rows = [[T(td) for td in tr] for tr in c.iter() if tr.tag.split("}")[-1] == "tr"]
                hits = []
                for r in rows:
                    for n in names_in(" | ".join(r[:2]), abbr, strict=False):
                        hits.append(n)
                        if diet:
                            cands.append({"kind": "table_row", "locator": lab, "caption": cap[:500], "name": n, "text": " | ".join(r)[:400]})
                tables.append({"label": lab, "caption": cap[:600], "header": head, "foot": foot[:400], "diet_caption": diet, "plant_names": len(set(hits))})
            else:
                walk(c, sec)

    walk(body, "")
    paper = {"title": title, "tortoise_taxa": tortoise_taxa(title + " " + abstract + " " + full[:20000]), "tables": tables,
             "abstract_names": sorted(names_in(abstract, abbr))}
    return paper, cands


TABLE_CAP = re.compile(r"^\s*(Table|TABLE)\s+(\d+|[IVX]+)\.?\s*(.*)")


def from_txt(path, w):
    # pdftotext output of an OpenAlex open-access PDF; sentences plus lines under a diet-table caption
    title = w.get("title") or ""
    inv = w.get("abstract_inverted_index") or {}
    abstract = " ".join(k for k, _ in sorted(((k, p) for k, ps in inv.items() for p in ps), key=lambda x: x[1]))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if not (TORT.search(title + " " + abstract) or len(TORT.findall(raw[:6000])) >= 3) or NOISE.search(title + " " + abstract):
        return None, []
    lines = raw.splitlines()
    full = re.sub(r"-\n(?=[a-z])", "", raw)
    full = re.sub(r"\s+", " ", full)
    abbr = abbr_map(full)
    cands, tables = [], []
    for s in sentences(full):
        if len(s) < 2000 and FEED_SENT.search(s) and TORT.search(s):
            for n in names_in(s, abbr):
                cands.append({"kind": "sentence", "locator": "pdf text", "name": n, "text": s[:700], "negative": bool(NEG.search(s))})
    i = 0
    while i < len(lines):
        m = TABLE_CAP.match(lines[i])
        if m:
            cap = " ".join(l.strip() for l in lines[i:i + 3])[:500]
            diet = bool(DIET_CAP.search(cap))
            hits = []
            for l in lines[i + 1:i + 120]:
                if TABLE_CAP.match(l):
                    break
                for n in names_in(l, abbr, strict=True):
                    hits.append(n)
                    if diet:
                        cands.append({"kind": "table_row", "locator": f"Table {m.group(2)}", "caption": cap, "name": n, "text": l.strip()[:400]})
            tables.append({"label": f"Table {m.group(2)}", "caption": cap, "header": "", "foot": "", "diet_caption": diet, "plant_names": len(set(hits))})
        i += 1
    paper = {"title": title, "tortoise_taxa": tortoise_taxa(title + " " + abstract + " " + full[:20000]), "tables": tables,
             "abstract_names": sorted(names_in(abstract, abbr))}
    return paper, cands


def main():
    meta = {}
    for f in [HERE / "meta.jsonl", HERE / "ft/meta.jsonl"]:
        if f.exists():
            for l in f.read_text(encoding="utf-8").splitlines():
                m = json.loads(l)
                if m.get("pmcid"):
                    meta[m["pmcid"]] = m
    xmls = {}
    for d in [HERE / "xml", HERE / "ft/xml"]:
        for x in d.glob("*.xml"):
            xmls[x.stem] = x
    papers, cands = {}, []
    for pmc, x in sorted(xmls.items()):
        try:
            p, c = from_xml(x, meta.get(pmc, {}))
        except ET.ParseError:
            continue
        if p:
            m = meta.get(pmc, {})
            p.update(pmcid=pmc, doi=m.get("doi"), year=m.get("pubYear"), authors=m.get("authorString"),
                     journal=((m.get("journalInfo") or {}).get("journal") or {}).get("title") or m.get("journal"), license=m.get("license"))
            papers[pmc] = p
            for k in c:
                k["paper"] = pmc
            cands += c
    import hashlib
    works = json.loads((HERE / "oa/works.json").read_text(encoding="utf-8")) if (HERE / "oa/works.json").exists() else []
    by_sha = {hashlib.sha1(w["id"].encode()).hexdigest()[:16]: w for w in works}
    for t in sorted((HERE / "oa/txt").glob("*.txt")):
        w = by_sha.get(t.stem)
        if not w:
            continue
        p, c = from_txt(t, w)
        if p:
            key = "oa:" + w["id"].rsplit("/", 1)[-1]
            loc = w.get("best_oa_location") or {}
            p.update(pmcid=None, openalex=w["id"], doi=(w.get("doi") or "").replace("https://doi.org/", "") or None, year=w.get("publication_year"),
                     authors=", ".join(((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or [])[:6]),
                     journal=((loc.get("source") or {}).get("display_name")), license=loc.get("license"), url=loc.get("landing_page_url"), pdf_url=loc.get("pdf_url"))
            papers[key] = p
            for k in c:
                k["paper"] = key
            cands += c
    json.dump(papers, open(HERE / "papers.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(cands, open(HERE / "candidates.json", "w", encoding="utf-8"), ensure_ascii=False)
    print("xml", len(xmls), "tortoise-focused papers", len(papers), "with diet tables", sum(any(t["diet_caption"] and t["plant_names"] for t in p["tables"]) for p in papers.values()),
          "candidates", len(cands), collections.Counter(c["kind"] for c in cands), "distinct names", len({c["name"] for c in cands}))


if __name__ == "__main__":
    main()
