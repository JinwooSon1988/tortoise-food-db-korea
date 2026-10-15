#!/usr/bin/env python3
"""Compare every record in data/plant_nutrition_reference_v1.json with its original source (manual, network/cache).

Sources with a machine-readable original are parsed and compared value by value:
  * Feedipedia node pages (feed tables: Avg and Nb per nutrient, % DM / g/kg DM, dry matter % as fed)
  * MEXT Standard Tables of Food Composition in Japan (fooddb.mext.go.jp item pages, per 100 g edible portion)
  * Norwegian Food Composition Table (matvaretabellen.no food pages, per 100 g edible portion)
  * JIRCAS Thai vegetable database pages
Journal articles and PDFs are reported as "manual" with the location recorded in the record; they are checked by hand
and the result is written in docs/NUTRITION_REFERENCE_SOURCE_VERIFICATION_20261010.md.

Pages are read from --cache (one file per source, see fetch_name()); with --fetch, missing pages are downloaded politely
(Feedipedia crawl-delay 10 s). Nothing in data/ is modified. Output: a JSON report on stdout or --out.

  python scripts/verify_nutrition_reference_sources_v1.py --cache <dir> [--fetch] [--out report.json]
"""
import argparse, html, json, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "tortoise-food-db-korea nutrition source verification (https://jinwooson1988.github.io/tortoise-food-db-korea/)"

FEEDIPEDIA_LABELS = {
    "dry_matter_pct_as_fed": ("dry matter", "% as fed"), "crude_protein_pct_dm": ("crude protein", "% dm"),
    "crude_fibre_pct_dm": ("crude fibre", "% dm"), "ndf_pct_dm": ("ndf", "% dm"), "adf_pct_dm": ("adf", "% dm"),
    "lignin_pct_dm": ("lignin", "% dm"), "ether_extract_pct_dm": ("ether extract", "% dm"), "ash_pct_dm": ("ash", "% dm"),
    "total_sugars_pct_dm": ("total sugars", "% dm"), "starch_pct_dm": ("starch", "% dm"),
    "water_soluble_carbohydrates_pct_dm": ("water-soluble carbohydrates", "% dm"),
    "gross_energy_mj_per_kg_dm": ("gross energy", "mj/kg dm"),
    "calcium_g_per_kg_dm": ("calcium", "g/kg dm"), "phosphorus_g_per_kg_dm": ("phosphorus", "g/kg dm"),
    "potassium_g_per_kg_dm": ("potassium", "g/kg dm"), "sodium_g_per_kg_dm": ("sodium", "g/kg dm"),
    "magnesium_g_per_kg_dm": ("magnesium", "g/kg dm"), "manganese_mg_per_kg_dm": ("manganese", "mg/kg dm"),
    "zinc_mg_per_kg_dm": ("zinc", "mg/kg dm"), "copper_mg_per_kg_dm": ("copper", "mg/kg dm"),
    "iron_mg_per_kg_dm": ("iron", "mg/kg dm"),
}
MEXT_LABELS = {"water_g": "水分", "protein_g": "たんぱく質", "fat_g": "脂質", "carbohydrate_g": "炭水化物",
               "fiber_g": "食物繊維総量", "calcium_mg": "カルシウム", "phosphorus_mg": "リン", "vitamin_c_mg": "ビタミンC",
               "potassium_mg": "カリウム", "magnesium_mg": "マグネシウム", "iron_mg": "鉄", "sodium_mg": "ナトリウム",
               "zinc_mg": "亜鉛", "ash_g": "灰分"}
JIRCAS_LABELS = {"water_g": "water", "protein_g": "protein", "fat_g": "fat", "carbohydrate_g": "carbohydrate",
                 "fiber_g": "fiber", "calcium_mg": "calcium", "phosphorus_mg": "phosphorus", "vitamin_c_mg": "vitamin c",
                 "iron_mg": "iron"}


def flat(page):
    t = html.unescape(re.sub(r"<[^>]+>", "|", page))
    return re.sub(r"\s*\|\s*(\|\s*)*", "|", t)


def num(x):
    try:
        return float(str(x).replace(",", "").strip("()"))
    except ValueError:
        return None


def fetch_name(url):
    if "feedipedia" in url:
        return "feedipedia_" + re.search(r"node/(\d+)", url).group(1) + ".html"
    if "fooddb.mext.go.jp" in url:
        return "mext_" + re.search(r"ITEM_NO=\d+_(\d+)_", url).group(1) + ".html"
    if "jircas" in url:
        return "jircas_" + url.rstrip("/").split("/")[-1] + ".html"
    if "matvaretabellen" in url:
        return "matv_" + url.rstrip("/").split("/")[-1] + ".html"
    return None


