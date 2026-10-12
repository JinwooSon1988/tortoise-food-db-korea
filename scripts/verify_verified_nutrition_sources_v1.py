#!/usr/bin/env python3
"""Re-check every VERIFIED nutrition record against the original source file, value by value.

Covers data/plant_nutrition_v56.json (plants + part_state_records) and data/rda_food_composition_v56.json.
Original files are not committed (size / licence); pass their local paths. A record whose original file is not
supplied is reported as "source_not_supplied", never as verified.

  --usda-sr          FoodData_Central_sr_legacy_food_json_2018-04.json
  --usda-foundation  FoodData_Central_foundation_food_json_2026-04-30.json
  --usda-csv         one or more original USDA CSV archives (FoodData_Central_*_food_csv_*.zip); full-precision amounts
  --rda              RDA 통합식품영양성분정보(원재료성식품) CSV (data.go.kr 15100065, UTF-8 with BOM)
  --ifct             IFCT2017.pdf (https://nin.res.in/ebooks/IFCT2017.pdf)
  --pmc-6268292 / --pmc-8472405   JATS XML from NCBI E-utilities efetch
  --rda104-dir       directory with detail_<F-code>.html pages of the RDA 10.4 database
                     (GET https://www.nics.go.kr/food/kfi/fct/fctFoodSrch/detail?foodCodes=<F-code>&fdNms=x&reformNo=-1&customQnt=100&onCuntNtkQntAt=)
  --bls              BLS_4_0_Daten_2025_DE.xlsx (https://blsdb.de/download, CC BY 4.0)
  --mext-dir         directory with mext_<code>.html item pages (fooddb.mext.go.jp)

Also checks, without any source file: Ca:P ratio arithmetic, per-100 g basis text, unit table, raw state.
Writes a JSON report with --out; exits 1 when any stored value differs from its original.
"""
import argparse
import csv
import html as H
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USDA_NAMES = {
    "Water": "water_g", "Protein": "protein_g", "Total lipid (fat)": "fat_g", "Carbohydrate, by difference": "carbohydrate_g",
    "Fiber, total dietary": "fiber_g", "Calcium, Ca": "calcium_mg", "Phosphorus, P": "phosphorus_mg", "Magnesium, Mg": "magnesium_mg",
    "Potassium, K": "potassium_mg", "Sodium, Na": "sodium_mg", "Iron, Fe": "iron_mg", "Vitamin C, total ascorbic acid": "vitamin_c_mg",
    "Vitamin A, RAE": "vitamin_a_rae_ug", "Sugars, total including NLEA": "sugars_g", "Sugars, Total": "sugars_g", "Total Sugars": "sugars_g",
    "Energy": "energy_kcal", "Energy (Atwater General Factors)": "energy_kcal", "Energy (Atwater Specific Factors)": "energy_kcal",
}
RDA_COLS = {"수분(g)": "water_g", "단백질(g)": "protein_g", "지방(g)": "fat_g", "탄수화물(g)": "carbohydrate_g", "식이섬유(g)": "fiber_g",
            "당류(g)": "sugars_g", "칼슘(mg)": "calcium_mg", "철(mg)": "iron_mg", "인(mg)": "phosphorus_mg", "칼륨(mg)": "potassium_mg",
            "나트륨(mg)": "sodium_mg", "마그네슘(mg)": "magnesium_mg", "비타민 C(mg)": "vitamin_c_mg", "에너지(kcal)": "energy_kcal",
            "비타민 A(μg RAE)": "vitamin_a_rae_ug"}
MEXT_LABELS = {"water_g": "水分", "protein_g": "たんぱく質", "fat_g": "脂質", "carbohydrate_g": "炭水化物", "fiber_g": "食物繊維総量",
               "calcium_mg": "カルシウム", "phosphorus_mg": "リン", "potassium_mg": "カリウム", "sodium_mg": "ナトリウム",
               "magnesium_mg": "マグネシウム", "iron_mg": "鉄", "vitamin_c_mg": "ビタミンC", "vitamin_a_rae_ug": "レチノール活性当量",
               "energy_kcal": "エネルギー"}
