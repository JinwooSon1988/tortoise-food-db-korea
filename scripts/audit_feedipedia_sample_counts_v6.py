#!/usr/bin/env python3
"""Check every Feedipedia value held in the repository against saved copies of the Feedipedia pages, reading each table row
directly (label, unit, mean, Nb, calculated marker). Written after the shared parser in verify_nutrition_reference_sources_v1.py
was found to give a blank-Nb row the Nb of the following row.

Usage:
  python scripts/audit_feedipedia_sample_counts_v6.py --pages <dir of feedipedia_<node>.html saved from the live site> --fetched-on YYYY-MM-DD

Writes data/research/feedipedia_sample_count_audit_v6.json. Public data files are only read; this script never edits them.
"""
import argparse
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
RESEARCH_FILES = ["forage_nutrition_research_v1.json", "forage_nutrition_research_v2.json", "forage_nutrition_research_v5.json"]
PUBLIC_DM = ROOT / "data/plant_nutrition_dm_basis_v1.json"
PUBLIC_REF = ROOT / "data/plant_nutrition_reference_v1.json"
ABBR = {"ndf": "neutral detergent fibre", "adf": "acid detergent fibre", "wsc": "water-soluble carbohydrates"}
SUFFIX = [("_pct_as_fed", "% as fed"), ("_pct_dm", "% DM"), ("_g_per_kg_dm", "g/kg DM"), ("_mg_per_kg_dm", "mg/kg DM"), ("_mj_per_kg_dm", "MJ/kg DM")]


def cell(c):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", c))).strip()


