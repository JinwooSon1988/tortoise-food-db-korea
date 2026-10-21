"""Re-verify batch-002 agent records against the saved source texts.

For every records.jsonl line: the source exists in sources.jsonl, its local text exists, the verbatim quote occurs in the
text (whitespace, hyphenation and case normalised), and the reported plant name (or its genus-abbreviated form) occurs in
the quote. Writes verified.jsonl (with a 'check' field) and prints per-folder counts.
Run: python -X utf8 -I verify_b2.py <b2 dir>
"""
import json, re, sys, unicodedata, collections
from pathlib import Path

B2 = Path(sys.argv[1])


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"-\s*\n\s*", "", s)          # line-end hyphenation
    s = s.replace("­", "")
    s = re.sub(r"[‘’“”`´]", "'", s)
    s = re.sub(r"[‐-―]", "-", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


def name_forms(n):
    n = (n or "").strip()
    parts = n.split()
    forms = {n}
    if len(parts) >= 2:
        forms.add(parts[0][0] + ". " + " ".join(parts[1:]))
        forms.add(parts[0][0] + "." + " ".join(parts[1:]))
        forms.add(parts[1])
    return {norm(f) for f in forms if f}


out, stats = [], collections.defaultdict(collections.Counter)
for d in sorted(p for p in B2.iterdir() if p.is_dir()):
    srcf, recf = d / "sources.jsonl", d / "records.jsonl"
    if not recf.exists():
        continue
    src = {}
    for line in srcf.read_text(encoding="utf-8").splitlines() if srcf.exists() else []:
        if line.strip():
            s = json.loads(line); src[s["source_id"]] = s
    texts = {}
    for line in recf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        s = src.get(r.get("source_id"))
        check = "ok"
        if not s:
            check = "no_source"
        else:
            lt = r.get("local_txt") or s.get("local_txt") or ""
            p = (d / lt) if lt and not Path(lt).is_absolute() else Path(lt)
            if not lt or not p.exists():
                check = "no_local_text"
            else:
                if p not in texts:
                    texts[p] = norm(p.read_text(encoding="utf-8", errors="replace"))
                q = norm(r.get("quote"))
                if not q or q not in texts[p]:
                    # tolerate PDF column breaks: every 6-word window of the quote must occur
                    w = q.split()
                    wins = [" ".join(w[i:i + 6]) for i in range(0, max(1, len(w) - 5), 3)]
                    check = "quote_fragments_found" if w and all(x in texts[p] for x in wins) else "quote_not_found"
                if check != "quote_not_found" and not any(f in q for f in name_forms(r.get("plant_reported"))) \
                        and norm(r.get("plant_common_reported") or "~") not in q:
                    check = "name_not_in_quote"
        stats[d.name][check] += 1
        out.append(dict(r, folder=d.name, check=check))
(B2 / "verified.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out), encoding="utf-8")
for k, v in stats.items():
    print(k, dict(v))
