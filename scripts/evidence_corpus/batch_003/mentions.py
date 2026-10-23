"""Stage 2 of the batch 003 queue: for every (species, open-access paper) hit, fetch the Europe PMC full text (JATS XML,
cached; batch 001 cache reused) and find where the species is named. Writes mentions.jsonl with the sentence or table row,
its locator, and flags (tortoise named nearby, feeding words nearby, paper about tortoises). Nothing here is evidence.
Run: python -X utf8 mentions.py <queue_results.jsonl> <xml cache dir> <batch-001 xml dir> <out jsonl>
"""
import json, re, sys, time, urllib.request, collections, threading, concurrent.futures as cf
import xml.etree.ElementTree as ET
from pathlib import Path

QR, CACHE, OLD, OUT = map(Path, sys.argv[1:5]); CACHE.mkdir(exist_ok=True)
UA = "geobukbap-evidence-research/0.3 (+https://jinwooson1988.github.io/tortoise-food-db-korea/)"
TG = ["Testudo", "Agrionemys", "Gopherus", "Xerobates", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys",
      "Aldabrachelys", "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria", "Malacochersus", "Pyxis"]
TORT = re.compile(r"\b(tortoises?|" + "|".join(TG) + r")\b")
NOISE = re.compile(r"tortoise beetle|tortoiseshell|tortoise shell|Cassida|Aglais|Testudinis", re.I)
FEED = re.compile(r"\b(ate|eaten|eat|eats|eating|consum\w*|fed\b|feed\w*|forag\w*|brows\w*|graz\w*|ingest\w*|diet\w*|food\w*|fa?ec\w*|scats?|droppings|dung|stomach|frugivor\w*|seed dispers\w*|bites?|selected|preferred|palatab\w*|herbivor\w*)\b", re.I)
T = lambda e: re.sub(r"\s+", " ", "".join(e.itertext())).strip() if e is not None else ""

def xml_for(pmcid):
    for d in (OLD, CACHE):
        p = d / f"{pmcid}.xml"
        if p.exists() and p.stat().st_size > 500:
            return p
    u = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60) as r:
                data = r.read()
            p = CACHE / f"{pmcid}.xml"; p.write_bytes(data); return p
        except Exception as e:
            if getattr(e, "code", None) == 404:
                (CACHE / f"{pmcid}.missing").write_text("404"); return None
            time.sleep(2 ** a)
    return None

def units(path):
    """(locator, text, caption) for every paragraph sentence and table row; title/abstract text."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return "", []
    head = T(root.find(".//article-title")) + " " + T(root.find(".//abstract"))
    out = []
    for sec in root.iter("sec"):
        st = T(sec.find("title"))[:60]
        for p in sec.findall("p"):
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", T(p)):
                out.append(("section: " + st, s, ""))
    for tw in root.iter("table-wrap"):
        lab, cap = T(tw.find("label")), T(tw.find("caption"))
        for tr in tw.iter("tr"):
            out.append((lab or "table", " | ".join(T(c) for c in tr), cap[:300]))
    return head, out

qr = [json.loads(l) for l in QR.read_text(encoding="utf-8").splitlines() if l.strip()]
pairs = collections.defaultdict(list)
for r in qr:
    for h in r["hits"]:
        if h.get("pmcid") and h.get("isOpenAccess") == "Y":
            pairs[h["pmcid"]].append((r["taxon_id"], r["scientific"], h))
print("papers", len(pairs), "pairs", sum(len(v) for v in pairs.values()), flush=True)
done = set()
if OUT.exists():
    for l in OUT.read_text(encoding="utf-8").splitlines():
        done.add(json.loads(l)["pmcid"])
lock = threading.Lock()
def work(pmcid):
    if pmcid in done:
        return
    p = xml_for(pmcid)
    rows = []
    if p:
        head, us = units(p)
        paper_tort = bool(TORT.search(head)) and not NOISE.search(head)
        for tid, name, h in pairs[pmcid]:
            g, ep = name.split()[0], name.split()[1]
            pat = re.compile(r"\b(" + re.escape(name) + r"|" + re.escape(g[0]) + r"\. ?" + re.escape(ep) + r")\b")
            found = [(loc, txt, cap) for loc, txt, cap in us if pat.search(txt)]
            for loc, txt, cap in found[:20]:
                ctx = txt + " " + cap
                rows.append({"pmcid": pmcid, "taxon_id": tid, "scientific": name, "title": h.get("title"), "doi": h.get("doi"),
                             "year": h.get("pubYear"), "journal": h.get("journalTitle"), "locator": loc, "text": txt[:600], "caption": cap,
                             "tortoise_near": bool(TORT.search(ctx)) and not NOISE.search(ctx), "feeding_near": bool(FEED.search(ctx)),
                             "paper_about_tortoises": paper_tort})
            if not found:
                rows.append({"pmcid": pmcid, "taxon_id": tid, "scientific": name, "title": h.get("title"), "doi": h.get("doi"),
                             "locator": None, "text": None, "name_not_in_full_text": True, "paper_about_tortoises": paper_tort})
    else:
        rows.append({"pmcid": pmcid, "full_text_unavailable": True})
    with lock, open(OUT, "a", encoding="utf-8") as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
with cf.ThreadPoolExecutor(4) as ex:
    list(ex.map(work, sorted(pairs)))
print("done", flush=True)
