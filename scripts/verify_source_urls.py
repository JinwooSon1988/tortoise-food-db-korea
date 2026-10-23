#!/usr/bin/env python3
"""Check every source URL shown on catalog detail pages (catalog shards, Batch 002 site index, batch files).

Requests go through polite_http (robots.txt, per-host spacing, retries, provenance). Each URL gets one class:
  ok                - 2xx after redirects
  host_refuses_bots - 401/403/429 left after retries, or robots.txt disallows checking (the link may work in a browser)
  broken            - 404/410 or the host cannot be reached
  error             - other HTTP status
Resumable: results are kept in <out dir>/checkpoint.jsonl. Writes <out dir>/source-url-check.json (counts and the URLs
that are not ok, with the pages that cite them).
Run: python -X utf8 scripts/verify_source_urls.py <out dir> [workers]
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from polite_http import Checkpoint, FetchError, PoliteClient, RobotsDisallowed, run_tasks  # noqa: E402


def cited_urls():
    urls = {}
    for f in sorted(glob.glob(str(ROOT / "data/plant-catalog/taxa-*.json"))):
        for r in json.loads(Path(f).read_text(encoding="utf-8"))["records"]:
            for e in r["feeding_evidence"]:
                if str(e.get("url") or "").startswith("http"):
                    urls.setdefault(e["url"], set()).add(r["id"])
    for f in sorted((ROOT / "data/catalog-evidence").glob("batch-[0-9][0-9][0-9]-*.json")):
        for s in json.loads(f.read_text(encoding="utf-8")).get("sources", []):
            if str(s.get("url") or "").startswith("http"):
                urls.setdefault(s["url"], set()).add(f.stem)
    b2 = json.loads((ROOT / "data/catalog-evidence/batch-002-site-index.json").read_text(encoding="utf-8"))
    src = b2.get("sources") or []
    for s in (src.values() if isinstance(src, dict) else src):
        if str(s.get("url") or "").startswith("http"):
            urls.setdefault(s["url"], set()).add("batch-002")
    return urls


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    client = PoliteClient(provenance=out / "requests.jsonl", timeout=30, retries=2)
    cp = Checkpoint(out / "checkpoint.jsonl")
    urls = cited_urls()

    def check(url):
        try:
            _, row = client.get(url, purpose="source link check")
            return "ok", {"class": "ok", "http_status": row["status"], "final_url": row["final_url"]}
        except RobotsDisallowed:
            return "final", {"class": "host_refuses_bots", "http_status": None, "note": "robots.txt disallows automated checks"}
        except FetchError as e:
            cls = ("host_refuses_bots" if e.status in (401, 403, 429) else "broken" if e.status in (404, 410) or e.status is None
                   else "error")
            return "final", {"class": cls, "http_status": e.status}

    run_tasks(((u, u) for u in sorted(urls)), check, cp, workers=workers)
    rows = {u: cp.rows[u] for u in urls if u in cp.rows}
    counts = {}
    for r in rows.values():
        counts[r.get("class", r["status"])] = counts.get(r.get("class", r["status"]), 0) + 1
    report = {"urls": len(urls), "checked": len(rows), "by_class": counts,
              "not_ok": [{"url": u, "class": r.get("class"), "http_status": r.get("http_status"), "cited_by": sorted(urls[u])[:10]}
                         for u, r in sorted(rows.items()) if r.get("class") != "ok"],
              "requests": client.stats}
    (out / "source-url-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("urls", "checked", "by_class", "requests")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
