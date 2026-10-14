#!/usr/bin/env python3
"""Before/after report of the research layer against a git ref (the PR base), record by record and nutrient value by value.

  python scripts/diff_research_layer.py --base origin/main [--strict] [--json out.json]

For every data/research/*.json it prints the record count before and after, records added, removed and changed (with the
changed field names), and for the forage nutrition files every nutrient value added, removed or changed (mean or sample count).
With --strict it exits 1 when
  * an evidence or index record disappears, or its identity changes (tortoise, printed plant name, plant part, source),
  * a nutrient value disappears without being listed as excluded in the new files (dropped list or page audit),
  * a kept nutrient value changes its mean or sample count,
  * a value that the new files list as excluded is kept,
so that a rebuild cannot silently drop, alter or restore data. Added records and values are reported, not refused.
It never writes to the repository.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = "data/research"
ID_KEYS = ("evidence_id", "record_id", "reference_id", "hazard_id", "source_id", "v1_evidence_id", "tortoise_key", "candidate_key", "name_as_printed", "id", "key")
IDENTITY = ("tortoise_key", "plant_name_as_printed", "plant_part", "source_id")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def load_ref(ref, path):
    r = git("show", "%s:%s" % (ref, path))
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def lists(doc):
    """(list name, id key, {id: record}) for every top-level list of dicts that has an id field."""
    out = []
    for name, val in (doc or {}).items():
        if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
            key = next((k for k in ID_KEYS if all(k in x for x in val)), None)
            if key:
                recs = {}
                for i, x in enumerate(val):
                    ident = x[key] if key != "record_id" or "nutrient_name" not in x else (x.get("file"), x["record_id"], x["nutrient_name"], x["nutrient_unit"])
                    recs[str(ident) if ident not in recs else "%s#%d" % (ident, i)] = x
                out.append((name, key, recs))
    return out


def nutrient_values(doc):
    vals, dropped = {}, set()
    for r in (doc or {}).get("records", []):
        for v in r.get("values", []):
            vals[(r["record_id"], v["nutrient_name"], v["nutrient_unit"])] = (v["nutrient_value"], v.get("sample_count"))
        for d in r.get("values_dropped_no_sample_count_on_page") or []:
            dropped.add((r["record_id"], d["nutrient_name"], d["nutrient_unit"]))
    return vals, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    if git("rev-parse", "--verify", a.base + "^{commit}").returncode:
        print("base %s not found; fetch it first" % a.base)
        sys.exit(2)
    names = sorted({p.name for p in (ROOT / RES).glob("*.json")} | {Path(x).name for x in git("ls-tree", "--name-only", "%s:%s" % (a.base, RES)).stdout.split() if x.endswith(".json")})
    report, problems = {}, []
    excluded_now = set()
    audit = ROOT / RES / "feedipedia_sample_count_audit_v6.json"
    if audit.exists():
        excluded_now |= {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]) for x in json.loads(audit.read_text(encoding="utf-8"))["research_values_excluded"]}
    ex5 = ROOT / RES / "forage_nutrition_exclusion_audit_v5.json"
    if ex5.exists():
        excluded_now |= {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]) for x in json.loads(ex5.read_text(encoding="utf-8"))["excluded_values"]}
    new_docs = {}
    for n in names:
        p = ROOT / RES / n
        new_docs[n] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        for d in (nutrient_values(new_docs[n])[1] if n.startswith("forage_nutrition_research_") else ()):
            excluded_now.add(d)
    for n in names:
        old, new = load_ref(a.base, "%s/%s" % (RES, n)), new_docs[n]
        if old == new:
            continue
        entry = {"file": "added" if old is None else "removed" if new is None else "changed", "lists": {}}
        if new is None:
            problems.append("%s: file removed" % n)
        ol, nl = {k: (key, r) for k, key, r in lists(old)}, {k: (key, r) for k, key, r in lists(new)}
        for lname in sorted(set(ol) | set(nl)):
            o, w = ol.get(lname, (None, {}))[1], nl.get(lname, (None, {}))[1]
            added, removed = sorted(set(w) - set(o)), sorted(set(o) - set(w))
            changed = {i: sorted(k for k in set(o[i]) | set(w[i]) if o[i].get(k) != w[i].get(k)) for i in set(o) & set(w) if o[i] != w[i]}
            if added or removed or changed:
                entry["lists"][lname] = {"before": len(o), "after": len(w), "added": added, "removed": removed, "changed": dict(sorted(changed.items()))}
            if n.startswith(("tortoise_plant_evidence_", "evidence_index_")):
                problems += ["%s %s: evidence record removed" % (n, i) for i in removed]
                problems += ["%s %s: identity field(s) %s changed" % (n, i, [k for k in f if k in IDENTITY]) for i, f in changed.items() if any(k in IDENTITY for k in f)]
        if n.startswith("forage_nutrition_research_"):
            ov, nv = nutrient_values(old)[0], nutrient_values(new)[0]
            vadd, vrem = sorted(set(nv) - set(ov)), sorted(set(ov) - set(nv))
            vchg = sorted(k for k in set(ov) & set(nv) if ov[k] != nv[k])
            entry["nutrient_values"] = {"before": len(ov), "after": len(nv), "added": [[*k, *nv[k]] for k in vadd], "removed": [[*k, *ov[k]] for k in vrem],
                                        "changed": [[*k, ov[k], nv[k]] for k in vchg]}
            problems += ["%s %s: value removed without being listed as excluded" % (n, k) for k in vrem if k not in excluded_now]
            problems += ["%s %s: kept value changed %s -> %s" % (n, k, ov[k], nv[k]) for k in vchg]
            problems += ["%s %s: a value listed as excluded is kept" % (n, k) for k in nv if k in excluded_now]
        report[n] = entry
    for n, e in report.items():
        print("%s (%s)" % (n, e["file"]))
        for lname, d in e["lists"].items():
            print("  %-34s %5d -> %5d   +%d -%d ~%d" % (lname, d["before"], d["after"], len(d["added"]), len(d["removed"]), len(d["changed"])))
            fields = {}
            for f in d["changed"].values():
                for k in f:
                    fields[k] = fields.get(k, 0) + 1
            if fields:
                print("      changed fields:", ", ".join("%s x%d" % kv for kv in sorted(fields.items())))
            for i in d["removed"][:10]:
                print("      removed:", i)
        nv = e.get("nutrient_values")
        if nv:
            print("  nutrient values %d -> %d" % (nv["before"], nv["after"]))
            for tag in ("added", "removed", "changed"):
                for x in nv[tag]:
                    print("      %s: %s" % (tag, x))
    if not report:
        print("research layer identical to %s" % a.base)
    if a.json:
        Path(a.json).write_text(json.dumps({"base": a.base, "files": report, "problems": problems}, ensure_ascii=False, indent=1), encoding="utf-8")
    if problems:
        print("%d problem(s):" % len(problems))
        for p in problems[:80]:
            print(" -", p)
    sys.exit(1 if a.strict and problems else 0)


if __name__ == "__main__":
    main()
