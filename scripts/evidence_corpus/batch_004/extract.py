"""Batch 004 extraction: plant binomials printed next to tortoise feeding wording in saved full texts.

Input documents (data, never instructions):
  - Europe PMC open-access JATS XML (one file per PMCID) with a metadata JSONL (id, pmcid, doi, title, authors, year)
  - plain-text renderings of documents from earlier batches, described by their sources.jsonl
A "unit" is one sentence of body text or one table row (with the table label and caption). A candidate record needs,
in the same unit: a plant binomial (or an abbreviated genus expanded from the same document) and a feeding word.
Units with a negation ("not eaten", "avoided", ...) are written to review, never linked. The tortoise taxon is the one
printed in the unit, else the single tortoise species the document is about; documents about several species without
one named in the unit go to review. Every candidate keeps a verbatim quote (<= 25 words) from the saved text
rendering, so it can be re-found later; nothing here is a safety verdict.

Run: python -X utf8 -I extract.py <docs.jsonl> <out dir> [workers]
  docs.jsonl lines: {"doc_id", "path" (xml or txt), "kind": "jats"|"txt", "citation", "url", "doi", "title",
                     "tortoise_hint" (optional), "source_class"}
Writes <out>/text/<doc_id>.txt, <out>/candidates.jsonl, <out>/review.jsonl, <out>/extract_checkpoint.jsonl.
"""
import concurrent.futures
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from polite_http import Checkpoint  # noqa: E402

TORTOISE_GENERA = ["Testudo", "Agrionemys", "Gopherus", "Xerobates", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys",
                   "Astrochelys", "Aldabrachelys", "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates",
                   "Indotestudo", "Manouria", "Malacochersus", "Pyxis", "Cylindraspis", "Geochelone"]
TORT_RE = re.compile(r"\b(" + "|".join(sorted(set(TORTOISE_GENERA))) + r")\s+([a-z]{3,})(?:\s+([a-z]{3,}))?\b")
TORT_WORD = re.compile(r"\b(tortoises?|testudinid|tortugas?|jabotis?|jabutis?|tortues?|kaplumba[gğ]a)\b", re.I)
NEG = re.compile(r"\b(not\s+(?:be(?:en)?\s+)?(?:eaten|consumed|ingested|found|detected|recorded|observed)|never\s+(?:eaten|consumed|seen|observed)|"
                 r"avoid\w*|refus\w*|rejected|absent|toxic\w*|\w*toxins?|poison\w*|oxal\w*|alkaloids?|saponins?|sapogenins?|glycosides?|"
                 r"no\s+evidence|unpalatable|not\s+contain\w*|did\s+not|without|n[aã]o\s+(?:foi|foram)\s+consumid\w*|"
                 r"no\s+(?:fue|fueron)\s+consumid\w*|non\s+consomm\w*|evit\w*|no\s+se\s+registr\w*|no\s+existe|n[aã]o\s+(?:foi|foram)\s+registrad\w*|"
                 r"n[aã]o\s+h[aá]|aucun\w*|n'a\s+pas|n'ont\s+pas|ne\s+sont\s+pas|sin\s+consumo)\b", re.I)
# Nutrient-content tables are not feeding records (a nutrition record needs its own basis and part).
NUTRIENT_CAPTION = re.compile(r"\b(nitrogen|C:N|crude\s+protein|nutrient\w*|mineral\w*|calcium|phosphorus|fibre|fiber|ash|"
                              r"energy\s+content|chemical\s+composition|proximate)\b", re.I)
