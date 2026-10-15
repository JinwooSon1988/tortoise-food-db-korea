#!/usr/bin/env python3
"""Korean and English plant pages show the same evidence and the same information.

1. Every evidence card field on the Korean pages shows the record's own content: none of the generic sentences the
   Korean generator falls back to when it cannot localize an English field (summary, plant scope, plant part,
   limits, animal taxon) may appear.
2. data/i18n/ko/evidence_text_ko.json, the Korean text for those fields, is a translation and nothing more:
   every entry matches the current English value of that field in some public evidence record (no stale or unused
   entry), keeps every number and every scientific name of the English text, and is written in Korean.
3. For every plant, the Korean and English pages list the same evidence cards in the same order, show the same
   source counts and the same "same finding" / "different finding" notes, and the Korean plant-scope cell names
   every scientific name the English cell names.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
load = lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))

# The generic sentences of scripts/generate_static_pages.py (animal_taxon_display, plant_taxon_display,
# part_state_display, evidence_support_display, evidence_limit_display) for an English value it cannot localize.
FALLBACKS = {
    "summary": "명시된 근거 범위를 뒷받침한다. 구체적인 급여 판정은 위 판정 카드와",
    "plant scope": "원자료가 실제로 다룬 식물 범위 — 세부 종과 적용 범위는 출처에 명시된 내용만 사용",
    "plant part": "출처에 명시된 식물 부위·상태만 해당 — 다른 부위나 상태로 임의 일반화하지 않음",
    "limits": "이 자료만으로 육지거북의 정확한 급여량·정해진 급여 빈도·식단 비율·독성 용량·무제한 급여 또는 자료가 직접 다루지 않은",
    "animal": "원자료가 실제로 다룬 동물 — 육지거북을 직접 시험한 자료인지 여부는",
}
FIELDS = {"supports", "does_not_support", "plant_taxon", "plant_part_state", "animal_taxon"}
NOT_EPITHET = {"spp", "ssp", "var", "subsp", "and", "syn", "agg", "species", "leaf", "leaves", "food", "concept", "within", "taxa",
               "plant", "plants", "context", "scope", "sprouts", "seedlings", "group", "the", "source", "identity", "only", "linked", "greens"}
NUM = re.compile(r"\d+(?:[.,]\d+)?")
CARD = re.compile(r'<article class="evcard[^"]*"[^>]*data-evidence-id="([^"]+)"(.*?)</article>', re.S)


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def binomials(s, genera, epithets):
    """Latin binomials (and abbreviated ones such as R. acetosa): a known genus followed by a known epithet."""
    out = set()
    for g, ep in re.findall(r"(?<![A-Za-z])([A-Z][a-z]+|[A-Z]\.) (?:× )?([a-z]{3,})(?![a-z])", s):
        if (g in genera or len(g) == 2) and ep in epithets:
            out.add((g, ep))
    return out


def main():
    errors = []
    records = load("data/public_evidence_records.json")["records"]
    # Genera and epithets come from the plant list and the records' plant-scope fields, so English words that follow a
    # genus ("Salix species", "Testudo toxic dose") are not taken for epithets.
    genera, epithets = set(), set()
    for name in [p.get("scientific") for p in load("data/plants.json")] + [r.get("plant_taxon") for r in records]:
        for g, ep in re.findall(r"(?<![A-Za-z])([A-Z][a-z]+) (?:× )?([a-z]{3,})(?![a-z])", str(name or "")):
            if ep not in NOT_EPITHET:
                genera.add(g); epithets.add(ep)

    # --- 2. the Korean text store
    current = {(f, r[f]) for r in records for f in FIELDS if isinstance(r.get(f), str)}
    seen = set()
    for e in load("data/i18n/ko/evidence_text_ko.json")["entries"]:
        key = (e["field"], e["en"])
        label = f'{e["field"]}: {e["en"][:70]}'
        if key in seen:
            errors.append("duplicate Korean text entry: " + label)
        seen.add(key)
        if e["field"] not in FIELDS:
            errors.append("Korean text entry for an unknown field: " + label)
        if key not in current:
            errors.append("stale Korean text entry (no record has this English text any more): " + label)
        if not re.search(r"[가-힣]", e["ko"]):
            errors.append("Korean text entry is not Korean: " + label)
        ko = e["ko"].replace("–", "-")
        for n in NUM.findall(e["en"].replace("–", "-")):
            if n not in ko:
                errors.append(f"Korean text drops the number {n}: " + label)
        for g, ep in binomials(e["en"], genera, epithets):
            if not re.search(re.escape(g) + r" (?:× )?" + ep, e["ko"]):
                errors.append(f"Korean text drops the scientific name {g} {ep}: " + label)

    # --- 1 and 3. rendered pages
    pages = 0
    for ko_path in sorted((ROOT / "plant").glob("*/index.html")):
        pid = ko_path.parent.name
        en_path = ROOT / "en/plant" / pid / "index.html"
        if not en_path.exists():
            continue
        pages += 1
        tk, te = ko_path.read_text(encoding="utf-8"), en_path.read_text(encoding="utf-8")
        ck, ce = dict((m[0], m[1]) for m in CARD.findall(tk)), dict((m[0], m[1]) for m in CARD.findall(te))
        if list(ck) != list(ce):
            errors.append(f"{pid}: evidence cards differ (ko {list(ck)}, en {list(ce)})")
        stats = [re.findall(r"<strong>(\d+)", (re.search(r'<div class="evstats">(.*?)</div></div>', t, re.S) or [None, ""])[1]) for t in (tk, te)]
        if stats[0] != stats[1]:
            errors.append(f"{pid}: source counts differ (ko {stats[0]}, en {stats[1]})")
        for cid, body in ck.items():
            b = text(body)
            for name, sentence in FALLBACKS.items():
                if sentence in b:
                    errors.append(f"{pid}/{cid}: Korean {name} shows the generic sentence instead of the source's content")
            if cid not in ce:
                continue
            eb = text(ce[cid])
            for pat in (r"기록 (\d+)건을 이 카드 하나로|(\d+) more records? with the same finding",
                        r"다른 결과 기록이 (\d+)건|has (\d+) more records? with a different"):
                k, n = re.search(pat, b), re.search(pat, eb)
                if bool(k) != bool(n) or (k and n and set(k.groups()) - {None} != set(n.groups()) - {None}):
                    errors.append(f"{pid}/{cid}: same-source note differs between Korean and English")
            dk = re.findall(r"<dd>(.*?)</dd>", body, re.S)
            de = re.findall(r"<dd>(.*?)</dd>", ce[cid], re.S)
            if len(dk) > 1 and len(de) > 1:
                missing = binomials(text(de[1]), genera, epithets) - binomials(text(dk[1]), genera, epithets)
                if missing:
                    errors.append(f"{pid}/{cid}: Korean plant scope drops {sorted(' '.join(x) for x in missing)}")

    if errors:
        print("Korean/English evidence parity QA failed (%d):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"Korean/English evidence parity QA ok: {pages} plants, {len(seen)} Korean text entries, no generic fallback on any card")


if __name__ == "__main__":
    main()
