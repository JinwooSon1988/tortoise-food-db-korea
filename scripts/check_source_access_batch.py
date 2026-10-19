#!/usr/bin/env python3
"""Batch open-access check and full-text collection for the sources in the corpus inventory.

Run: python scripts/check_source_access_batch.py --cache <dir outside the repo> [--workers 4]
     (reads data/evidence_corpus_inventory_20261019.json, writes data/source_access_check_20261019.json)

Phase 1  access: every unique DOI is looked up in OpenAlex (open-access status, OA locations, PMCID); every
         URL-only source gets one GET of its landing page. HTTP errors, 403s and timeouts are recorded as they are.
Phase 2  full text: for sources linked to a published plant, the full text is fetched only from open routes
         (Europe PMC full-text XML for a PMCID, or an OA PDF/HTML location OpenAlex lists). Nothing behind a login,
         paywall or bot check is bypassed. Texts are cached outside the repository; only metadata is written here.
Phase 3  passages: in each obtained text, sentences naming the plant genus are located with their section and
         page where available. A located passage is a machine pointer for review, not a verified feeding record.
"""
import argparse, gzip, hashlib, io, json, re, sys, time, threading, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "data/evidence_corpus_inventory_20261019.json"
OUT = ROOT / "data/source_access_check_20261019.json"
UA = "tortoise-food-db-korea source access check (research; respects access restrictions)"
_lock = threading.Lock()
_last = [0.0]


def polite(min_gap):
    with _lock:
        wait = _last[0] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


def fetch(url, timeout=30, accept=None, min_gap=0.15, max_bytes=40_000_000):
    polite(min_gap)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept or "*/*", "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(max_bytes)
            if r.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            return {"status": r.status, "final_url": r.geturl(), "content_type": r.headers.get("Content-Type", ""), "body": body}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": f"HTTP {e.code}"}
    except Exception as e:  # timeouts, DNS, TLS: recorded, not retried around restrictions
        return {"status": None, "error": type(e).__name__ + ": " + str(e)[:160]}


def openalex(doi):
    r = fetch("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi, safe="/:()"), accept="application/json")
    if r.get("status") != 200:
        return {"lookup": "failed", "error": r.get("error") or f"HTTP {r.get('status')}"}
    w = json.loads(r["body"])
    oa = w.get("open_access") or {}
    locs = []
    for l in w.get("locations") or []:
        if l.get("is_oa"):
            locs.append({"pdf_url": l.get("pdf_url"), "landing_page_url": l.get("landing_page_url"),
                         "version": l.get("version"), "license": l.get("license"),
                         "host": ((l.get("source") or {}).get("display_name"))})
    ids = w.get("ids") or {}
    pmcid = (ids.get("pmcid") or "").rsplit("/", 1)[-1] or None
    return {"lookup": "ok", "title": w.get("title"), "year": w.get("publication_year"),
            "authors": [a["author"]["display_name"] for a in (w.get("authorships") or [])][:8],
            "is_oa": oa.get("is_oa"), "oa_status": oa.get("oa_status"), "oa_locations": locs, "pmcid": pmcid}


def landing(url):
    r = fetch(url if url.startswith("http") else "https://" + url, accept="text/html,application/pdf", max_bytes=2_000_000)
    return {"lookup": "ok" if r.get("status") == 200 else "failed", "http_status": r.get("status"),
            "content_type": r.get("content_type"), "error": r.get("error"), "final_url": r.get("final_url")}


def pdf_text(body):
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(body))
    return [(p.extract_text() or "") for p in reader.pages]


def xml_text(body):
    t = body.decode("utf-8", "ignore")
    out, sec = [], "front"
    for m in re.finditer(r"<sec[^>]*>\s*<title>(.*?)</title>|<p[^>]*>(.*?)</p>|<table-wrap[^>]*>(.*?)</table-wrap>", t, re.S):
        if m.group(1):
            sec = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        else:
            txt = re.sub(r"<[^>]+>", " ", m.group(2) or m.group(3) or "")
            out.append((sec, re.sub(r"\s+", " ", txt).strip()))
    return out


