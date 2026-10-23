"""Batch 004 discovery outside PubMed Central: open-access tortoise diet papers and theses found through OpenAlex.

OpenAlex works search (open access only), one query per tortoise genus / language; a work is kept only if its title
names tortoises or a tortoise genus and OpenAlex lists an open-access PDF. PDFs are downloaded from the hosting site
(robots.txt checked per host, one request per second per host) and converted with pdftotext -layout. OpenAlex requests
are spaced 3 s apart (the interval this repository uses for OpenAlex). Output in the layout make_docs/extract read:
<out>/docs.jsonl (kind "txt"), <out>/raw/*.pdf, <out>/txt/*.txt. Checkpoints make the run resumable.
Downloaded PDFs are untrusted data: they are only parsed by pdftotext, never opened or executed otherwise.
Run: python -X utf8 -I discover_openalex.py <out dir> <existing docs.jsonl> [workers]
"""
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from polite_http import Checkpoint, HostPolicy, PoliteClient, run_tasks  # noqa: E402

QUERIES = ["tortoise diet", "tortoise feeding ecology", "tortoise faecal analysis", "tortoise food plants", "tortoise herbivory",
           "Testudo diet", "Testudo hermanni feeding", "Testudo graeca diet", "Gopherus diet", "Gopherus agassizii forage",
           "Chelonoidis diet", "Geochelone diet", "Centrochelys sulcata diet", "Stigmochelys pardalis diet", "Kinixys diet",
           "Astrochelys diet", "Aldabrachelys diet", "Indotestudo diet", "Homopus diet", "Psammobates diet", "Chersina diet",
           "Manouria diet", "Agrionemys horsfieldii diet", "dieta tortuga terrestre", "dieta jabuti", "alimentação jabuti",
           "régime alimentaire tortue", "alimentation tortue terrestre", "kaplumbağa beslenme"]
TITLE = re.compile(r"\b(tortoises?|testudo|gopherus|chelonoidis|geochelone|centrochelys|stigmochelys|kinixys|astrochelys|aldabrachelys|"
                   r"dipsochelys|indotestudo|homopus|chersobius|psammobates|chersina|manouria|malacochersus|pyxis|agrionemys|"
                   r"testudinidae|tortugas?|jabutis?|jabotis?|tortues?|kaplumba[gğ]a)\b", re.I)


def squash(s):
    """Lower-case letters and digits only, to compare titles across citation styles."""
    return re.sub(r"[^0-9a-z]", "", s.lower())


def citation(w):
    names = [a.get("author", {}).get("display_name") for a in w.get("authorships") or [] if a.get("author")]
    auth = ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")
    venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    return " ".join(p for p in [auth, f"({w.get('publication_year')})" if w.get("publication_year") else "", (w.get("title") or "").rstrip("."), venue] if p)


def main():
    out, existing = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    (out / "raw").mkdir(exist_ok=True); (out / "txt").mkdir(exist_ok=True)
    client = PoliteClient(provenance=out / "requests.jsonl", timeout=60, policies={
        "api.openalex.org": HostPolicy(3.0, 1, "https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication",
                                       "3 s between requests, as in scripts/research_bulk_leads.py")})
    have_doi, have_text = set(), []
    for line in existing.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            if d.get("doi"):
                have_doi.add(d["doi"].lower().replace("https://doi.org/", ""))
            have_text.append(squash((d.get("citation") or "") + " " + (d.get("title") or "")))
    seen_before = lambda title: len(squash(title)) >= 25 and any(squash(title)[:60] in t for t in have_text)

    qcp = Checkpoint(out / "search_checkpoint.jsonl")
    def search(q):
        works = []
        for page in (1, 2):
            u = "https://api.openalex.org/works?" + urllib.parse.urlencode({
                "search": q, "filter": "is_oa:true", "per-page": 100, "page": page,
                "select": "id,doi,title,publication_year,type,language,authorships,primary_location,best_oa_location"})
            d, _ = client.get_json(u, purpose="openalex open-access search")
            works += d.get("results", [])
            if len(d.get("results", [])) < 100:
                break
        return "ok", {"works": works}
    print("searches", run_tasks(((q, q) for q in QUERIES), search, qcp, workers=1), flush=True)

    keep = {}
    for r in qcp.rows.values():
        for w in r.get("works", []):
            pdf = (w.get("best_oa_location") or {}).get("pdf_url")
            doi = (w.get("doi") or "").lower().replace("https://doi.org/", "")
            if not pdf or not TITLE.search(w.get("title") or "") or (doi and doi in have_doi) or seen_before(w.get("title") or ""):
                continue
            keep[w["id"].rsplit("/", 1)[-1]] = w
    print(len(keep), "open-access PDFs about tortoises not saved before", flush=True)

    dcp = Checkpoint(out / "download_checkpoint.jsonl")
    def download(wid):
        w = keep[wid]
        body, prov = client.get(w["best_oa_location"]["pdf_url"], purpose="open-access pdf")
        if not body.startswith(b"%PDF"):
            return "final", {"error": "not a PDF (landing page or login wall)", "content_type": prov.get("content_type")}
        pdf = out / "raw" / f"{wid}.pdf"; pdf.write_bytes(body)
        txt = out / "txt" / f"{wid}.txt"
        subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(txt)], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "ok", {"sha256": prov["sha256"], "final_url": prov["final_url"]}
    print("downloads", run_tasks(((k, k) for k in keep), download, dcp, workers=workers), flush=True)

    docs = []
    for wid, w in keep.items():
        r = dcp.rows.get(wid, {})
        if r.get("status") != "ok" or not (out / "txt" / f"{wid}.txt").exists():
            continue
        loc = w.get("best_oa_location") or {}
        docs.append({"doc_id": "oa_" + wid, "path": str(out / "txt" / f"{wid}.txt"), "kind": "txt", "citation": citation(w),
                     "title": w.get("title") or "", "doi": (w.get("doi") or "").replace("https://doi.org/", "") or None,
                     "url": w.get("doi") or loc.get("landing_page_url") or loc.get("pdf_url"),
                     "source_class": "thesis" if w.get("type") == "dissertation" else "peer_reviewed",
                     "access": "open-access PDF listed by OpenAlex (" + (loc.get("license") or "license not stated") + ")",
                     "license": loc.get("license"), "language": w.get("language")})
    (out / "docs.jsonl").write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in docs), encoding="utf-8")
    print(json.dumps({"kept": len(keep), "documents": len(docs), "download": dcp.summary(), "requests": client.stats}))


if __name__ == "__main__":
    main()
