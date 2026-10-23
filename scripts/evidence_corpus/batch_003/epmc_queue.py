"""Batch 003 work queue: search Europe PMC for every catalog species together with any land-tortoise term.
Restartable: results are appended to queue_results.jsonl and taxa already present are skipped; failures are kept in
queue_checkpoint.jsonl (transient ones run again on the next start). Requests go through scripts/polite_http.py:
robots.txt, Europe PMC request spacing, Retry-After on 429, a provenance log (requests.jsonl) and a bounded pool.
Run: python -X utf8 epmc_queue.py <search.json> <out dir> [workers]
"""
import json, sys, threading, time, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from polite_http import PoliteClient, Checkpoint, run_tasks  # noqa: E402

SEARCH, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
RES, LOG = OUT / "queue_results.jsonl", OUT / "queue_log.txt"
GENERA = ["Testudo", "Agrionemys", "Gopherus", "Xerobates", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys",
          "Aldabrachelys", "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria",
          "Malacochersus", "Pyxis", "Testudinidae"]
TORT = "(tortoise OR tortoises OR " + " OR ".join(GENERA) + ")"
FIELDS = ("id", "source", "pmid", "pmcid", "doi", "title", "authorString", "pubYear", "journalTitle", "isOpenAccess", "inEPMC", "hasTextMinedTerms")
client = PoliteClient(provenance=OUT / "requests.jsonl")
cp = Checkpoint(OUT / "queue_checkpoint.jsonl")
lock = threading.Lock()


def log(m):
    with lock, open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def search(task):
    tid, name = task
    qs = '"%s" AND %s' % (name, TORT)
    u = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": qs, "format": "json", "pageSize": 25, "resultType": "lite"})
    d, prov = client.get_json(u, purpose="europepmc species x tortoise search")
    hits = [{k: x.get(k) for k in FIELDS} for x in d.get("resultList", {}).get("result", [])]
    with lock, open(RES, "a", encoding="utf-8") as f:
        f.write(json.dumps({"taxon_id": tid, "scientific": name, "query": qs, "hit_count": d.get("hitCount", 0), "hits": hits,
                            "searched": time.strftime("%Y-%m-%d"), "request_sha256": prov["sha256"]}, ensure_ascii=False) + "\n")
    return "ok", {"hit_count": d.get("hitCount", 0)}


if __name__ == "__main__":
    done = set()
    if RES.exists():
        for l in RES.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(l)["taxon_id"])
            except (ValueError, KeyError):
                pass
    rows = json.loads(SEARCH.read_text(encoding="utf-8"))["rows"]
    todo = [(r[0], (r[0], r[1])) for r in rows if r[0] not in done]
    log(f"start: {len(todo)} to do, {len(done)} already done, workers={WORKERS}")
    summary = run_tasks(todo, search, cp, workers=WORKERS, progress=lambda n, s: log(f"progress {n} {s} {client.stats}"))
    log(f"done {summary} {client.stats}")
