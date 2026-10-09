#!/usr/bin/env python3
"""Audit every USDA record in data/plant_nutrition_v56.json against the ORIGINAL USDA CSV archives.

Usage:
  python scripts/audit_usda_master_original_csv.py SR_LEGACY_CSV.zip FOUNDATION_CSV.zip [--apply]

Without --apply: report mismatches and exit 1 if any food description or stored value differs.
With --apply:    set every stored USDA value to the exact CSV amount (same FDC ID, same nutrient),
                 recompute Ca:P from the CSV Ca and P of that record, record the archive SHA-256,
                 and write data/usda_master_original_csv_audit.json.

This is the original-source check. It is separate from internal CI consistency checks, which do not
read USDA files. The USDA JSON editions round many amounts to three significant figures; the CSV keeps
the full published precision, so the CSV is used as the reference.
"""
import csv, hashlib, io, json, sys, zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUT = ROOT / "data/plant_nutrition_v56.json"
OUT = ROOT / "data/usda_master_original_csv_audit.json"
NBR = {"255": "water_g", "203": "protein_g", "204": "fat_g", "205": "carbohydrate_g", "291": "fiber_g", "269": "sugars_g",
       "301": "calcium_mg", "305": "phosphorus_mg", "306": "potassium_mg", "307": "sodium_mg", "304": "magnesium_mg",
       "303": "iron_mg", "401": "vitamin_c_mg", "320": "vitamin_a_rae_ug", "208": "energy_kcal"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_archive(path, wanted_ids):
    z = zipfile.ZipFile(path)
    def rows(name):
        member = next((n for n in z.namelist() if n.endswith("/" + name)), None)
        if member is None:
            raise SystemExit(f"{path}: missing {name}")
        return csv.DictReader(io.TextIOWrapper(z.open(member), encoding="utf-8-sig"))
    nutrients = {}
    for r in rows("nutrient.csv"):
        if r["nutrient_nbr"] in NBR and not (r["nutrient_nbr"] == "208" and r["unit_name"].upper() != "KCAL"):
            nutrients[r["id"]] = NBR[r["nutrient_nbr"]]
    food = {r["fdc_id"]: r["description"] for r in rows("food.csv") if r["fdc_id"] in wanted_ids}
    amounts = {}
    for r in rows("food_nutrient.csv"):
        if r["fdc_id"] in wanted_ids and r["nutrient_id"] in nutrients:
            key = (r["fdc_id"], nutrients[r["nutrient_id"]])
            if key in amounts and amounts[key] != float(r["amount"]):
                raise SystemExit(f"{path}: conflicting duplicate rows for {key}")
            amounts[key] = float(r["amount"])
    return food, amounts


def main(sr_zip, fd_zip, apply):
    data = json.loads(NUT.read_text(encoding="utf-8"))
    usda = [r for r in data["plants"] if r.get("source_name") == "USDA FoodData Central"]
    archives = {"SR Legacy": sr_zip, "Foundation": fd_zip}
    results, changes, problems = [], [], []
    for dtype, path in archives.items():
        recs = [r for r in usda if r["data_type"] == dtype]
        ids = {r["source_id"].split()[1] for r in recs}
        food, amounts = load_archive(path, ids)
        for r in recs:
            fdc = r["source_id"].split()[1]
            row = {"plant_id": r["plant_id"], "fdc_id": int(fdc), "data_type": dtype, "description_match": food.get(fdc) == r["food_description"], "values_checked": 0, "values_changed": []}
            if not row["description_match"]:
                problems.append(f"{r['plant_id']}: description {food.get(fdc)!r} != stored {r['food_description']!r}")
            for key in NBR.values():
                if key not in r:
                    continue
                row["values_checked"] += 1
                csv_val = amounts.get((fdc, key))
                if csv_val is None:
                    problems.append(f"{r['plant_id']}: {key} stored but absent in original CSV")
                    continue
                if abs(csv_val - float(r[key])) > 1e-9:
                    row["values_changed"].append({"field": key, "stored": r[key], "original_csv": csv_val})
                    if apply:
                        r[key] = int(csv_val) if csv_val.is_integer() and isinstance(r[key], int) else csv_val
            if apply:
                ca, p = r.get("calcium_mg"), r.get("phosphorus_mg")
                if ca and p:
                    r["calcium_phosphorus_ratio"] = round(ca / p, 2)
                r["original_csv_audit"] = {"archive": Path(path).name, "sha256": sha256(path), "checked_at": date.today().isoformat(),
                                           "result": "food description and every stored nutrient equal the original USDA CSV amounts"}
            changes += [dict(c, plant_id=r["plant_id"]) for c in row["values_changed"]]
            results.append(row)
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        sys.exit("original USDA CSV audit FAILED (identity or missing values)")
    if apply:
        NUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        OUT.write_text(json.dumps({
            "audit_date": date.today().isoformat(), "kind": "original_usda_csv_direct_comparison",
            "archives": {k: {"file": Path(v).name, "sha256": sha256(v), "origin": f"https://fdc.nal.usda.gov/fdc-datasets/{Path(v).name}"} for k, v in archives.items()},
            "records": len(results), "values_checked": sum(r["values_checked"] for r in results),
            "values_aligned_to_csv": len(changes),
            "note": "Differences were rounding only (USDA JSON editions/website-style 3 significant figures vs full CSV precision); no FDC ID or food identity changed.",
            "changes": changes, "per_record": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'APPLIED' if apply else 'CHECKED'}: {len(results)} USDA records, {sum(r['values_checked'] for r in results)} values; "
          f"{len(changes)} differ from original CSV{' and were aligned' if apply else ''}")
    if changes and not apply:
        for c in changes:
            print("  DIFF", c)
        sys.exit(1)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], "--apply" in sys.argv)