def get_fulltext(src, acc, cache):
    """Open routes only. Returns metadata and the cached text path."""
    tried = []
    oa = acc.get("openalex") or {}
    if oa.get("pmcid"):
        r = fetch(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{oa['pmcid']}/fullTextXML", accept="application/xml")
        tried.append({"route": "europepmc_fulltext_xml", "status": r.get("status"), "error": r.get("error")})
        if r.get("status") == 200 and b"<body" in r["body"]:
            parts = xml_text(r["body"])
            return save(cache, src, "europepmc_fulltext_xml", [{"section": s, "text": t} for s, t in parts], tried)
    for loc in oa.get("oa_locations") or []:
        for url in [loc.get("pdf_url"), loc.get("landing_page_url")]:
            if not url:
                continue
            r = fetch(url, accept="application/pdf,text/html", timeout=45)
            ct = (r.get("content_type") or "").lower()
            tried.append({"route": "openalex_oa_location", "url": url, "status": r.get("status"), "content_type": ct, "error": r.get("error")})
            if r.get("status") != 200:
                continue
            if "pdf" in ct or r["body"][:4] == b"%PDF":
                try:
                    pages = pdf_text(r["body"])
                except Exception as e:
                    tried[-1]["error"] = "pdf parse: " + type(e).__name__
                    continue
                if sum(len(p) for p in pages) > 2000:
                    return save(cache, src, "oa_pdf", [{"page": i + 1, "text": p} for i, p in enumerate(pages)], tried)
                tried[-1]["error"] = "pdf without extractable text"
            elif "html" in ct:
                html = r["body"].decode("utf-8", "ignore")
                if re.search(r"captcha|are you a robot|cf-chl|Just a moment", html, re.I):
                    tried[-1]["error"] = "bot check page; not bypassed"
                    continue
                body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
                if len(text) > 15000 and re.search(r"\b(Methods|Results|Discussion)\b", text):
                    return save(cache, src, "oa_html", [{"section": "html", "text": text}], tried)
                tried[-1]["error"] = "landing page without article full text"
    return {"obtained": False, "attempts": tried}


def save(cache, src, route, parts, tried):
    blob = json.dumps(parts, ensure_ascii=False)
    h = hashlib.sha256(blob.encode()).hexdigest()
    p = Path(cache) / (hashlib.sha1(src.encode()).hexdigest()[:16] + ".json")
    p.write_text(blob, encoding="utf-8")
    return {"obtained": True, "route": route, "chars": sum(len(x["text"]) for x in parts), "units": len(parts),
            "sha256": h, "cache_file": p.name, "attempts": tried}


SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def passages(parts, genus_names, limit=6):
    out = []
    pats = [re.compile(r"\b" + re.escape(g) + r"\b") for g in genus_names if g]
    for unit in parts:
        for s in SENT.split(unit["text"]):
            if any(p.search(s) for p in pats):
                out.append({k: unit[k] for k in ("page", "section") if k in unit} | {"text": re.sub(r"\s+", " ", s)[:400]})
                if len(out) >= limit:
                    return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--leads", help="paper_leads.jsonl to include in the access check (candidates only)")
    a = ap.parse_args()
    Path(a.cache).mkdir(parents=True, exist_ok=True)
    inv = json.loads(INV.read_text(encoding="utf-8"))
    plants = {p["id"]: p for p in json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))}
    srcs = {s["key"]: s for s in inv["sources"]}
    leads = {}
    if a.leads and Path(a.leads).exists():
        for line in Path(a.leads).read_text(encoding="utf-8").splitlines():
            if line.strip():
                l = json.loads(line)
                if l.get("doi"):
                    leads.setdefault("doi:" + l["doi"].lower(), l)

    keys = sorted(set(srcs) | set(leads))
    t0 = time.time()

    def access(k):
        if k.startswith("doi:"):
            return k, {"openalex": openalex(k[4:])}
        return k, {"landing": landing(k[4:])}

    with ThreadPoolExecutor(a.workers) as ex:
        acc = dict(ex.map(access, keys))
    print(f"phase 1: {len(keys)} access lookups in {time.time() - t0:.0f}s", flush=True)

    # Phase 2: reviewed sources linked to a published plant only; leads stay candidates.
    targets = [k for k in srcs if srcs[k]["plant_ids"] and (acc[k].get("openalex") or {}).get("lookup") == "ok"
               and ((acc[k]["openalex"].get("is_oa")) or acc[k]["openalex"].get("pmcid"))]

    def ft(k):
        return k, get_fulltext(k, acc[k], a.cache)

    with ThreadPoolExecutor(min(a.workers, 3)) as ex:
        fts = dict(ex.map(ft, targets))
    print(f"phase 2: {len(targets)} full-text attempts, {sum(v['obtained'] for v in fts.values())} obtained", flush=True)

    for k, meta in fts.items():
        if not meta["obtained"]:
            continue
        parts = json.loads((Path(a.cache) / meta["cache_file"]).read_text(encoding="utf-8"))
        meta["passages"] = {}
        for pid in srcs[k]["plant_ids"]:
            sci = (plants.get(pid) or {}).get("scientific", "")
            words = sci.split()
            names = [" ".join(words[:2])] if len(words) >= 2 else []
            if words:
                names += [words[0], words[0][0] + ". " + words[1] if len(words) > 1 else None]
            meta["passages"][pid] = passages(parts, [n for n in names if n])

    records = []
    for k in keys:
        rec = {"key": k, "kind": "reviewed_source" if k in srcs else "bibliographic_lead",
               "plant_ids": srcs[k]["plant_ids"] if k in srcs else [], "levels": srcs[k]["levels"] if k in srcs else ["lead"]}
        rec.update(acc[k])
        if k in fts:
            rec["fulltext"] = fts[k]
        records.append(rec)

    def cls(r):
        o = r.get("openalex")
        if o is not None:
            if o["lookup"] != "ok":
                return "metadata_lookup_failed"
            if r.get("fulltext", {}).get("obtained"):
                return "fulltext_obtained_open_route"
            if r.get("fulltext"):
                return "oa_listed_but_fulltext_not_obtained"
            return "open_access_listed" if o.get("is_oa") else "closed_or_subscription"
        l = r["landing"]
        if l["http_status"] == 200:
            return "landing_page_reachable"
        if l["http_status"] in (401, 403):
            return "landing_page_forbidden"
        return "landing_page_failed"

    summary = {}
    for r in records:
        r["access_class"] = cls(r)
        summary.setdefault(r["kind"], {}).setdefault(r["access_class"], 0)
        summary[r["kind"]][r["access_class"]] += 1
    out = {"schema_version": "1.0", "checked_at": time.strftime("%Y-%m-%d"),
           "scope": "Access and open full-text collection only. A located passage is a pointer for review, not verification.",
           "rules": ["No login, paywall, bot check or robots restriction is bypassed; failures are recorded as failures.",
                     "Bibliographic leads are access-checked only; their full texts are not collected or reviewed here.",
                     "Full texts are cached outside the repository; only hashes, sizes and short located passages are stored."],
           "counts": {"lookups": len(records), "reviewed_sources": len(srcs), "leads_with_doi": len(leads),
                      "fulltext_attempts": len(targets), "fulltext_obtained": sum(v["obtained"] for v in fts.values()),
                      "by_class": summary},
           "records": records}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
