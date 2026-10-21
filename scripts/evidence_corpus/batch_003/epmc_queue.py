"""Batch 003 work queue: search Europe PMC for every catalog species together with any land-tortoise term.
Restartable: results are appended to queue_results.jsonl and taxa already present are skipped. Concurrency adapts:
it starts at START workers, halves on HTTP 429/5xx or timeouts and slowly grows back while requests succeed.
Run: python -X utf8 epmc_queue.py <search.json> <out dir>
"""
import json, sys, time, threading, urllib.request, urllib.parse, queue, random
from pathlib import Path

SEARCH, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
RES, LOG = OUT / "queue_results.jsonl", OUT / "queue_log.txt"
GENERA = ["Testudo", "Agrionemys", "Gopherus", "Xerobates", "Chelonoidis", "Geochelone", "Centrochelys", "Stigmochelys", "Astrochelys",
          "Aldabrachelys", "Dipsochelys", "Kinixys", "Homopus", "Chersobius", "Chersina", "Psammobates", "Indotestudo", "Manouria",
          "Malacochersus", "Pyxis", "Testudinidae"]
TORT = "(tortoise OR tortoises OR " + " OR ".join(GENERA) + ")"
UA = "geobukbap-evidence-research/0.3 (+https://jinwooson1988.github.io/tortoise-food-db-korea/)"
rows = json.loads(SEARCH.read_text(encoding="utf-8"))["rows"]
done = set()
if RES.exists():
    for l in RES.read_text(encoding="utf-8").splitlines():
        try:
            done.add(json.loads(l)["taxon_id"])
        except Exception:
            pass
todo = [(r[0], r[1]) for r in rows if r[0] not in done]
q = queue.Queue(); [q.put(t) for t in todo]
lock = threading.Lock(); state = {"workers": 8, "ok": 0, "err": 0, "retry": 0, "active": 0}
MAXW, START = 16, 8
def log(m):
    with lock, open(LOG, "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")
def fetch(name):
    qs = '"%s" AND %s' % (name, TORT)
    u = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
        {"query": qs, "format": "json", "pageSize": 25, "resultType": "lite"})
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=40) as r:
        return qs, json.load(r)
def worker(i):
    while True:
        with lock:
            if i >= state["workers"]:
                pass
        if i >= state["workers"]:
            time.sleep(2); 
            if q.empty(): return
            continue
        try:
            tid, name = q.get_nowait()
        except queue.Empty:
            return
        for attempt in range(5):
            try:
                qs, d = fetch(name)
                hits = [{k: x.get(k) for k in ("id", "source", "pmid", "pmcid", "doi", "title", "authorString", "pubYear", "journalTitle", "isOpenAccess", "inEPMC", "hasTextMinedTerms")}
                        for x in d.get("resultList", {}).get("result", [])]
                with lock:
                    with open(RES, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"taxon_id": tid, "scientific": name, "query": qs, "hit_count": d.get("hitCount", 0), "hits": hits,
                                            "searched": time.strftime("%Y-%m-%d")}, ensure_ascii=False) + "\n")
                    state["ok"] += 1
                    if state["ok"] % 100 == 0 and state["workers"] < MAXW:
                        state["workers"] += 1
                break
            except Exception as e:
                code = getattr(e, "code", None)
                with lock:
                    state["retry"] += 1
                    if code in (429, 500, 502, 503, 504) or "timed out" in str(e):
                        state["workers"] = max(1, state["workers"] // 2)
                log(f"retry {attempt} {name}: {e}")
                time.sleep(2 ** attempt + random.random())
        else:
            with lock:
                state["err"] += 1
                with open(OUT / "queue_failed.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps({"taxon_id": tid, "scientific": name}) + "\n")
        q.task_done()
log(f"start: {len(todo)} to do, {len(done)} already done")
ts = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(MAXW)]
[t.start() for t in ts]
while any(t.is_alive() for t in ts):
    time.sleep(60); log(f"progress ok={state['ok']} err={state['err']} retry={state['retry']} workers={state['workers']} left={q.qsize()}")
log(f"done ok={state['ok']} err={state['err']} retry={state['retry']}")