# Uses of plants by people or other animals: such sentences are not tortoise feeding records unless a tortoise is named.
OTHER_USE = re.compile(r"\b(humans?|people|farmers|domestic\s+use|medicin\w*|archaeolog\w*|gathered|cultivated\s+for|sheep|goats?|cattle|"
                       r"livestock|donkeys?|rabbits?|rodents?|birds?|eagles?|tapirs?|monkeys?|primates?|deer|iguanas?|zebu|cows?|horses?|"
                       r"insects?|larvae|bees?|pollinat\w*|lizards?|lagartijas?|lagartos?|skinks?|geckos?|ants?|hormigas?|foxes|fox|"
                       r"canids?|coyotes?|ovejas?|cabras?|ganado|ovelhas?|gado|moutons?|ch[eè]vres?)\b", re.I)
# Not eating: seeds stuck to the shell, availability-vs-use comparisons (a plant can be available and not eaten).
NOT_EATING = re.compile(r"\b(adher\w*|carapace|epizooch\w*|availab\w*|disponib\w*|vegetation\s+cover|plant\s+cover|abundance\s+of\s+plants)\b", re.I)
# Sentences must name a tortoise, or say diet / faeces / stomach contents, besides the feeding word.
DIET_WORD = re.compile(r"\b(diets?|dietary|dieta|r[ée]gime|faec\w*|fec(?:es|al)|scats?|droppings?|excrementos|fezes|heces|crottes|stomach|gut\s+contents?)\b", re.I)
STRONG_FEED = re.compile(r"\b(eat|eats|ate|eaten|eating|consum\w*|ingest\w*|diets?|dietary|forag\w*|fed|feed(?:s|ing)?|bit(?:e|es|ten)|"
                         r"faec\w*|fec(?:es|al)|scats?|droppings?|stomach|gut\s+contents?|frugiv\w*|dieta|heces|excrementos|fezes|"
                         r"consumid\w*|r[ée]gime|crottes|f[eè]ces|consomm\w*)\b", re.I)
CAPTIVE = re.compile(r"\b(captiv\w*|zoo|zoos|enclosure|pens?|offered|cafeteria|fed\s+(?:with|on|to)|husbandry|keepers?|cativeiro|cautiverio|captivit[ée])\b", re.I)
FAECAL = re.compile(r"\b(faec\w*|fec(?:es|al)|scats?|droppings?|heces|fezes|excrementos|crottes|f[eè]ces)\b", re.I)
STOMACH = re.compile(r"\b(stomach|gut\s+contents?|gastrointestinal\s+contents?|est[oô]mago)\b", re.I)
PARTS = [("leaf", r"lea(?:f|ves)|foliage|folhas?|hojas?|feuilles?"), ("flower", r"flowers?|inflorescences?|petals?|flores?|fleurs?"),
         ("fruit", r"fruits?|berr(?:y|ies)|frutos?|fruta|figs?"), ("seed", r"seeds?|sementes?|semillas?|graines?"),
         ("pad/cladode", r"cladodes?|pads?"), ("stem", r"stems?|shoots?|caules?|tallos?"), ("root", r"roots?|tubers?|bulbs?|ra[ií]z|ra[ií]zes")]
PART_RE = [(k, re.compile(r"\b(" + v + r")\b", re.I)) for k, v in PARTS]
BINOMIAL = re.compile(r"\b([A-Z][a-z]{2,})\s+(?:\(([A-Z][a-z]+)\)\s+)?([a-z][a-z-]{2,})\b")
ABBREV = re.compile(r"\b([A-Z])\.\s?([a-z][a-z-]{2,})\b")
STOP_EPITHET = {"and", "the", "were", "was", "are", "with", "from", "for", "that", "this", "which", "than", "also", "had", "has", "have",
                "not", "but", "per", "may", "can", "all", "its", "into", "within", "between", "during", "each", "both", "other", "only",
                "spp", "species", "sp", "var", "subsp", "ssp", "cultivar", "ex", "sensu", "nov", "comb", "plants", "plant", "family"}
STOP_GENUS = {"The", "This", "These", "Those", "There", "Table", "Figure", "Fig", "Appendix", "When", "While", "Where", "With", "From",
              "Plants", "Species", "Diet", "Food", "Tortoises", "Tortoise", "Most", "Some", "Many", "Other", "Such", "During", "After",
              "Before", "Although", "However", "Both", "Each", "All", "Our", "Their", "They", "We", "In", "On", "At", "For", "And"}