PMC_HEADS = {"Phosphorus": "phosphorus_mg", "Potassium": "potassium_mg", "Calcium": "calcium_mg", "Magnesium": "magnesium_mg",
             "Sodium": "sodium_mg", "Iron": "iron_mg", "Crude protein": "protein_g", "Crude Protein": "protein_g", "Dry matter": "dry_matter_pct",
             "Dry Matter": "dry_matter_pct"}
IFCT_HEADS = {"WATER": "water_g", "PROTCNT": "protein_g", "FATCE": "fat_g", "FIBTG": "fiber_g", "CHOAVLDF": "available_carbohydrate_g",
              "CA": "calcium_mg", "FE": "iron_mg", "MG": "magnesium_mg", "P": "phosphorus_mg", "K": "potassium_mg", "NA": "sodium_mg",
              "VITC": "vitamin_c_mg"}
NUTRIENT_KEYS = sorted(set(USDA_NAMES.values()) | set(RDA_COLS.values()) | set(IFCT_HEADS.values()) | {"dry_matter_pct"})


def decimals(v):
    s = repr(float(v))
    return len(s.split(".")[1]) if "." in s and not s.endswith(".0") else 0


def compare(stored, candidates):
    """exact / rounded (stored equals the source rounded to the stored precision) / mismatch."""
    for c in candidates:
        if abs(stored - c) < 1e-9:
            return "exact", c
    for c in candidates:
        if abs(round(c + 1e-12, decimals(stored)) - stored) < 1e-9 or abs(round(c - 1e-12, decimals(stored)) - stored) < 1e-9:
            return "rounded", c
    return "mismatch", (candidates[0] if candidates else None)


def usda_values(food):
    vals = {}
    for n in food["foodNutrients"]:
        k = USDA_NAMES.get(n["nutrient"]["name"])
        if not k or n.get("amount") is None:
            continue
        if k == "energy_kcal" and n["nutrient"].get("unitName", "").lower() != "kcal":
            continue
        vals.setdefault(k, []).append(float(n["amount"]))
    return vals


def usda_csv(zip_path, wanted):
    """Full-precision amounts from an original USDA CSV archive for the wanted FDC ids."""
    import zipfile
    out = {}
    with zipfile.ZipFile(zip_path) as z:
        def table(name):
            member = next(n for n in z.namelist() if n.endswith("/" + name) or n == name)
            return csv.DictReader(io.TextIOWrapper(z.open(member), encoding="utf-8-sig"))
        nutrients = {r["id"]: r for r in table("nutrient.csv")}
        for r in table("food.csv"):
            if int(r["fdc_id"]) in wanted:
                out[int(r["fdc_id"])] = {"description": r["description"], "foodNutrients": []}
        for r in table("food_nutrient.csv"):
            f = out.get(int(r["fdc_id"]))
            if f is not None and r.get("amount") not in (None, ""):
                n = nutrients[r["nutrient_id"]]
                f["foodNutrients"].append({"nutrient": {"name": n["name"], "unitName": n["unit_name"]}, "amount": float(r["amount"])})
    return out


def rda_values(row):
    vals = {}
    for col, k in RDA_COLS.items():
        raw = (row.get(col) or "").strip()
        try:
            vals[k] = [float(raw)]
        except ValueError:
            pass
    return vals


RDA104_LABELS = {"water_g": "수분 (g)", "protein_g": "단백질 (g)", "fat_g": "지방 (g)", "carbohydrate_g": "탄수화물 (g)",
                 "fiber_g": "총 식이섬유 (g)", "sugars_g": "당류 (g)", "calcium_mg": "칼슘 (㎎)", "phosphorus_mg": "인 (㎎)",
                 "potassium_mg": "칼륨 (㎎)", "sodium_mg": "나트륨 (㎎)", "magnesium_mg": "마그네슘 (㎎)", "iron_mg": "철 (㎎)",
                 "vitamin_c_mg": "비타민 C (㎎)", "energy_kcal": "에너지 (㎉)"}


