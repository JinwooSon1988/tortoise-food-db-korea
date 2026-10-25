"""Bibliography -> open full texts for the existing candidate scan (never verification, never publication).

The incremental worker collects OpenAlex metadata (worker-output/worldwide-literature.json) but only titles and
abstracts were scanned. This step adds the missing link to full texts; it does not classify plants itself:

1. classify  (offline) every work: tortoise-related or not, and its access route -
   already_read (DOI or title already in an earlier full-text corpus), pmc_open_access (PMCID known),
   oa_pdf (open-access PDF URL), oa_landing_only, abstract_only, metadata_only  -> <work-dir>/access.json
2. resolve   tortoise works whose record lacks PMCID / OA-PDF fields: one OpenAlex single-work GET each (these cost
   0 credits, measured 2026-10-25), checkpointed.
3. fetch     at most --max-downloads new full texts per run: Europe PMC fullTextXML for PMCIDs (Crawl-delay 10 is
   honoured by polite_http) and open-access PDFs (robots.txt per host, pdftotext -layout). Checkpointed with cause
   and attempt count; a document is never downloaded twice, and is given up after 3 failed attempts.
4. list      the saved documents as <docs-out> (make_docs.py layout). scripts/build_evidence_candidates.py, already
   in the worker pipeline, reads worker-output/docs*.jsonl and separates name mentions from feeding context, resolves
   synonyms and writes the reviewer queue and unreviewed approval drafts.

Run (worker root): python -X utf8 scripts/evidence_corpus/fulltext_from_bibliography.py [--known-docs docs.jsonl ...]
                    [--max-resolve 100] [--max-downloads 30] [--offline]
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "batch_004"))
from discover_openalex import TITLE as TORTOISE, squash  # noqa: E402
from polite_http import Checkpoint, FetchError, HostPolicy, PoliteClient, RobotsDisallowed, run_tasks  # noqa: E402

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
OPENALEX_POLICY = HostPolicy(3.0, 1, "https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication",
                             "3 s between requests, as in scripts/research_bulk_leads.py")
ACCESS_ORDER = ["already_read", "pmc_open_access", "oa_pdf", "oa_landing_only", "abstract_only", "metadata_only"]


def pdf_to_text(pdf, txt):
    """pdftotext -layout (as batch 004), else PyMuPDF: the PowerShell worker has no pdftotext on PATH
    (it ships with Git Bash only), and every conversion failed with FileNotFoundError."""
    exe = shutil.which("pdftotext")
    if exe:
        subprocess.run([exe, "-layout", "-enc", "UTF-8", str(pdf), str(txt)], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "pdftotext"
    # Pages end with a form feed, as pdftotext writes them: extract.py numbers "PDF p.N" by splitting on it.
    try:
        import pymupdf  # the PDF is untrusted data and is only parsed for text
        with pymupdf.open(str(pdf)) as d:
            pages = [page.get_text("text", sort=True) for page in d]
        how = "pymupdf"
    except ImportError:
        from pypdf import PdfReader
        pages = [page.extract_text() or "" for page in PdfReader(str(pdf)).pages]
        how = "pypdf"
    txt.write_text("".join(p + chr(10) + chr(12) for p in pages), encoding="utf-8")
    return how


def bare_doi(doi):
    return (doi or "").lower().replace("https://doi.org/", "").strip() or None


def load_known(paths):
    dois, titles = set(), set()
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if bare_doi(d.get("doi")):
                dois.add(bare_doi(d["doi"]))
            t = squash(d.get("title") or "")
            if len(t) >= 25:
                titles.add(t[:60])
    return dois, titles


def tortoise_related(w):
    return bool(TORTOISE.search((w.get("title") or "") + " " + (w.get("abstract") or "")))


def access_of(w, known, resolved):
    dois, titles = known
    r = resolved.get(w.get("openalex_id") or "", {})
    if bare_doi(w.get("doi")) in dois or squash(w.get("title") or "")[:60] in titles:
        return "already_read"
    if w.get("pmcid") or r.get("pmcid"):
        return "pmc_open_access"
    if w.get("best_oa_pdf") or w.get("fulltext_url") or r.get("pdf_url"):
        return "oa_pdf"
    if w.get("is_oa") or r.get("is_oa"):
        return "oa_landing_only"
    return "abstract_only" if w.get("abstract") else "metadata_only"


def saved_path(work, d):
    """The saved document of a checkpoint row: its recorded path, else the same file name under this work dir
    (rows written before paths were absolute, or a worker-output folder copied to another place)."""
    p = Path(d.get("path") or "")
    if p.is_file():
        return p.resolve()
    q = work / ("xml" if d.get("kind") == "jats" else "txt") / p.name
    return q if p.name and q.is_file() else None


def classify_all(works, known, resolved):
    rows = []
    for w in works:
        rows.append({"openalex_id": w.get("openalex_id"), "doi": w.get("doi"), "title": w.get("title"),
                     "year": w.get("year"), "tortoise_related": tortoise_related(w),
                     "access": access_of(w, known, resolved),
                     "pmcid": w.get("pmcid") or resolved.get(w.get("openalex_id") or "", {}).get("pmcid"),
                     "pdf_url": w.get("best_oa_pdf") or w.get("fulltext_url") or resolved.get(w.get("openalex_id") or "", {}).get("pdf_url")})
    return rows


def summary_of(rows):
    by = Counter((r["access"], r["tortoise_related"]) for r in rows)
    return {"works": len(rows), "tortoise_related": sum(r["tortoise_related"] for r in rows),
            "access_all": {a: sum(v for (k, _), v in by.items() if k == a) for a in ACCESS_ORDER},
            "access_tortoise_related": {a: by[(a, True)] for a in ACCESS_ORDER},
            "full_text_obtainable_tortoise": by[("pmc_open_access", True)] + by[("oa_pdf", True)],
            "abstract_or_metadata_only_tortoise": by[("abstract_only", True)] + by[("metadata_only", True)] + by[("oa_landing_only", True)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bibliography", default="worker-output/worldwide-literature.json")
    ap.add_argument("--known-docs", nargs="*", default=[], help="docs.jsonl of corpora already read (batch 004 etc.)")
    ap.add_argument("--work-dir", default="worker-output/fulltext")
    ap.add_argument("--docs-out", default="worker-output/docs-fulltext.jsonl")
    ap.add_argument("--max-resolve", type=int, default=100)
    ap.add_argument("--max-downloads", type=int, default=30)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--offline", action="store_true", help="classify and rebuild the queue only; no network")
    args = ap.parse_args()
    work = Path(args.work_dir).resolve()  # absolute, so the document list stays valid when worker-output is copied
    for sub in ("xml", "raw", "txt"):
        (work / sub).mkdir(parents=True, exist_ok=True)
    works = json.loads(Path(args.bibliography).read_text(encoding="utf-8")).get("works", [])
    known = load_known(args.known_docs)
    client = PoliteClient(provenance=work / "requests.jsonl", timeout=60, retries=2,
                          policies={"api.openalex.org": OPENALEX_POLICY})

    # 2. resolve missing access fields with free single-work lookups
    rcp = Checkpoint(work / "resolve_checkpoint.jsonl")
    need = [w for w in works if tortoise_related(w) and not w.get("pmcid") and not w.get("best_oa_pdf")
            and "best_oa_pdf" not in w and w.get("openalex_id") and access_of(w, known, {}) != "already_read"
            and not rcp.done(w["openalex_id"])][:0 if args.offline else args.max_resolve]

    def resolve(wid):
        d, row = client.get_json(wid.replace("https://openalex.org/", "https://api.openalex.org/works/") +
                                 "?select=id,ids,best_oa_location,open_access", purpose="openalex single-work access lookup")
        return "ok", {"pmcid": ((d.get("ids") or {}).get("pmcid") or "").rsplit("/", 1)[-1] or None,
                      "pdf_url": (d.get("best_oa_location") or {}).get("pdf_url"),
                      "is_oa": (d.get("open_access") or {}).get("is_oa"), "credits": (row.get("ratelimit") or {}).get("x-ratelimit-credits-used")}
    if need:
        print("resolve", run_tasks(((w["openalex_id"], w["openalex_id"]) for w in need), resolve, rcp, workers=1), flush=True)
    resolved = {k: v for k, v in rcp.rows.items() if v.get("status") == "ok"}

    # 1. classify
    rows = classify_all(works, known, resolved)
    access = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "summary": summary_of(rows), "works": rows}
    (work / "access.json").write_text(json.dumps(access, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(access["summary"], ensure_ascii=False), flush=True)

    # 3. fetch new full texts (tortoise-related only, bounded per run)
    dcp = Checkpoint(work / "download_checkpoint.jsonl")
    todo = [r for r in rows if r["tortoise_related"] and r["access"] in ("pmc_open_access", "oa_pdf")
            and not dcp.done(r["openalex_id"])][:0 if args.offline else args.max_downloads]

    def download(wid):
        r = next(x for x in rows if x["openalex_id"] == wid)
        key = wid.rsplit("/", 1)[-1]
        if r["pmcid"]:
            try:
                body, prov = client.get(EPMC + f"{r['pmcid']}/fullTextXML", purpose="europepmc open-access full text")
                (work / "xml" / f"{r['pmcid']}.xml").write_bytes(body)
                return "ok", {"kind": "jats", "path": str(work / "xml" / f"{r['pmcid']}.xml"), "sha256": prov["sha256"]}
            except FetchError as e:
                if not r["pdf_url"]:
                    return ("final" if e.final else "retry"), {"error": str(e)[:200]}
        pdf, txt = work / "raw" / f"{key}.pdf", work / "txt" / f"{key}.txt"
        if pdf.is_file() and pdf.read_bytes()[:4] == b"%PDF":
            # Saved by an earlier attempt whose text conversion failed: convert again, do not download again.
            how = pdf_to_text(pdf, txt)
            return "ok", {"kind": "txt", "path": str(txt), "converter": how, "reused_download": True}
        try:
            # Some listed PDF URLs carry spaces or non-ASCII characters; send them percent-encoded.
            body, prov = client.get(urllib.parse.quote(r["pdf_url"], safe=":/?#[]@!$&'()*+,;=%~"), purpose="open-access pdf")
        except RobotsDisallowed:
            return "final", {"error": "robots.txt disallows"}
        except FetchError as e:
            return ("final" if e.final else "retry"), {"error": str(e)[:200]}
        if not body.startswith(b"%PDF"):
            return "final", {"error": "not a PDF (landing page or login wall)", "content_type": prov.get("content_type")}
        pdf.write_bytes(body)
        how = pdf_to_text(pdf, txt)
        return "ok", {"kind": "txt", "path": str(txt), "converter": how, "sha256": prov["sha256"], "final_url": prov["final_url"]}
    def download_counted(wid):
        # Failures keep their cause and attempt count; after 3 attempts a document is not tried again.
        attempts = dcp.rows.get(wid, {}).get("attempts", 0) + 1
        try:
            status, data = download(wid)
        except Exception as e:  # noqa: BLE001 - recorded in the checkpoint
            status, data = "retry", {"error": type(e).__name__ + ": " + str(e)[:200]}
        if status == "retry" and attempts >= 3:
            status = "final"
        return status, dict(data, attempts=attempts)
    if todo:
        print("downloads", run_tasks(((r["openalex_id"], r["openalex_id"]) for r in todo), download_counted, dcp,
                                     workers=args.workers), flush=True)

    # 4. document list for build_evidence_candidates.py
    by_id = {r["openalex_id"]: r for r in rows}
    docs = []
    for wid, d in dcp.rows.items():
        r = by_id.get(wid)
        if d.get("status") != "ok" or not r:
            continue
        path = saved_path(work, d)
        if not path:
            continue
        docs.append({"doc_id": "wl_" + wid.rsplit("/", 1)[-1], "path": str(path), "kind": d["kind"], "title": r["title"] or "",
                     "citation": f"{r['title']} ({r['year']})", "doi": bare_doi(r["doi"]),
                     "url": r["doi"] or (f"https://europepmc.org/article/PMC/{r['pmcid']}" if r["pmcid"] else r["pdf_url"]),
                     "source_class": "peer_reviewed",
                     "access": "Europe PMC open-access JATS" if d["kind"] == "jats" else "open-access PDF listed by OpenAlex"})
    out = Path(args.docs_out)
    tmp = out.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in docs), encoding="utf-8")
    tmp.replace(out)
    failures = Counter(str(v.get("error", ""))[:40] for v in dcp.rows.values() if v.get("status") != "ok")
    print(json.dumps({"access_tortoise_related": access["summary"]["access_tortoise_related"], "downloads": dcp.summary(),
                      "download_failures_by_cause": dict(failures.most_common(10)), "documents_listed": len(docs),
                      "docs_out": str(out), "http": client.stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