def parse_feedipedia(page):
    """Feedipedia composition rows, read cell by cell from each table row (scripts/feedipedia_table.py).
    The former flattened-text regex let a row with a blank Nb take the Nb of the next row and drop that row."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("feedipedia_table", Path(__file__).resolve().parent / "feedipedia_table.py")
    ft = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ft)
    return ft.legacy(page)


def parse_mext(page):
    t = flat(page)
    out = {}
    for key, label in MEXT_LABELS.items():
        m = re.search(r"\|" + re.escape(label) + r"\|([0-9.()]+|Tr|-|\(Tr\))\|(g|mg|μg)\|", t)
        if m:
            out[key] = num(m.group(1))
    name = re.search(r"食品名：\|([^|]+)\|", t)
    sci = re.search(r"学名：\|([^|]+)\|", t)
    return out, (name.group(1) if name else None), (sci.group(1) if sci else None)


def parse_matv(page):
    """Rows: | Label (symbol) | source code | value | unit |"""
    t = flat(page).lower()
    out = {}
    pairs = {"water_g": "water", "protein_g": "protein", "fat_g": "fat", "carbohydrate_g": "carbohydrate",
             "fiber_g": "dietary fibre", "calcium_mg": "calcium (ca)", "phosphorus_mg": "phosphorus (p)",
             "potassium_mg": "potassium (k)", "magnesium_mg": "magnesium (mg)", "iron_mg": "iron (fe)", "sodium_mg": "sodium (na)",
             "vitamin_c_mg": "vitamin c (askorbic acid)", "zinc_mg": "zinc (zn)"}
    for key, label in pairs.items():
        m = re.search(r"\|" + re.escape(label) + r"\|[^|]*\|([0-9]+(?:[.,][0-9]+)?)\|(g|mg|µg|μg)\|", t)
        if m:
            out[key] = num(m.group(1))
    return out


def parse_jircas(page):
    """Sentence form: 'Contains 91.6 g water, 1.1 g protein, ... 138 mg calcium ... per 100-g serving.'"""
    t = flat(page).lower()
    out = {}
    words = {"water": "water_g", "protein": "protein_g", "fat": "fat_g", "carbohydrates": "carbohydrate_g", "fibre": "fiber_g",
             "fiber": "fiber_g", "vitamin c": "vitamin_c_mg", "calcium": "calcium_mg", "phosphorus": "phosphorus_mg", "iron": "iron_mg"}
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?) (g|mg) (water|protein|fat|carbohydrates|fibre|fiber|vitamin c|calcium|phosphorus|iron)\b", t):
        out.setdefault(words[m.group(3)], float(m.group(1)))
    return out


def get(url, cache, fetch):
    name = fetch_name(url)
    if not name:
        return None, None
    f = cache / name
    if not f.exists() and fetch:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        time.sleep(11 if "feedipedia" in url else 2)
    return (f.read_text(encoding="utf-8", errors="replace") if f.exists() else None), name


def close(a, b):
    return a is not None and b is not None and abs(a - b) <= 1e-9 + 0.0005 * max(abs(a), abs(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    recs = json.loads((ROOT / "data/plant_nutrition_reference_v1.json").read_text(encoding="utf-8"))["records"]
    report = []
    for r in recs:
        url = r.get("source_url", "")
        page, name = get(url, cache, args.fetch)
        entry = {"reference_id": r["reference_id"], "plant_id": r["plant_id"], "source_url": url, "checked": [], "mismatch": [],
                 "not_in_source": [], "sample_count_mismatch": []}
        if page is None:
            entry["result"] = "manual"
            report.append(entry)
            continue
        nutrients = r.get("nutrients", {})
        if "feedipedia" in url:
            rows, title = parse_feedipedia(page)
            entry["source_title"] = title
            for k, v in nutrients.items():
                lab = FEEDIPEDIA_LABELS.get(k)
                if not lab or lab not in rows:
                    entry["not_in_source"].append(k)
                    continue
                avg, nb = rows[lab]
                (entry["checked"] if close(v, avg) else entry["mismatch"]).append(k if close(v, avg) else f"{k}: record {v} vs source {avg}")
                sc = (r.get("sample_counts") or {}).get(k)
                # Feedipedia prints "*" in the Nb column for values calculated by equation; the records store "equation".
                if sc is not None and nb is not None and sc != ("equation" if nb == "*" else nb):
                    entry["sample_count_mismatch"].append(f"{k}: record n={sc} vs source n={nb}")
        else:
            if "mext" in url:
                src, fname, sci = parse_mext(page)
                entry["source_title"], entry["source_scientific"] = fname, sci
            elif "matvaretabellen" in url:
                src = parse_matv(page)
            else:
                src = parse_jircas(page)
            for k, v in nutrients.items():
                if k not in src:
                    entry["not_in_source"].append(k)
                elif close(v, src[k]):
                    entry["checked"].append(k)
                else:
                    entry["mismatch"].append(f"{k}: record {v} vs source {src[k]}")
        entry["result"] = "mismatch" if entry["mismatch"] or entry["sample_count_mismatch"] else ("partial" if entry["not_in_source"] else "match")
        report.append(entry)
    out = json.dumps(report, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
    from collections import Counter
    print(Counter(e["result"] for e in report))
    for e in report:
        if e["result"] in ("mismatch", "partial"):
            print(e["result"].upper(), e["reference_id"], e["mismatch"][:4], e["sample_count_mismatch"][:3], "not in source:", e["not_in_source"][:6])


if __name__ == "__main__":
    main()
