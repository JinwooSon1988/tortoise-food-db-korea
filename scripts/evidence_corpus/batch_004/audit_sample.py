"""Precision audit for batch 004: print a random sample of linked records with the surrounding text, for a reviewer
to mark each as correct (the source says this tortoise ate / was fed this plant) or not.
Run: python -X utf8 -I audit_sample.py <batch json> <extract dir> [<extract dir> ...] --n 120 --seed 4 > sample.txt
Marks go in a JSONL file ({"i": n, "ok": true|false, "why": "..."}) and are counted with --score <marks.jsonl>.
"""
import argparse
import json
import random
import re
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path)
    ap.add_argument("dirs", nargs="+", type=Path)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--score", type=Path)
    ap.add_argument("--quotes", type=Path, help="records_with_quotes.jsonl.gz: show the context of the quoted passage")
    a = ap.parse_args()
    quotes = {}
    if a.quotes:
        import gzip
        with gzip.open(a.quotes, "rt", encoding="utf-8") as f:
            for line in f:
                q = json.loads(line)
                quotes[(q["source_key"], q["reported_name"], q["tortoise"], q["type"])] = q["quote"]
    b = json.loads(a.batch.read_text(encoding="utf-8"))
    rng = random.Random(a.seed)
    sample = rng.sample(b["records"], min(a.n, len(b["records"])))
    if a.score:
        marks = [json.loads(l) for l in a.score.read_text(encoding="utf-8").splitlines() if l.strip()]
        ok = sum(1 for m in marks if m["ok"])
        print(json.dumps({"audited": len(marks), "correct": ok, "precision": round(ok / len(marks), 3) if marks else None,
                          "errors": [m for m in marks if not m["ok"]]}, ensure_ascii=False, indent=1))
        return
    for i, r in enumerate(sample):
        doc = r["source_key"][3:]
        text = next((d / "text" / (doc + ".txt") for d in a.dirs if (d / "text" / (doc + ".txt")).exists()), None)
        ctx = ""
        if text:
            t = text.read_text(encoding="utf-8")
            name = r.get("reported_as") or r["reported_name"]
            q = quotes.get((r["source_key"], r["reported_name"], r["tortoise"], r["type"]))
            flat = " ".join(t.split())
            pos = flat.find(" ".join(q.split())) if q else -1
            if pos >= 0:
                ctx = flat[max(0, pos - 300):pos + len(q) + 200]
            else:
                m = re.search(re.escape(name), t)
                if m:
                    ctx = " ".join(t[max(0, m.start() - 350):m.end() + 250].split())
        print(f"[{i}] {r['reported_name']} | {r['tortoise']} | {r['type']} | {r['locator'][:90]}\n    {ctx}\n")


if __name__ == "__main__":
    main()
