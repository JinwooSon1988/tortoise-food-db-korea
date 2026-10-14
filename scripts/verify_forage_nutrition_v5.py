#!/usr/bin/env python3
"""Check every unit-5 Feedipedia value against a saved copy of the source page, with a parser written separately from the one
that built the records (it reads the HTML table rows directly).

Usage:
  python scripts/verify_forage_nutrition_v5.py --pages <dir with feedipedia_<node>.html saved from the live site> --fetched-on YYYY-MM-DD

Writes data/research/forage_nutrition_verification_v5.json. A value is 'matched' only when the page row has the same label,
unit, mean and sample count; anything else is reported as it is and is not called verified.
"""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"
UNIT_MAP = {"% as fed": "% as fed", "% DM": "% DM", "g/kg DM": "g/kg DM", "mg/kg DM": "mg/kg DM"}


def cell_text(c):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", c))).strip()


def page_rows(page):
    rows = []
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", page):
        cells = [cell_text(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
        if len(cells) >= 7 and cells[1] and re.fullmatch(r"-?\d+(\.\d+)?", cells[2] or "x"):
            rows.append({"label": cells[0], "unit": cells[1], "avg": float(cells[2]), "nb": cells[6]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True)
    ap.add_argument("--fetched-on", required=True)
    a = ap.parse_args()
    recs = json.loads((RES / "forage_nutrition_research_v5.json").read_text(encoding="utf-8"))["records"]
    out = []
    for r in recs:
        p = Path(a.pages) / ("feedipedia_%s.html" % r["source_id"])
        entry = {"record_id": r["record_id"], "source_url": r["source_url"], "page_saved": p.exists(), "page_sha256": None, "page_title": None,
                 "title_matches_record": None, "values": [], "record_status": "not_verified_page_missing"}
        if p.exists():
            raw = p.read_bytes()
            page = raw.decode("utf-8", "replace")
            entry["page_sha256"] = hashlib.sha256(raw).hexdigest()
            m = re.search(r'property="dc:title" content="([^"]+)"', page)
            entry["page_title"] = html.unescape(m.group(1)) if m else None
            entry["title_matches_record"] = entry["page_title"] == r["table_title_as_printed"]
            rows = page_rows(page)
            for v in r["values"]:
                hits = [x for x in rows if x["label"].lower() == v["nutrient_name"] and x["unit"] == v["nutrient_unit"]]
                if len(hits) != 1:
                    st = "row_not_found" if not hits else "row_ambiguous"
                    entry["values"].append({"nutrient_name": v["nutrient_name"], "nutrient_unit": v["nutrient_unit"], "status": st})
                    continue
                h = hits[0]
                same = abs(h["avg"] - v["nutrient_value"]) < 1e-9 and str(h["nb"]) == str(v["sample_count"])
                entry["values"].append({"nutrient_name": v["nutrient_name"], "nutrient_unit": v["nutrient_unit"], "measurement_basis": v["measurement_basis"],
                                        "record_value": v["nutrient_value"], "page_value": h["avg"], "record_sample_count": v["sample_count"], "page_sample_count": h["nb"],
                                        "status": "matched" if same else "mismatch"})
            ok = entry["title_matches_record"] and entry["values"] and all(x["status"] == "matched" for x in entry["values"])
            entry["record_status"] = "all_values_matched_saved_live_page" if ok else "not_fully_verified"
        out.append(entry)
    doc = {"schema_version": "5.0", "generated_by": "scripts/verify_forage_nutrition_v5.py", "pages_fetched_on": a.fetched_on,
           "method": "Each value of forage_nutrition_research_v5.json is looked up in the table rows of a copy of the Feedipedia page saved from the live site, using a parser separate from the build. A value is 'matched' when label, unit, mean and sample count (Nb) are identical. The page title gives the plant part and fresh/hay state.",
           "not_checked": "Standard deviation, minimum and maximum were not stored and are not compared. The underlying samples behind each Feedipedia mean were not examined.",
           "records": out,
           "totals": {"records": len(out), "records_all_matched": sum(e["record_status"] == "all_values_matched_saved_live_page" for e in out),
                      "values": sum(len(e["values"]) for e in out), "values_matched": sum(x["status"] == "matched" for e in out for x in e["values"])}}
    (RES / "forage_nutrition_verification_v5.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(doc["totals"])


if __name__ == "__main__":
    main()