def rda104_values(page):
    """One food of the RDA 10.4 database. A label with no number after it is a blank cell and stays absent."""
    text = re.sub(r"\s+", " ", H.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", page, flags=re.S)))
    name = re.search(r"성분보기 테이블 (.*?) 기본 \(100g\)", text)
    vals = {}
    for k, label in RDA104_LABELS.items():
        m = re.search(r"(?<=\s)" + re.escape(label) + r" ([0-9]+(?:\.[0-9]+)?)(?=\s)", text)
        if m:
            vals[k] = [float(m.group(1))]
    return (name.group(1).strip() if name else None), vals


BLS_HEADS = {"WATER": "water_g", "PROT625": "protein_g", "FAT": "fat_g", "FIBT": "fiber_g", "CA": "calcium_mg", "P": "phosphorus_mg",
             "K": "potassium_mg", "MG": "magnesium_mg", "FE": "iron_mg", "VITC": "vitamin_c_mg", "NA": "sodium_mg"}


def bls_values(xlsx, code):
    """One food row of the BLS workbook, read straight from the xlsx XML (no spreadsheet library needed)."""
    import xml.etree.ElementTree as ET
    import zipfile
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(xlsx)
    shared = []
    for _, el in ET.iterparse(z.open("xl/sharedStrings.xml")):
        if el.tag == ns + "si":
            shared.append("".join(t.text or "" for t in el.iter(ns + "t")))
            el.clear()

    def cells(row):
        out = {}
        for c in row.iter(ns + "c"):
            v = c.find(ns + "v")
            if v is not None:
                out[re.match(r"[A-Z]+", c.get("r")).group(0)] = shared[int(v.text)] if c.get("t") == "s" else v.text
        return out

    head = None
    for _, el in ET.iterparse(z.open("xl/worksheets/sheet1.xml")):
        if el.tag != ns + "row":
            continue
        d = cells(el)
        if head is None:
            head = d
        elif d.get("A") == code:
            vals = {}
            for col, name in head.items():
                k = BLS_HEADS.get(name.split(" ")[0]) if name.endswith("/100g]") else None
                try:
                    if k:
                        vals[k] = [round(float(d[col]), 6)]
                except (KeyError, ValueError):
                    pass
            return d.get("B"), vals
        el.clear()
    return None, {}


def norm_food(s):
    return re.sub(r"[\s,_]+", "", s or "")


def mext_values(page):
    text = re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", page)))
    vals = {}
    for k, label in MEXT_LABELS.items():
        m = re.search(r"(?<=\s)" + re.escape(label) + r"\s+([0-9]+(?:\.[0-9]+)?)\s", text)  # whole label only
        if m:
            vals[k] = [float(m.group(1))]
    return vals


def pmc_rows(xml):
    x = Path(xml).read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"<table-wrap\b.*?</table-wrap>", x, re.S):
        rows = [[H.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
                for r in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(0), re.S)]
        if not rows:
            continue
        for r in rows[1:]:
            for name, val in zip(rows[0][1:], r[1:]):
                m2 = re.match(r"^\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*±", val)
                if m2 and name in PMC_HEADS:
                    out.setdefault(r[0], {})[PMC_HEADS[name]] = float(m2.group(1).replace(",", ""))
    return out


def ifct_values(pdf, code):
    """Column-aligned read of one IFCT 2017 food row across all tables (text layer misaligns names and values)."""
    import pymupdf
    doc = pymupdf.open(pdf)
    out = {}
    for page in doc:
        ws = page.get_text("words")
        codes = [w for w in ws if w[4] == code]
        if not codes:
            continue
        heads = [w for w in ws if w[4] in IFCT_HEADS and w[1] < 140]
        if not heads:
            continue
        yc = (codes[0][1] + codes[0][3]) / 2
        for v in [w for w in ws if abs((w[1] + w[3]) / 2 - yc) < 1.5 and w[0] > codes[0][2] + 15]:
            h = min(heads, key=lambda h: abs((h[0] + h[2]) / 2 - (v[0] + v[2]) / 2))
            if abs((h[0] + h[2]) / 2 - (v[0] + v[2]) / 2) < 4:
                try:
                    out.setdefault(IFCT_HEADS[h[4]], []).append(float(v[4].split("±")[0]))
                except ValueError:
                    pass
    return out


