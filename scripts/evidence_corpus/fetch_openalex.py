"""Collect open-access tortoise diet works from OpenAlex that are not in PMC, and download their OA PDFs (one at a time per host)."""
import concurrent.futures as cf, hashlib, json, pathlib, time, urllib.parse, urllib.request, urllib.robotparser

OUT = pathlib.Path.cwd() / "oa"  # run from a scratch directory, not the repository
OUT.mkdir(exist_ok=True); (OUT / "pdf").mkdir(exist_ok=True)
UA = "geobukbap-tortoise-food-db research (non-commercial; github.com/JinwooSon1988/tortoise-food-db-korea)"
ANIMALS = ["tortoise", "tortoises", "Testudo", "Agrionemys", "Gopherus", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys",
           "Aldabrachelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria", "Malacochersus", "Pyxis"]
TOPICS = ["diet", "feeding", "food", "forage", "faecal", "fecal", "scat", "herbivory", "frugivory", "seed dispersal", "food plants", "nutrition"]


def get(url, tries=3, timeout=90):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404, 410, 451):
                return None, ""
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(3 * (i + 1))
    return None, ""


def works():
    seen = {}
    for a in ANIMALS:
        for t in TOPICS:
            cursor = "*"
            while cursor:
                q = urllib.parse.urlencode({"filter": f"title_and_abstract.search:{a} {t},open_access.is_oa:true", "per-page": 200, "cursor": cursor,
                                            "select": "id,doi,title,publication_year,ids,open_access,best_oa_location,primary_location,type,authorships,abstract_inverted_index"})
                raw, _ = get("https://api.openalex.org/works?" + q)
                if not raw:
                    break
                d = json.loads(raw)
                for w in d["results"]:
                    seen[w["id"]] = w
                cursor = d["meta"].get("next_cursor") if d["results"] else None
                time.sleep(0.15)
        print(a, len(seen), flush=True)
    return list(seen.values())


robots = {}


def allowed(url):
    host = urllib.parse.urlsplit(url)
    base = f"{host.scheme}://{host.netloc}"
    if base not in robots:
        rp = urllib.robotparser.RobotFileParser(); raw, _ = get(base + "/robots.txt", tries=1, timeout=20)
        rp.parse((raw or b"").decode("utf-8", "ignore").splitlines()); robots[base] = rp
    return robots[base].can_fetch(UA, url)


def main():
    p = OUT / "works.json"
    if not p.exists():
        p.write_text(json.dumps(works(), ensure_ascii=False), encoding="utf-8")
    ws = json.loads(p.read_text(encoding="utf-8"))
    todo = []
    for w in ws:
        if (w.get("ids") or {}).get("pmcid"):
            continue  # covered by Europe PMC XML
        loc = w.get("best_oa_location") or {}
        url = loc.get("pdf_url")
        if url:
            todo.append((w["id"], url))
    by_host = {}
    for wid, url in todo:
        by_host.setdefault(urllib.parse.urlsplit(url).netloc, []).append((wid, url))
    log = []

    def host_worker(items):
        out = []
        for wid, url in items:
            f = OUT / "pdf" / (hashlib.sha1(wid.encode()).hexdigest()[:16] + ".pdf")
            if f.exists():
                out.append((wid, url, "cached")); continue
            if not allowed(url):
                out.append((wid, url, "robots_disallow")); continue
            raw, ctype = get(url)
            if raw and raw[:4] == b"%PDF":
                f.write_bytes(raw); out.append((wid, url, "ok"))
            else:
                out.append((wid, url, "not_pdf_or_blocked"))
            time.sleep(1.0)
        return out

    with cf.ThreadPoolExecutor(8) as ex:
        for res in ex.map(host_worker, by_host.values()):
            log += res
    (OUT / "download_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=0), encoding="utf-8")
    from collections import Counter
    print("works", len(ws), "non-PMC with pdf url", len(todo), Counter(s for *_, s in log))


if __name__ == "__main__":
    main()
