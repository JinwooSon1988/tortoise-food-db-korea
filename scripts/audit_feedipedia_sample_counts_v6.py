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


def _ft():
    import importlib.util
    spec = importlib.util.spec_from_file_location("feedipedia_table", Path(__file__).resolve().parent / "feedipedia_table.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


FT = _ft()


def table_rows(page):
    """Rows read cell by cell by scripts/feedipedia_table.py (the same reader the shared parser now uses)."""
    return FT.parse_rows(page)


def explain(rows, r, stored_nb):
    """Where a stored Nb that is not printed on the row could have come from: an Nb or a mean printed on a following row of the same table."""
    out = []
    after = [x for x in rows if x["table"] == r["table"] and x["row"] > r["row"]]
    for x in after:
        if x["nb"] is not None and str(x["nb"]) == str(stored_nb):
            out.append("Nb of %s [%s]" % (x["label"], x["unit"]))
        if abs(x["avg"] - float(stored_nb)) < 1e-9:
            out.append("mean of %s [%s]" % (x["label"], x["unit"]))
    return out


def check_value(rows, label, unit, value, nb, heading_word=None):
    hits = FT.find(rows, label, unit, heading_word)
    if len(hits) != 1:
        return {"status": "row_not_found" if not hits else "row_ambiguous", "candidate_tables": sorted({h["table_heading"] or "" for h in hits})}
    r = hits[0]
    res = {"mean_on_page": r["avg"], "nb_on_page": r["nb"], "calculated_marker_on_page": r["calculated"], "table_heading": r["table_heading"],
           "section": r["section"], "rowspan_in_row": r["rowspan_in_row"]}
    if r["rowspan_in_row"]:
        res["status"] = "row_in_rowspan_block_not_decidable"
    elif abs(r["avg"] - value) > 1e-9:
        res["status"] = "mean_differs"
    elif nb is None:
        res["status"] = "mean_matched_nb_not_stored"
    elif r["calculated"] and nb == "*":
        res["status"] = "matched_calculated"
    elif r["nb"] is not None and str(r["nb"]) == str(nb):
        res["status"] = "matched"
    elif r["nb"] is None:
        res.update(status="nb_blank_on_page_but_stored", stored_nb_found_on_following_rows=explain(rows, r, nb))
    else:
        res["status"] = "nb_differs"
    return res


# what a status lets a reader rely on: the mean and the sample count, the mean alone, or nothing
LEVEL = {"matched": "mean_and_sample_count_verified", "matched_calculated": "mean_verified_calculated_value_without_sample_count",
         "mean_matched_nb_not_stored": "mean_only_verified", "excluded_nb_blank_on_page": "excluded_not_used", "excluded_but_page_prints_nb": "excluded_not_used"}


def level(status):
    return LEVEL.get(status, "not_verified")


# sample counts that the former flattened-text parser attached to rows whose Nb cell is blank (found in units 2, 5 and 6)
FORMER_PARSER_COUNTS = {("feedipedia-11865", "dry matter"): 165, ("feedipedia-11865", "calcium"): 72, ("feedipedia-12645", "magnesium"): 6,
                        ("feedipedia-12645", "sodium"): 33, ("feedipedia-12646", "dry matter"): 6, ("feedipedia-12646", "ether extract"): 5}


def state_word(*texts):
    t = " ".join(x or "" for x in texts).lower()
    return next((w for w in ("silage", "straw", "hay", "fresh", "dried", "dehydrated") if w in t), None)


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
                res = check_value(rows, v["nutrient_name"], v["nutrient_unit"], v["nutrient_value"], v["sample_count"], state_word(r.get("table_title_as_printed"))) if rows else {"status": "page_not_saved"}
                research.append({"file": f, "record_id": r["record_id"], "nutrient_name": v["nutrient_name"], "nutrient_unit": v["nutrient_unit"],
                                 "stored_value": v["nutrient_value"], "stored_nb": v["sample_count"], **res, "verification_level": level(res.get("status"))})
            for dv in r.get("values_dropped_no_sample_count_on_page") or []:
                former = FORMER_PARSER_COUNTS.get((r["record_id"], dv["nutrient_name"]))
                res = check_value(rows, dv["nutrient_name"], dv["nutrient_unit"], dv["mean_on_page"], None, state_word(r.get("table_title_as_printed"))) if rows else {"status": "page_not_saved"}
                if res.get("status") == "mean_matched_nb_not_stored":
                    res["status"] = "excluded_nb_blank_on_page" if res["nb_on_page"] is None else "excluded_but_page_prints_nb"
                if former is not None and rows:
                    hit = FT.find(rows, dv["nutrient_name"], dv["nutrient_unit"], state_word(r.get("table_title_as_printed")))
                    res["former_parser_count_found_on_following_rows"] = explain(rows, hit[0], former) if len(hit) == 1 else []
                dropped.append({"file": f, "record_id": r["record_id"], "nutrient_name": dv["nutrient_name"], "nutrient_unit": dv["nutrient_unit"],
                                "value": dv["mean_on_page"], "count_given_by_former_parser": former, **res,
                                "decision": "excluded: the source row prints no sample count" if res.get("status") == "excluded_nb_blank_on_page" else "check: see status",
                                "verification_level": level(res.get("status"))})

    public = []
    if PUBLIC_DM.exists():
        for r in json.loads(PUBLIC_DM.read_text(encoding="utf-8"))["records"]:
            m = re.search(r"feedipedia\.org/node/(\d+)", r.get("source_url", ""))
            if not m:
                continue
            rows, _ = rows_for(m.group(1))
            for key, v in r["values"].items():
                lab, unit = label_of(key)
                res = check_value(rows, lab, unit, v["value"], v.get("n"), state_word(r.get("variant"), r.get("preparation_state"))) if rows and lab else {"status": "page_not_saved" if not rows else "key_not_mapped"}
                public.append({"file": "data/plant_nutrition_dm_basis_v1.json", "plant_id": r["plant_id"], "node": m.group(1), "key": key, "stored_value": v["value"], "stored_nb": v.get("n"), **res, "verification_level": level(res.get("status"))})
    if PUBLIC_REF.exists():
        for r in json.loads(PUBLIC_REF.read_text(encoding="utf-8"))["records"]:
            m = re.search(r"feedipedia\.org/node/(\d+)", r.get("source_url", "") or "")
            if not m:
                continue
            rows, _ = rows_for(m.group(1))
            for key, val in (r.get("nutrients") or {}).items():
                lab, unit = label_of(key)
                res = check_value(rows, lab, unit, val, None, state_word(r.get("preparation_state"), r.get("analyzed_part"))) if rows and lab else {"status": "page_not_saved" if not rows else "key_not_mapped"}
                public.append({"file": "data/plant_nutrition_reference_v1.json", "plant_id": r["plant_id"], "node": m.group(1), "key": key, "stored_value": val, "stored_nb": None, **res, "verification_level": level(res.get("status"))})

    doc = {"schema_version": "6.0", "generated_by": "scripts/audit_feedipedia_sample_counts_v6.py", "pages_fetched_on": a.fetched_on,
           "method": "Each stored Feedipedia value is looked up in the table rows of a copy of the source page saved from the live site. 'matched' means the same label, unit, mean and Nb. 'nb_blank_on_page_but_stored' means the page row has no Nb but the file holds one; the audit names the following row(s) whose Nb equals the stored number. 'verification_level' separates values whose mean and sample count were both compared ('mean_and_sample_count_verified') from values whose mean alone was compared because no sample count is stored ('mean_only_verified').",
           "cause": "verify_nutrition_reference_sources_v1.parse_feedipedia reads a flattened text in which blank cells disappear, so a row with a blank Nb takes the Nb printed on the next row.",
           "pages": {n: h for n, (_, h) in sorted(pages.items())},
           "research_values": research, "research_values_excluded": dropped, "public_values_read_only": public,
           "totals": {"research_values": len(research), "research_by_status": dict(sorted(Counter(x["status"] for x in research).items())),
                      "research_excluded": len(dropped), "research_excluded_by_status": dict(sorted(Counter(x["status"] for x in dropped).items())),
                      "public_values": len(public), "public_by_status": dict(sorted(Counter(x["status"] for x in public).items())),
                      "research_by_verification_level": dict(sorted(Counter(x["verification_level"] for x in research).items())),
                      "public_by_verification_level": dict(sorted(Counter(x["verification_level"] for x in public).items())),
                      "public_mean_only_whose_page_row_prints_no_sample_count": sum(1 for x in public if x["verification_level"] == "mean_only_verified" and x.get("nb_on_page") is None)}}
    # fill the source-row fields of the unit-5 exclusion audit (keys kept as its author defined them)
    ex_path = RES / "forage_nutrition_exclusion_audit_v5.json"
    if ex_path.exists():
        ex = json.loads(ex_path.read_text(encoding="utf-8"))
        by = {(x["record_id"], x["nutrient_name"], x["nutrient_unit"]): x for x in dropped}
        for row in ex.get("excluded_values", []):
            hit = by.get((row["record_id"], row["nutrient_name"], row["nutrient_unit"]))
            if not hit or hit.get("status") != "excluded_nb_blank_on_page":
                continue
            node = row["record_id"].split("-", 1)[1]
            row.update(source_row_mean=hit["mean_on_page"], source_row_unit=row["nutrient_unit"], source_row_sample_count="",
                       source_row_sample_count_printed=False, source_row_calculated_marker=hit["calculated_marker_on_page"],
                       previous_sample_count_matches_nb_of_following_rows=[x for x in hit.get("former_parser_count_found_on_following_rows") or [] if x.startswith("Nb of")],
                       previous_sample_count_matches_mean_of_following_rows=[x for x in hit.get("former_parser_count_found_on_following_rows") or [] if x.startswith("mean of")],
                       exclusion_reason="source_row_prints_no_sample_count",
                       review_status="source_row_verified", verified_against="saved copy of %s fetched on %s, sha256 %s" % (row["source_url"], a.fetched_on, pages[node][1]),
                       verified_by_script="scripts/audit_feedipedia_sample_counts_v6.py")
        ex["source_row_check"] = {"done_on": a.fetched_on, "method": "table row read directly from the saved page; an empty Nb cell is recorded as an empty string and source_row_sample_count_printed=false"}
        ex_path.write_text(json.dumps(ex, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    (RES / "feedipedia_sample_count_audit_v6.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
