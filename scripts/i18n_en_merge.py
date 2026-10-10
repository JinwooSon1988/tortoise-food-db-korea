#!/usr/bin/env python3
"""Merge reviewed English translation batches into data/i18n/en/strings_en.json and check each entry.

  python scripts/i18n_en_merge.py data/i18n/en/batches/*.json   # merge {key: english} files (source text taken from _missing.json)
  python scripts/i18n_en_merge.py --check                       # check every stored entry (also run by QA)

Checks per entry (Korean source -> English):
  * no Hangul in the English text;
  * every Latin binomial / abbreviated name / genus with spp. in the source appears in the English text;
  * every number in the source appears in the English text (counts, years, percentages, grades);
  * an A–D grade letter or evidence-certainty code mentioned in the source is kept.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data/i18n/en/strings_en.json"
MISSING = ROOT / "data/i18n/en/_missing.json"
HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"\b[A-Z][a-z]+(?: (?:×|x) )?(?: [a-z]{3,})?(?: (?:subsp|var|f|cv)\. [a-z]+)?|\b[A-Z]\. ?[a-z]{2,}(?: [a-z]{3,})?")
NUM = re.compile(r"(?<![A-Za-z가-힣])\d+(?:[.,]\d+)?(?!\d|차)")  # "2차 대사산물" = secondary metabolites, not a count
GRADE = re.compile(r"(?<![A-Za-z])([ABCD][+-]?)(?= ?(?:등급|수준|판정|는|은|가|이|로|의|$|\s|,|\)|·))")


def norm(s):
    return re.sub(r"\s+", " ", s.replace("×", "x")).strip()


def check_entry(ko, en):
    errs = []
    if HANGUL.search(en):
        errs.append("Hangul left in English")
    en_n = norm(en)
    for m in set(LATIN.findall(ko)):
        m = norm(m)
        if len(m) < 4 or m in {"Merck", "Tortoise Trust", "UC Davis", "The Tortoise", "Tortoise Table", "Kew", "BCG", "Vetpharm", "GBIF", "POWO"}:
            continue
        first = m.split(" ")[0]
        if m not in en_n and m.lower() not in en_n.lower() and not (first.endswith(".") and first[:-1] in en_n):
            if " " in m and m.split(" ")[0] in en_n and m.split(" ")[1] in en_n:
                continue
            errs.append(f"Latin name not kept: {m}")
    for n in set(NUM.findall(ko)):
        if n not in en:
            errs.append(f"number not kept: {n}")
    for g in set(GRADE.findall(ko)):
        if not re.search(rf"(?<![A-Za-z]){re.escape(g)}(?![A-Za-z+-])", en):
            errs.append(f"grade/code not kept: {g}")
    return errs


def load_store():
    return json.loads(STORE.read_text(encoding="utf-8")) if STORE.exists() else {}


def main(args):
    store = load_store()
    if args and args[0] == "--check":
        bad = {k: check_entry(v["ko"], v["en"]) for k, v in store.items()}
        bad = {k: v for k, v in bad.items() if v}
        for k, v in list(bad.items())[:40]:
            print("ERROR", k, v, "|", store[k]["ko"][:60])
        if bad:
            sys.exit(f"translation check FAILED: {len(bad)} entr{'y' if len(bad) == 1 else 'ies'}")
        print(f"OK: {len(store)} English entries pass the source-fidelity checks")
        return
    missing = json.loads(MISSING.read_text(encoding="utf-8")) if MISSING.exists() else {}
    added, problems = 0, []
    for f in args:
        batch = json.loads(Path(f).read_text(encoding="utf-8"))
        for k, en in batch.items():
            src = (missing.get(k) or store.get(k) or {}).get("ko")
            if not src:
                problems.append(f"{f}: unknown key {k}")
                continue
            errs = check_entry(src, en)
            if errs:
                problems.append(f"{k}: {errs} | {src[:70]}")
            store[k] = {"en": en, "ko": src}
            added += 1
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(dict(sorted(store.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for p in problems:
        print("CHECK", p)
    print(f"merged {added} entries; store now {len(store)}; {len(problems)} entr{'y' if len(problems) == 1 else 'ies'} to review")


if __name__ == "__main__":
    main(sys.argv[1:])