def stored_values(rec):
    src = rec.get("values_per_100g") or rec
    return {k: float(src[k]) for k in NUTRIENT_KEYS if isinstance(src.get(k), (int, float)) and not isinstance(src.get(k), bool)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usda-csv", action="append", default=[])
    for a in ("usda-sr", "usda-foundation", "rda", "ifct", "pmc-6268292", "pmc-8472405", "mext-dir", "rda104-dir", "bls", "out"):
        ap.add_argument("--" + a)
    a = ap.parse_args()
    usda = {}
    for path, key in ((a.usda_sr, "SRLegacyFoods"), (a.usda_foundation, "FoundationFoods")):
        if path:
            usda.update({f["fdcId"]: f for f in json.loads(Path(path).read_text(encoding="utf-8"))[key] if f})
    main_ids = {int(m.group(1)) for r in json.loads((ROOT / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))["plants"]
                for m in [re.match(r"FDC (\d+)", r.get("source_id") or "")] if m}
    usda_full = {}
    for z in a.usda_csv:
        usda_full.update(usda_csv(z, main_ids))
    rda, rda_by_name = {}, {}
    if a.rda:
        rows = list(csv.reader(io.StringIO(Path(a.rda).read_bytes().decode("utf-8-sig"))))
        rda = {r[0]: dict(zip(rows[0], r)) for r in rows[1:]}
        for d in rda.values():
            rda_by_name.setdefault(norm_food(d["식품명"]), []).append(d)
    pmc = {"PMC6268292": pmc_rows(a.pmc_6268292) if a.pmc_6268292 else None, "PMC8472405": pmc_rows(a.pmc_8472405) if a.pmc_8472405 else None}

    main_doc = json.loads((ROOT / "data/plant_nutrition_v56.json").read_text(encoding="utf-8"))
    rda_doc = json.loads((ROOT / "data/rda_food_composition_v56.json").read_text(encoding="utf-8"))
    items = [("plants", r) for r in main_doc["plants"]] + [("part_state_records", r) for r in main_doc.get("part_state_records", [])] + \
            [("rda_food_composition_v56", r) for r in rda_doc.get("records", [])]
    results, bad = [], 0
    for table, rec in items:
        sid = rec.get("source_id") or rec.get("rda_food_code") or ""
        stored = stored_values(rec)
        res = {"table": table, "plant_id": rec["plant_id"], "source_id": sid, "food_description": rec.get("food_description") or rec.get("rda_food_name_ko"),
               "fields": {}, "checks": []}
        src, method, scale = None, None, {}
        m = re.match(r"FDC (\d+)", sid)
        if m:
            f = usda_full.get(int(m.group(1))) or usda.get(int(m.group(1)))
            if f:
                src, method = usda_values(f), "usda_original_csv" if int(m.group(1)) in usda_full else "usda_json"
                if f["description"] != rec.get("food_description"):
                    res["checks"].append("food_description differs from source: " + f["description"])
                res["source_scientific_name"] = (usda.get(int(m.group(1))) or {}).get("scientificName")
        elif sid.startswith("R106-"):
            if sid in rda:
                src, method = rda_values(rda[sid]), "rda_csv_same_release"
                if rda[sid]["식품명"] != rec.get("food_description"):
                    res["checks"].append("food_description differs from source: " + rda[sid]["식품명"])
        elif re.match(r"F\d", sid):
            page = Path(a.rda104_dir) / ("detail_%s.html" % sid) if a.rda104_dir else None
            if page and page.exists():
                name, src = rda104_values(page.read_text(encoding="utf-8", errors="replace"))
                method = "rda_10.4_detail_page"
                res["source_food_name"] = name
                stored_name = rec.get("food_description") or rec.get("rda_food_name_ko") or ""
                if name and norm_food(name) not in norm_food(stored_name) and table != "rda_food_composition_v56":
                    res["checks"].append("food_description differs from source: " + name)
        elif sid.startswith("BLS ") and a.bls:
            name, src = bls_values(a.bls, sid.split()[1])
            method = "bls_xlsx"
            res["source_food_name"] = name
        elif sid.startswith("MEXT ") and a.mext_dir:
            p = Path(a.mext_dir) / ("mext_%s.html" % sid.split()[1])
            if p.exists():
                src, method = mext_values(p.read_text(encoding="utf-8", errors="replace")), "mext_item_page"
        elif sid.startswith("IFCT2017 ") and a.ifct:
            src, method = ifct_values(a.ifct, sid.split()[1]), "ifct_pdf_word_positions"
        elif rec.get("source_pmcid") in pmc and pmc[rec["source_pmcid"]]:
            name = rec.get("source_scientific_name")
            row = pmc[rec["source_pmcid"]].get(name)
            if row:
                # published per kg fresh mass; the record stores per 100 g (÷10). Dry matter is a percentage.
                src = {k: [v if k == "dry_matter_pct" else v / 10] for k, v in row.items()}
                method = "pmc_xml_tables_div10"
        if src is None:
            res["status"] = "source_not_supplied"
        else:
            res["method"] = method
            for k, v in stored.items():
                if k in ("calcium_phosphorus_ratio",):
                    continue
                if k not in src:
                    res["fields"][k] = {"stored": v, "result": "not_in_parsed_source"}
                    continue
                verdict, sv = compare(v, src[k])
                res["fields"][k] = {"stored": v, "source": sv, "result": verdict}
            kinds = {f["result"] for f in res["fields"].values()}
            res["status"] = "mismatch" if "mismatch" in kinds else "partly_checked" if "not_in_parsed_source" in kinds else "match"
            if res["status"] == "mismatch":
                bad += 1
        # source-independent checks
        vals = rec.get("values_per_100g") or rec
        ca, p, ratio = vals.get("calcium_mg"), vals.get("phosphorus_mg"), vals.get("calcium_phosphorus_ratio")
        if ratio is not None and ca and p and abs(round(ca / p, 2) - ratio) > 0.011:
            res["checks"].append("Ca:P ratio %s does not equal %s/%s" % (ratio, ca, p))
            bad += 1
        if table != "rda_food_composition_v56":
            if "100 g" not in (rec.get("basis") or ""):
                res["checks"].append("basis is not per 100 g: %r" % rec.get("basis"))
            if rec.get("preparation_state") != "raw":
                res["checks"].append("preparation_state is %r" % rec.get("preparation_state"))
        results.append(res)

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    report = {"schema_version": "1.0", "purpose": "Value-by-value comparison of VERIFIED nutrition records with their original source files. "
                                                 "scripts/qa_nutrition_integrity_v1.py fails when a verified value differs from this ledger.",
              "record_count": len(results), "values_compared": sum(len(r["fields"]) for r in results), "status_counts": counts, "records": results}
    if a.out:
        Path(a.out).write_bytes((json.dumps(report, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    for r in results:
        probs = [k + "=" + str(f["stored"]) + " vs " + str(f.get("source")) for k, f in r["fields"].items() if f["result"] == "mismatch"]
        miss = [k for k, f in r["fields"].items() if f["result"] == "not_in_parsed_source"]
        print("%-10s %-18s %-22s %-28s %s %s %s" % (r["status"], r["plant_id"], r["source_id"][:22], r.get("method", "-")[:28], "; ".join(probs),
                                                 ("unparsed:" + ",".join(miss)) if miss else "", " | ".join(r["checks"])))
    print(counts)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
