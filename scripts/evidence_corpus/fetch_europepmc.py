"""Collect the tortoise diet literature from Europe PMC (metadata + abstracts, then open-access full-text XML). Usage: python fetch_europepmc.py [fulltext]

Polite use: one search stream with cursorMark paging, then <=4 parallel full-text requests with a pause.
"""
import concurrent.futures as cf, json, pathlib, time, urllib.parse, urllib.request

OUT = pathlib.Path.cwd()  # run from a scratch directory, not the repository
GENERA = ["Testudo", "Agrionemys", "Gopherus", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys", "Aldabrachelys",
          "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria", "Malacochersus", "Pyxis", "Cylindraspis"]
ANIMAL = " OR ".join(['"tortoise"', '"tortoises"'] + [f'"{g}"' for g in GENERA])
DIET = ('diet OR diets OR feeding OR forage OR foraging OR food OR foods OR fecal OR faecal OR feces OR faeces OR scat OR scats OR herbivory '
        'OR herbivore OR frugivory OR "seed dispersal" OR endozoochory OR browsing OR grazing OR consumed OR eaten OR nutrition OR husbandry')
import sys
QUERY = f"(TITLE_ABS:({ANIMAL})) AND (TITLE_ABS:({DIET}))"
if len(sys.argv) > 1 and sys.argv[1] == "fulltext":
    QUERY = f"({ANIMAL}) AND (diet OR feeding OR faecal OR fecal OR scat OR forage OR eaten OR consumed) AND OPEN_ACCESS:y"
    OUT = OUT / "ft"; OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "geobukbap-tortoise-food-db research (non-commercial; github.com/JinwooSon1988/tortoise-food-db-korea)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 400):
                return None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def search():
    out, cursor = [], "*"
    while True:
        q = urllib.parse.urlencode({"query": QUERY, "resultType": "core", "format": "json", "pageSize": 1000, "cursorMark": cursor})
        d = json.loads(get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + q))
        res = d["resultList"]["result"]
        out += res
        print("search", len(out), "/", d.get("hitCount"), flush=True)
        if not res or d.get("nextCursorMark") in (None, cursor):
            break
        cursor = d["nextCursorMark"]
        time.sleep(1)
    return out


def main():
    meta_path = OUT / "meta.jsonl"
    if not meta_path.exists():
        rows = search()
        keep = ("id", "source", "pmid", "pmcid", "doi", "title", "authorString", "pubYear", "journalInfo", "abstractText", "isOpenAccess", "license",
                "keywordList", "pubTypeList", "inEPMC", "hasPDF")
        with meta_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps({k: r.get(k) for k in keep}, ensure_ascii=False) + "\n")
    meta = [json.loads(l) for l in meta_path.read_text(encoding="utf-8").splitlines()]
    xml = OUT / "xml"; xml.mkdir(exist_ok=True)
    todo = [m["pmcid"] for m in meta if m.get("pmcid") and m.get("isOpenAccess") == "Y" and m.get("inEPMC") == "Y" and not (xml / f"{m['pmcid']}.xml").exists()]

    def one(pmcid):
        x = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
        if x:
            (xml / f"{pmcid}.xml").write_bytes(x)
        time.sleep(0.3)
        return bool(x)

    with cf.ThreadPoolExecutor(4) as ex:
        got = sum(ex.map(one, todo))
    print("records", len(meta), "full text fetched now", got, "of", len(todo), "total xml", len(list(xml.glob("*.xml"))))


if __name__ == "__main__":
    main()