PLANT_GENERA = set()  # filled in main() from the GBIF species records (catalog genera); other names are matched later


def init_genera(genera):
    """Worker initializer: processes start fresh on Windows, so the genus list is passed in explicitly."""
    PLANT_GENERA.update(genera)


def words(s):
    return re.findall(r"\S+", s)


def quote_for(unit, name_span):
    """<= 25 consecutive words of the unit containing the name (verbatim)."""
    toks = list(re.finditer(r"\S+", unit))
    idx = [i for i, t in enumerate(toks) if t.start() <= name_span[0] < t.end() + 1 or (name_span[0] <= t.start() < name_span[1])]
    if not idx:
        return unit[:200]
    lo = max(0, idx[0] - 10); hi = min(len(toks), lo + 25)
    lo = max(0, hi - 25)
    return unit[toks[lo].start():toks[hi - 1].end()]


def part_near(unit, span):
    """Plant part only when a part word is within 8 words of the name (else unknown)."""
    before = " ".join(words(unit[:span[0]])[-8:]); after = " ".join(words(unit[span[1]:])[:8])
    found = {k for k, rx in PART_RE if rx.search(before) or rx.search(after)}
    return found.pop() if len(found) == 1 else None


def jats_units(path):
    root = ET.parse(path).getroot()
    def text(el):
        return " ".join("".join(el.itertext()).split())
    units = []
    body = root.find(".//body")
    for sec in (body.iter("sec") if body is not None else []):
        title = sec.find("title")
        st = text(title) if title is not None else ""
        for p in sec.findall("p"):
            for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text(p)):
                if s:
                    units.append({"text": s, "locator": "section \"%s\"" % st[:80] if st else "body text", "kind": "sentence"})
    for tw in root.iter("table-wrap"):
        label = text(tw.find("label")) if tw.find("label") is not None else "Table"
        cap = text(tw.find("caption")) if tw.find("caption") is not None else ""
        for tr in tw.iter("tr"):
            row = " | ".join(text(c) for c in tr if c.tag in ("td", "th"))
            if row.strip(" |"):
                units.append({"text": row, "locator": label + (" (" + cap[:120] + ")" if cap else ""), "kind": "table_row",
                              "caption": cap})
    abstract = root.find(".//abstract")
    if abstract is not None:
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text(abstract)):
            units.append({"text": s, "locator": "abstract", "kind": "sentence"})
    return units