def table_rows(page):
    """Rows of the composition tables in page order: label, unit, mean, Nb (blank stays blank), calculated marker."""
    rows = []
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", page):
        cells = [cell(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
        if len(cells) >= 7 and cells[1] and re.fullmatch(r"-?\d+(\.\d+)?", cells[2] or "x"):
            rows.append({"label": cells[0], "unit": cells[1], "avg": float(cells[2]), "nb": cells[6], "calculated_marker": (cells[7] if len(cells) > 7 else "") == "*"})
        elif len(cells) >= 2 and cells[1] == "Unit":
            rows.append({"section": cells[0]})
    return rows


ALIASES = {"neutral detergent fibre": ["ndf"], "acid detergent fibre": ["adf"], "water-soluble carbohydrates": ["water soluble carbohydrates"],
           "water soluble carbohydrates": ["water-soluble carbohydrates"]}


def find(rows, label, unit):
    names = {label.lower(), *ALIASES.get(label.lower(), [])}
    return [i for i, r in enumerate(rows) if "label" in r and r["label"].lower() in names and r["unit"] == unit]


def explain(rows, i, stored_nb):
    """Where a stored Nb that is not on the row itself could have come from: the next rows of the same section."""
    out = []
    for r in rows[i + 1:]:
        if "section" in r:
            break
        if str(r["nb"]) == str(stored_nb):
            out.append("%s [%s]" % (r["label"], r["unit"]))
    return out


def check_value(rows, label, unit, value, nb):
    idx = find(rows, label, unit)
    if len(idx) != 1:
        return {"status": "row_not_found" if not idx else "row_ambiguous"}
    r = rows[idx[0]]
    res = {"mean_on_page": r["avg"], "nb_on_page": r["nb"] or None, "calculated_marker_on_page": r["calculated_marker"]}
    if abs(r["avg"] - value) > 1e-9:
        res["status"] = "mean_differs"
    elif nb is None:
        res["status"] = "mean_matched_nb_not_stored"
    elif str(r["nb"]) == str(nb):
        res["status"] = "matched"
    elif not r["nb"]:
        res.update(status="nb_blank_on_page_but_stored", stored_nb_equals_nb_of_following_rows=explain(rows, idx[0], nb))
    else:
        res["status"] = "nb_differs"
    return res


def label_of(key):
    for suf, unit in SUFFIX:
        if key.endswith(suf):
            name = key[: -len(suf)].replace("_", " ")
            return ABBR.get(name, name), unit
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--fetched-on", required=True)
    a = ap.parse_args()
    pages = {}

    def rows_for(node):
        if node not in pages:
            p = Path(a.pages) / ("feedipedia_%s.html" % node)
            pages[node] = (table_rows(p.read_text(encoding="utf-8", errors="replace")), hashlib.sha256(p.read_bytes()).hexdigest()) if p.exists() else (None, None)
        return pages[node]

    research, dropped = [], []
    for f in RESEARCH_FILES:
        for r in json.loads((RES / f).read_text(encoding="utf-8"))["records"]:
            if not r["record_id"].startswith("feedipedia-"):
                continue
            rows, _ = rows_for(r["source_id"])
            for v in r["values"]:
                res = check_value(rows, v["nutrient_name"], v["nutrient_unit"], v["nutrient_value"], v["sample_count"]) if rows else {"status": "page_not_saved"}
                research.append({"file": f, "record_id": r["record_id"], "nutrient_name": v["nutrient_name"], "nutrient_unit": v["nutrient_unit"],
                                 "stored_value": v["nutrient_value"], "stored_nb": v["sample_count"], **res})
            for dv in r.get("values_dropped_no_sample_count_on_page") or []:
                res = check_value(rows, dv["nutrient_name"], dv["nutrient_unit"], dv["mean_on_page"], dv["sample_count_from_the_shared_parser"]) if rows else {"status": "page_not_saved"}
                dropped.append({"file": f, "record_id": r["record_id"], "nutrient_name": dv["nutrient_name"], "nutrient_unit": dv["nutrient_unit"],
                                "value": dv["mean_on_page"], "nb_given_by_shared_parser": dv["sample_count_from_the_shared_parser"], **res,
                                "decision": "excluded: the source row prints no sample count; the number came from another row" if res.get("status") == "nb_blank_on_page_but_stored" else "excluded; see status"})

    public = []
    if PUBLIC_DM.exists():
        for r in json.loads(PUBLIC_DM.read_text(encoding="utf-8"))["records"]:
            m = re.search(r"feedipedia\.org/node/(\d+)", r.get("source_url", ""))
            if not m:
                continue
            rows, _ = rows_for(m.group(1))
            for key, v in r["values"].items():
                lab, unit = label_of(key)
                res = check_value(rows, lab, unit, v["value"], v.get("n")) if rows and lab else {"status": "page_not_saved" if not rows else "key_not_mapped"}
                public.append({"file": "data/plant_nutrition_dm_basis_v1.json", "plant_id": r["plant_id"], "node": m.group(1), "key": key, "stored_value": v["value"], "stored_nb": v.get("n"), **res})
    if PUBLIC_REF.exists():
        for r in json.loads(PUBLIC_REF.read_text(encoding="utf-8"))["records"]:
            m = re.search(r"feedipedia\.org/node/(\d+)", r.get("source_url", "") or "")
            if not m:
                continue
            rows, _ = rows_for(m.group(1))
            for key, val in (r.get("nutrients") or {}).items():
                lab, unit = label_of(key)
                res = check_value(rows, lab, unit, val, None) if rows and lab else {"status": "page_not_saved" if not rows else "key_not_mapped"}
                public.append({"file": "data/plant_nutrition_reference_v1.json", "plant_id": r["plant_id"], "node": m.group(1), "key": key, "stored_value": val, "stored_nb": None, **res})

    doc = {"schema_version": "6.0", "generated_by": "scripts/audit_feedipedia_sample_counts_v6.py", "pages_fetched_on": a.fetched_on,
           "method": "Each stored Feedipedia value is looked up in the table rows of a copy of the source page saved from the live site. 'matched' means the same label, unit, mean and Nb. 'nb_blank_on_page_but_stored' means the page row has no Nb but the file holds one; the audit names the following row(s) whose Nb equals the stored number.",
           "cause": "verify_nutrition_reference_sources_v1.parse_feedipedia reads a flattened text in which blank cells disappear, so a row with a blank Nb takes the Nb printed on the next row.",
           "pages": {n: h for n, (_, h) in sorted(pages.items())},
           "research_values": research, "research_values_excluded": dropped, "public_values_read_only": public,
           "totals": {"research_values": len(research), "research_by_status": dict(sorted(Counter(x["status"] for x in research).items())),
                      "research_excluded": len(dropped), "research_excluded_by_status": dict(sorted(Counter(x["status"] for x in dropped).items())),
                      "public_values": len(public), "public_by_status": dict(sorted(Counter(x["status"] for x in public).items()))}}
    # fill the source-row fields of the unit-5 exclusion audit (keys kept as its author defined them)
    ex_path = RES / "forage_nutrition_exclusion_audit_v5.json"
    if ex_path.exists():
        ex = json.loads(ex_path.read_text(encoding="utf-8"))
        by = {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]): x for x in dropped}
        for row in ex.get("excluded_values", []):
            hit = by.get((row["record_id"], row["nutrient_name"], row["nutrient_unit"]))
            if not hit or hit.get("status") != "nb_blank_on_page_but_stored":
                continue
            node = row["record_id"].split("-", 1)[1]
            row.update(source_row_mean=hit["mean_on_page"], source_row_unit=row["nutrient_unit"], source_row_sample_count="",
                       source_row_sample_count_printed=False, source_row_calculated_marker=hit["calculated_marker_on_page"],
                       previous_sample_count_matches_nb_of_following_rows=hit.get("stored_nb_equals_nb_of_following_rows") or [],
                       exclusion_reason="source_row_prints_no_sample_count",
                       review_status="source_row_verified", verified_against="saved copy of %s fetched on %s, sha256 %s" % (row["source_url"], a.fetched_on, pages[node][1]),
                       verified_by_script="scripts/audit_feedipedia_sample_counts_v6.py")
        ex["source_row_check"] = {"done_on": a.fetched_on, "method": "table row read directly from the saved page; an empty Nb cell is recorded as an empty string and source_row_sample_count_printed=false"}
        ex_path.write_text(json.dumps(ex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    (RES / "feedipedia_sample_count_audit_v6.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