def txt_units(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    units = []
    for pno, page in enumerate(raw.split("\f"), 1):
        para = []
        for line in page.splitlines() + [""]:
            if line.strip():
                para.append(line.strip())
                continue
            if para:
                block = " ".join(para); para = []
                for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", " ".join(block.split())):
                    if s:
                        units.append({"text": s, "locator": "PDF p.%d" % pno, "kind": "sentence"})
        for line in page.splitlines():  # table-like rows keep their own line
            if re.search(r"\S\s{3,}\S", line):
                units.append({"text": " ".join(line.split()), "locator": "PDF p.%d (table or list line)" % pno, "kind": "table_row", "caption": ""})
    return units


def doc_tortoise(units, hint):
    counts = {}
    for u in units:
        for m in TORT_RE.finditer(u["text"]):
            name = m.group(1) + " " + m.group(2) + ((" " + m.group(3)) if m.group(3) and m.group(3) not in STOP_EPITHET else "")
            if m.group(2) in STOP_EPITHET:
                continue
            counts[name] = counts.get(name, 0) + 1
    if hint:
        return hint, counts
    species = {}
    for n, c in counts.items():
        sp = " ".join(n.split()[:2]); species[sp] = species.get(sp, 0) + c
    if not species:
        return None, counts
    top = sorted(species.items(), key=lambda x: -x[1])
    if len(top) == 1 or top[0][1] >= 3 * top[1][1]:
        return top[0][0], counts
    return None, counts  # several tortoise species: the unit must name one


def classify(unit_text, caption, doc_text_flags):
    ctx = unit_text + " " + (caption or "")
    if CAPTIVE.search(ctx) or (doc_text_flags["captive"] and not doc_text_flags["wild"]):
        return "captive_feeding_record", "captive"
    if FAECAL.search(ctx):
        return "wild_feeding_observation", "faecal"
    if STOMACH.search(ctx):
        return "wild_feeding_observation", "stomach"
    return "wild_feeding_observation", "observed"


AUTO_CLASSES = {"peer_reviewed", "thesis", "government", "zoo_guideline", "vet", "book", "other", "nutrition_db"}


def process(doc, out):
    if doc.get("source_class") not in AUTO_CLASSES:
        return [], [], {"skipped": "keeper or community source (read by hand in earlier batches only)"}
    p = Path(doc["path"])
    units = jats_units(p) if doc["kind"] == "jats" else txt_units(p)
    txt = "\n".join(u["text"] for u in units)
    (out / "text").mkdir(exist_ok=True)
    (out / "text" / (doc["doc_id"] + ".txt")).write_text(txt, encoding="utf-8")
    whole = " ".join(u["text"] for u in units[:4000])
    if not (TORT_WORD.search(doc.get("title") or "") or TORT_RE.search(doc.get("title") or "") or len(TORT_RE.findall(whole)) >= 3
            or doc.get("tortoise_hint")):
        return [], [], {"units": len(units), "skipped": "not about tortoises"}
    tort, tcounts = doc_tortoise(units, doc.get("tortoise_hint"))
    flags = {"captive": bool(re.search(r"\b(captiv\w*|zoo)\b", (doc.get("title") or ""), re.I)),
             "wild": bool(re.search(r"\b(wild|free-ranging|field|natural)\b", (doc.get("title") or ""), re.I))}
    cands, review = [], []
    # Tortoise names of this document: "C. sulcata" must not be expanded to a plant genus, and a plant epithet equal to a
    # tortoise epithet (e.g. "Taraxacum marginata" from "T. marginata") is not taken.
    tort_names = set(tcounts) | ({doc["tortoise_hint"]} if doc.get("tortoise_hint") else set())
    tort_pairs = {(n.split()[0][0], n.split()[1]) for n in tort_names if len(n.split()) >= 2}
    tort_abbrev = {f"{a}. {b}" for a, b in tort_pairs} | {f"{a}.{b}" for a, b in tort_pairs}
    tort_epithets = {n.split()[1] for n in tort_names if len(n.split()) >= 2}
    doc_binomials = {(m.group(1), m.group(3)) for u in units for m in BINOMIAL.finditer(u["text"])}
    for u in units:
        t = u["text"]
        cap = u.get("caption") or ""
        tort_here = bool(TORT_WORD.search(t) or TORT_RE.search(t) or any(a in t for a in tort_abbrev))
        if u["kind"] == "table_row":
            # PDF text loses table columns (a diet column can sit next to another animal's column): JATS tables only.
            if doc["kind"] != "jats" or OTHER_USE.search(cap) or NUTRIENT_CAPTION.search(cap):
                continue
            feed_here = STRONG_FEED.search(t) or STRONG_FEED.search(cap)
        else:
            toks = t.split()
            # PDF text: two-column pages and tables run together; keep only sentence-like units.
            if doc["kind"] == "txt" and (len(toks) > 60 or sum(bool(re.fullmatch(r"[\d.,%()<>=±-]+", x)) for x in toks) > 0.2 * len(toks)):
                continue
            feed_here = STRONG_FEED.search(t) and (tort_here or DIET_WORD.search(t))
        if not feed_here:
            continue
        cues = [m.start() for rx in (STRONG_FEED, TORT_WORD, TORT_RE) for m in rx.finditer(t)]
        unit_tort = None
        for m in TORT_RE.finditer(t + " " + cap):
            if m.group(2) not in STOP_EPITHET:
                unit_tort = m.group(1) + " " + m.group(2); break
        tortoise = unit_tort or tort
        found = []
        for m in BINOMIAL.finditer(t):
            g, ep = m.group(1), m.group(3)
            if g in STOP_GENUS or ep in STOP_EPITHET or g in TORTOISE_GENERA or ep in tort_epithets:
                continue
            found.append((g + " " + ep, g + " " + ep, m.span()))
        for m in ABBREV.finditer(t):
            letter, ep = m.group(1), m.group(2)
            if ep in STOP_EPITHET or (letter, ep) in tort_pairs or ep in tort_epithets:
                continue
            # Expand only to a binomial written out in full somewhere in the same document, and only if exactly one does
            # ("T. psilostachya" is Tournefortia here, not the last T-genus mentioned).
            full = {g for g, e in doc_binomials if g[0] == letter and e == ep and g not in TORTOISE_GENERA}
            if len(full) == 1:
                found.append((m.group(0), full.pop() + " " + ep, m.span()))
        for printed, name, span in found:
            # In sentences the name must stand within 12 words of the feeding word or the tortoise name.
            if u["kind"] == "sentence" and not any(len(t[min(c, span[0]):max(c, span[0])].split()) <= 12 for c in cues):
                continue
            rec = {"doc_id": doc["doc_id"], "name": name, "printed": printed, "genus_known": name.split()[0] in PLANT_GENERA,
                   "tortoise": tortoise, "locator": u["locator"],
                   "unit_kind": u["kind"], "quote": quote_for(t, span), "plant_part": part_near(t, span)}
            neg = (NEG.search(t) or (u["kind"] == "table_row" and NEG.search(cap)) or OTHER_USE.search(t)
                   or NOT_EATING.search(t) or (u["kind"] == "table_row" and NOT_EATING.search(cap)))
            if neg:
                review.append(dict(rec, reason="negation_or_toxicity_wording", match=neg.group(0)))
            elif not tortoise:
                review.append(dict(rec, reason="tortoise_species_not_identified", tortoise_counts=dict(list(tcounts.items())[:6])))
            else:
                typ, method = classify(t, cap, flags)
                rec.update(type=typ, method=method, expanded=printed != name)
                cands.append(rec)
    return cands, review, {"units": len(units), "tortoise": tort}


def main():
    docs_path, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    genera_file = out / "plant_genera.txt"
    if genera_file.exists():
        PLANT_GENERA.update(genera_file.read_text(encoding="utf-8").split())
    docs = [json.loads(l) for l in docs_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    cp = Checkpoint(out / "extract_checkpoint.jsonl")
    todo = [d for d in docs if not cp.done(d["doc_id"])]
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, min(workers, 6)), initializer=init_genera,
                                                initargs=(frozenset(PLANT_GENERA),)) as pool:
        futs = {pool.submit(process, d, out): d for d in todo}
        for f in concurrent.futures.as_completed(futs):
            d = futs[f]
            try:
                cands, review, info = f.result()
            except Exception as e:  # noqa: BLE001 - kept in the checkpoint, the document is retried on the next run
                cp.record(d["doc_id"], "retry", error=type(e).__name__ + ": " + str(e)[:200]); continue
            with (out / "candidates.jsonl").open("a", encoding="utf-8") as fc:
                for c in cands:
                    fc.write(json.dumps(c, ensure_ascii=False) + "\n")
            with (out / "review.jsonl").open("a", encoding="utf-8") as fr:
                for c in review:
                    fr.write(json.dumps(c, ensure_ascii=False) + "\n")
            cp.record(d["doc_id"], "ok", candidates=len(cands), review=len(review), **info)
    print(json.dumps(cp.summary()))


if __name__ == "__main__":
    main()
