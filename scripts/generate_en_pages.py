#!/usr/bin/env python3
"""English site: plant detail pages (en/plant/<id>/), the English home, all-plants list and guides (scripts/en_hubs.py), the
bilingual sitemap and data/i18n/en/catalog_en.json.

Run after the Korean pipeline (generate_static_pages -> patch_curated_social_metadata -> inject_plant_detail_v56
-> generate_guide_hubs). Facts come from the same canonical files as the Korean pages; Korean prose stored in those
files is translated through data/i18n/en/strings_en.json (scripts/i18n_en.py). Visual design is shared: each English
page reuses the <style> block of the matching Korean page.

  python scripts/generate_en_pages.py            # build; fails if any Korean source string has no English entry
  python scripts/generate_en_pages.py --collect  # list untranslated strings to data/i18n/en/_missing.json, build nothing
"""
import html, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_verdict import load_assessments, representative, species_notes, by_plant, public_plants
from feeding_cautions import classify, dedupe, localize_specialist_labels
from assessment_copy import assessment_copy
import i18n_en as I
import en_hubs

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://jinwooson1988.github.io/tortoise-food-db-korea"
COLLECT = "--collect" in sys.argv
T = I.T

load = lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))
all_plants = load("data/plants.json")
assessments = load_assessments()
rows_by = by_plant(assessments)
plants = public_plants(all_plants, assessments)
evidence_by_id = {e["id"]: e for e in load("data/public_evidence_records.json").get("records", [])}
nutrition_by_id = {n["plant_id"]: n for n in load("data/plant_nutrition_v56.json").get("plants", []) if n.get("verification_status") == "verified"}
wild_by_plant = {}
for w in load("data/wild_feeding_evidence.json").get("records", []):
    wild_by_plant.setdefault(w.get("plant_id"), []).append(w)
risk_by_plant = {r.get("plant_id"): r for r in load("data/wild_candidate_risk_screening.json").get("records", [])}
ibera = load("data/ibera_direct_feeding_evidence_v56.json")
ibera_sources = {s["source_id"]: s for s in ibera.get("sources", [])}
ibera_by_plant = {}
for o in ibera.get("observations", []):
    if o.get("plant_id"):
        ibera_by_plant.setdefault(o["plant_id"], []).append(o)
image_by_plant = {i["plant_id"]: i for i in load("data/verified_plant_images_v56.json").get("images", []) if i.get("identity_scope") in {"exact_species", "exact_subspecies", "exact_variety"}}
curated_identity = load("data/curated_identity_notes.json").get("notes", {})
retail_by_id = {r["plant_id"]: r for r in load("data/korean_retail_name_map.json")}

esc = lambda v: html.escape(str(v or ""), quote=True)
rich = lambda v: re.sub(r"\*([^*]+)\*", r"<i>\1</i>", esc(v))
NEWTAB = '<span class="sr-only"> (opens in a new tab)</span>'

DETAIL_ICON_CSS = (".detailnavlinks .iconnav-home,.detailnavlinks .iconnav-back{display:inline-flex;align-items:center;justify-content:center;min-width:54px;min-height:52px;padding:10px;box-sizing:border-box}.detailnavlinks svg{flex:none}.detailnav .langswitch a[aria-current=\"page\"],.detailnav .langswitch a.active{background:#286a46!important;color:#fff!important}")

LANG_CSS = (".langswitch{display:inline-flex;align-items:stretch;border:1px solid #c9d8cd;border-radius:12px;overflow:hidden;background:#fff}"
            ".langswitch a,.langswitch strong{display:inline-flex;align-items:center;min-height:44px;padding:0 13px;font-size:13px;font-weight:850;text-decoration:none;color:#174d32}"
            ".langswitch strong{background:#286a46;color:#fff}.langswitch a:hover{background:#edf4ef}.topmeta{margin-left:auto}"
            ".detailnav .langswitch a{min-width:0;border:0;border-radius:0;box-shadow:none;background:#fff;color:#174d32}.detailnav .langswitch a:hover{background:#edf4ef;color:#174d32}"
            "@media(max-width:380px){.detailnav{gap:6px}.detailnav a,.detailnav button{min-width:0;padding:0 11px}.langswitch a,.langswitch strong{padding:0 9px}}")


def lang_switch(ko_href, en_current=True):
    if en_current:
        return f'<nav class="langswitch" aria-label="Language"><a href="{ko_href}?lang=ko" hreflang="ko" lang="ko">한국어</a><a href="./?lang=en" hreflang="en" lang="en" aria-current="page" class="active">English</a></nav>'
    return f'<nav class="langswitch" aria-label="언어"><strong aria-current="page">한국어</strong><a href="{ko_href}" hreflang="en" lang="en">English</a></nav>'


def credit_name(creator):
    """Licence attribution keeps the creator's name exactly as published; a Korean name is marked lang="ko"."""
    c = str(creator or "").strip()
    if not c:
        return "Photo source"
    return f'<span lang="ko">{esc(c)}</span>' if I.HANGUL.search(c) else esc(c)


def source_kind_en(e):
    """Same rules and ranks as source_kind() in generate_static_pages.py, so card order and labels match the Korean page."""
    t = str(e.get("source_type") or "")
    if t.startswith("peer_reviewed") or e.get("pmid"):
        return (0, "Peer-reviewed paper")
    if t.startswith("academic") or t == "conference_proceedings":
        return (1, "Academic research")
    if t.startswith("veterinary") or "veterinary" in t:
        return (2, "Veterinary source")
    if t.startswith("specialist") or t.startswith("expert"):
        return (3, "Specialist husbandry or plant source")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t:
        return (4, "Plant identification / taxonomy")
    if "nutrition" in t or "food_composition" in t:
        return (5, "Composition reference")
    if t.startswith("regulatory_"):
        return (6, "Official assessment")
    return (7, "Other public or contextual source")


def evidence_role_en(e):
    t = str(e.get("source_type") or "")
    if "taxonomy" in t or "taxonomic" in t or "botanical" in t or "biodiversity" in t or "agriculture" in t:
        return "Supports the plant's name, classification and identity. It does not show feeding safety."
    if "nutrition" in t or "food_composition" in t:
        return "A composition reference. It does not show feeding safety."
    if e.get("directness") == "direct":
        return "Directly supports the current feeding conclusion."
    return "Indirect evidence that supplements the current conclusion. It does not decide safety on its own."


def en_text(v, where):
    """Data field shown on an English page: English originals pass through; Korean goes through the dictionary."""
    return T(v, where)


def concise_part_en(v):
    v = en_text(v, "part").strip()
    v = re.split(r";|\s[—–]\s", v, maxsplit=1)[0].strip()
    low = v.lower()
    if not v or low.startswith(("as specified", "as described", "part/state", "identity only", "see linked", "species-level use", "genus-level", "plant; genus")):
        return ""
    if low in {"plant", "plant material", "whole plant", "wild plant material", "plant material/new untreated growth"}:
        return "plant"
    return v


def nutrition_basis_en(v):
    v = str(v or "").strip().lower().replace("_", " ")
    if "rda" in v or "nics" in v:
        return "Per 100 g edible portion (Korean national food composition table, RDA)"
    if "fresh flower" in v:
        return "Per 100 g fresh flower (the paper's mg/kg fresh-weight values converted to 100 g)"
    if "raw" in v:
        return "Per 100 g raw edible portion"
    return "Per 100 g edible portion"


def academic_nutrition_en(nu):
    if nu.get("source_kind") != "academic_peer_reviewed":
        return ""
    out = (f'<p class="small">Data type: primary analysis from a peer-reviewed paper, not a national food composition table '
           f'(open access, {esc(nu.get("source_license"))}). Water and fibre were not measured and are not shown; the dry-matter share is the measured value. '
           f'Citation: {esc(nu.get("source_citation"))}</p>')
    cc = nu.get("independent_crosscheck")
    if cc:
        out += (f'<p class="small">An independent second study (cultivar ‘{esc(cc.get("cultivar"))}’, {esc(str(cc.get("sampling_period", "")).replace("two-year mean", "2-year mean"))}): '
                f'calcium {cc.get("calcium_mg")} mg · phosphorus {cc.get("phosphorus_mg")} mg · Ca:P {cc.get("calcium_phosphorus_ratio")}:1 · dry matter {cc.get("dry_matter_pct")}%. '
                f'The two studies are shown separately and not averaged. <a href="{esc(cc.get("source_url"))}" target="_blank" rel="noopener noreferrer">Original paper{NEWTAB}</a></p>')
    return out


RISK_SIGNAL_EN = {
    "phytochemistry": "Plant chemistry", "acute_toxicity": "Acute toxicity", "nitrate_accumulation": "Nitrate accumulation",
    "veterinary_case_reports": "Veterinary case reports", "saponins": "Saponins", "forage_risk": "Risk factors in forage use",
    "genus_toxicology": "Toxicology of the same genus", "species_specific_gap": "No species-specific data",
    "genus_heterogeneity": "Differences between species in the genus", "related_taxon_cyanogenesis": "Cyanogenic glycosides in related taxa",
    "leaf_irritant": "Irritant compounds in the leaves", "essential_oil_cytotoxicity": "Cytotoxicity of the essential oil",
    "veterinary_extract_toxicology": "Veterinary toxicology of extracts", "extract_toxicity": "Extract toxicity",
    "authoritative_use_flag": "Usage caution in an official source", "species_specific_saponins": "Saponins in this species",
    "forage_context": "Forage-use context", "species_specific_feed_use": "Feed use of this species", "reptile_gap": "No reptile data",
}

VARIETY_GRID = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:10px'


def variety_card_en(title, r, ratio_key):
    ratio = r.get(ratio_key)
    cells = [("Calcium", r.get("calcium_mg"), "mg"), ("Phosphorus", r.get("phosphorus_mg"), "mg"), ("Fibre", r.get("fiber_g"), "g"), ("Vitamin C", r.get("vitamin_c_mg"), "mg")]
    grid = "".join(f'<div>{label} <strong>{"Not confirmed" if v is None else f"{v}{u}"}</strong></div>' for label, v, u in cells)
    grid += f'<div>Ca:P <strong>{"Not confirmed" if ratio is None else f"{ratio}:1"}</strong></div>'
    return (f'<article class="varietycard" style="border:1px solid #dce5dd;border-radius:12px;padding:12px;min-width:0;background:#fff">'
            f'<h3 style="margin:0 0 4px;font-size:15px">{esc(title)}</h3>'
            f'<p class="small" style="margin:0 0 8px;overflow-wrap:anywhere">FDC {esc(r["fdc_id"])} · {esc(r.get("food_description", ""))}</p>'
            f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;font-size:13px">{grid}</div>'
            f'<p class="small" style="margin:9px 0 0"><a class="sourceopen" href="{esc(r["source_url"])}" target="_blank" rel="noopener noreferrer">USDA record{NEWTAB} ↗</a></p></article>')


def special_nutrition_en(pid):
    """English versions of the plant-specific nutrition blocks; values come from the same data files as the Korean blocks."""
    if pid == "mint":
        ms = load("data/mentha_species_nutrition_v1.json")
        parts = []
        for s in ms["species"]:
            n, v, fc = s["nutrition"], s["nutrition"]["values"], s["feeding"]["specialist_database_context"]
            cells = [("Water", v.get("water_g"), "g"), ("Protein", v.get("protein_g"), "g"), ("Fibre", v.get("fiber_g"), "g"), ("Calcium", v.get("calcium_mg"), "mg"),
                     ("Phosphorus", v.get("phosphorus_mg"), "mg"), ("Potassium", v.get("potassium_mg"), "mg"), ("Vitamin C", v.get("vitamin_c_mg"), "mg")]
            grid = "".join(f'<div>{label} <strong>{"Not confirmed" if x is None else f"{x}{u}"}</strong></div>' for label, x, u in cells)
            grid += f'<div>Ca:P <strong>{n["calcium_phosphorus_ratio"]}:1</strong></div>'
            sci = esc(s["scientific_name"]).replace(" L.", "")
            parts.append(
                f'<div class="mintspecies" style="margin-top:14px;padding:14px;border:1px solid #d9e2da;border-radius:14px;background:#fff;min-width:0">'
                f'<h3 style="margin:0 0 2px">{esc(s["en"])} <i lang="la">{sci}</i> L.</h3>'
                f'<p class="small" style="margin:0 0 10px">No verified species photo</p>'
                f'<article class="varietycard" style="border:1px solid #dce5dd;border-radius:12px;padding:12px;min-width:0;background:#f8faf8">'
                f'<h4 style="margin:0 0 4px;font-size:14px">Nutrients · per 100 g raw edible portion</h4>'
                f'<p class="small" style="margin:0 0 8px;overflow-wrap:anywhere">USDA FDC {n["fdc_id"]} · {esc(n["food_description"])} · SR Legacy 2018-04 analytical values</p>'
                f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;font-size:13px">{grid}</div>'
                f'<p class="small" style="margin:8px 0 0">Analysed plant part: <strong>not confirmed</strong> (not stated by USDA; portions are given in leaves). Carbohydrate and energy are calculated values and are not shown; dried mint values are not converted.</p>'
                f'<p class="small" style="margin:6px 0 0"><a class="sourceopen" href="{esc(n["source_url"])}" target="_blank" rel="noopener noreferrer">USDA record{NEWTAB} ↗</a></p></article>'
                f'<div style="margin-top:10px;padding:12px;border:1px dashed #b9c4bb;border-radius:12px;background:#fbfbf7">'
                f'<h4 style="margin:0 0 4px;font-size:14px">Feeding evidence · separate from the nutrient data</h4>'
                f'<p style="margin:0 0 6px"><strong>Site assessment: under review</strong> — no grade has been set for this species, and the mint grade above is not carried over.</p>'
                f'<p class="small" style="margin:0">Specialist tortoise database <a class="sourceopen" href="{esc(fc["url"])}" target="_blank" rel="noopener noreferrer">The Tortoise Table{NEWTAB}</a>: '
                f'<strong>{esc(I.SPECIALIST_LABEL_EN.get(fc["classification"], fc["classification"]))}</strong>. {esc(T(fc["reason_ko"], "mint_reason"))}</p></div></div>')
        return ('<aside class="varietycompare" style="margin-top:14px;padding:14px;border:1px solid #d9e2da;border-radius:12px;background:#f8faf8">'
                '<h3>Mint species: peppermint and spearmint</h3>'
                '<p>“Mint” covers several <i lang="la">Mentha</i> species, so the general entry above stays at “No verified nutrition data”. '
                'The two species below have confirmed identities and are shown separately; they are not values for mint as a whole. Nutrient values do not show that a plant is safe for tortoises.</p>'
                + "".join(parts) +
                '<p class="small">The Korean food plant bakha (<i lang="la">Mentha canadensis</i>) is a different species from peppermint. The Korean RDA “peppermint, raw” record is a literature-collected copy of the USDA data and is not used as separate evidence. '
                '<a href="../../../data/mentha_species_nutrition_v1.json">Structured species data</a></p></aside>')
    if pid == "lettuce":
        d = load("data/plant_nutrition_variety_v1.json")
        labels = {"butterhead": "Butterhead", "red_leaf": "Red leaf", "romaine": "Romaine", "iceberg": "Iceberg", "green_leaf": "Green leaf"}
        recs = d["records"]
        cards = "".join(variety_card_en(labels[r["variety_key"]], r, "calcium_phosphorus_ratio") for r in recs)
        def extreme(k, fn):
            v = fn(r[k] for r in recs)
            return v, " · ".join(labels[r["variety_key"]] for r in recs if r[k] == v)
        ca_hi, ca_hi_n = extreme("calcium_mg", max); ca_lo, ca_lo_n = extreme("calcium_mg", min)
        fb_hi, fb_hi_n = extreme("fiber_g", max); fb_lo, fb_lo_n = extreme("fiber_g", min)
        cp_hi, cp_hi_n = extreme("calcium_phosphorus_ratio", max); cp_lo, cp_lo_n = extreme("calcium_phosphorus_ratio", min)
        summary = (f'<div style="background:#f1f7f2;border:1px solid #c9dfcf;border-radius:12px;padding:12px 14px;margin-top:12px">'
                   f'<h3 style="margin:0 0 8px;font-size:15px">What the 5 types show</h3>'
                   f'<p style="margin:4px 0"><strong>Calcium</strong> highest {esc(ca_hi_n)} {ca_hi}mg · lowest {esc(ca_lo_n)} {ca_lo}mg</p>'
                   f'<p style="margin:4px 0"><strong>Fibre</strong> highest {esc(fb_hi_n)} {fb_hi}g · lowest {esc(fb_lo_n)} {fb_lo}g</p>'
                   f'<p style="margin:4px 0"><strong>Ca:P</strong> {esc(cp_hi_n)} {cp_hi}:1 to {esc(cp_lo_n)} {cp_lo}:1. Nutrient values alone cannot decide feeding suitability.</p></div>')
        return ('<aside class="varietycompare" style="margin-top:14px;padding:14px;border:1px solid #d9e2da;border-radius:12px">'
                '<h3>Lettuce types compared (USDA) · different types of the same species</h3>'
                '<p>Values for 5 types of lettuce (<i lang="la">Lactuca sativa</i>) from USDA SR Legacy 2018-04, per 100 g raw leaf. '
                'They do not necessarily match the cultivars sold locally and do not decide feeding safety or amounts. '
                'They are not representative of lettuce as a whole, so the general entry above stays at “No verified nutrition data”.</p>'
                f'<div style="{VARIETY_GRID}">' + cards + '</div>' + summary +
                '<p class="small">These are nutrient data and do not show suitability or recommended amounts for tortoises. '
                '<a href="../../../data/plant_nutrition_variety_v1.json">Structured data by type</a></p></aside>')
    if pid == "marigold":
        tp = load("data/tagetes_patula_species_nutrition_v1.json")
        def card(r):
            cells = [("Calcium", r["calcium_mg"], "mg"), ("Phosphorus", r["phosphorus_mg"], "mg"), ("Potassium", r["potassium_mg"], "mg"), ("Dry matter", r["dry_matter_pct"], "%"), ("Protein", r["protein_g"], "g")]
            grid = "".join(f'<div>{label} <strong>{v}{u}</strong></div>' for label, v, u in cells) + f'<div>Ca:P <strong>{r["calcium_phosphorus_ratio"]}:1</strong></div>'
            return (f'<article class="varietycard" style="border:1px solid #dce5dd;border-radius:12px;padding:12px;min-width:0;background:#fff">'
                    f'<h3 style="margin:0 0 4px;font-size:15px">French marigold ‘{esc(r["cultivar"])}’</h3>'
                    f'<p class="small" style="margin:0 0 8px;overflow-wrap:anywhere">Whole fresh flowers · per 100 g fresh weight · {esc(r["sampling_period"].replace("two-year mean", "2-year mean"))}, n={r["n"]}</p>'
                    f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;font-size:13px">{grid}</div>'
                    f'<p class="small" style="margin:8px 0 0">Water, fibre and vitamin C: <strong>not confirmed</strong> (not measured)</p>'
                    f'<p class="small" style="margin:6px 0 0">{esc(r["source_citation"].split(". ")[0])} ({esc(r["source_doi"])}) '
                    f'<a class="sourceopen" href="{esc(r["source_url"])}" target="_blank" rel="noopener noreferrer">Original paper{NEWTAB} ↗</a></p></article>')
        fv = tp["feeding_verdict"]
        return ('<aside class="varietycompare" style="margin-top:14px;padding:14px;border:1px solid #d9e2da;border-radius:12px;background:#f8faf8">'
                '<h3>French marigold (<i lang="la">Tagetes patula</i>) flower nutrients by cultivar · not values for all marigolds</h3>'
                '<p>Marigold on this page means the whole genus <i lang="la">Tagetes</i>. The values below are peer-reviewed analyses of fresh flowers of two French marigold cultivars. '
                'They are not representative of all marigolds, so the general entry above stays at “No verified nutrition data”. The two studies are shown separately and not averaged.</p>'
                f'<div style="{VARIETY_GRID}">' + "".join(card(r) for r in tp["records"]) + '</div>'
                '<div style="margin-top:12px;padding:12px 14px;border:1px solid #efc9c6;border-radius:12px;background:#fffafa">'
                '<h3 style="margin:0 0 6px;font-size:15px">French marigold feeding assessment: on hold</h3>'
                '<p style="margin:0">There is no feeding assessment for French marigold on its own. The marigold grade above is not automatically transferred to it, and nutrient values are not used to judge safety. '
                f'However, the specialist tortoise database <a class="sourceopen" href="{esc(fv["context_source"])}" target="_blank" rel="noopener noreferrer">The Tortoise Table{NEWTAB}</a> '
                'classifies the whole genus <i lang="la">Tagetes</i>, including French marigold, as <strong>do not feed</strong>. “On hold” does not mean it is safe to feed.</p></div>'
                '<p class="small">Scientific name: the Korean Ministry of Food and Drug Safety raw-material list (#628) lists French marigold as <i lang="la">Tagetes patula</i> L. The GBIF backbone treats this name as a synonym of <i lang="la">Tagetes erecta</i> L. (African marigold), so its scope can differ between classifications. '
                '<a href="../../../data/tagetes_patula_species_nutrition_v1.json">Structured species data</a></p></aside>')
    if pid == "bellpepper":
        pep = load("data/usda_bellpepper_original_csv_verified_20261008.json")
        review = load("data/bellpepper_feeding_evidence_reassessment_20261008.json")
        color = {"green": "Green", "yellow": "Yellow", "red": "Red", "orange": "Orange"}
        found = [r for r in pep["records"] if r["data_type"] == "Foundation"]
        legacy = [r for r in pep["records"] if r["data_type"] == "SR Legacy"]
        th = 'style="padding:8px 6px;border-bottom:2px solid #dce5dd;text-align:left"'
        rows = "".join(f'<tr><th scope="row" style="padding:7px 6px;text-align:left">{color[r["color"]]}</th><td>{r["calcium_mg_per_100g"]}mg</td><td>{r["phosphorus_mg_per_100g"]}mg</td><td>{r["ca_p_ratio"]}:1</td></tr>' for r in found)
        all_p_gt_ca = all(r["phosphorus_mg_per_100g"] > r["calcium_mg_per_100g"] for r in found)
        tt = next((s for s in review["source_positions"] if "thetortoisetable" in s["url"]), None)
        conflict = (f'<div style="margin-top:12px;padding:12px 14px;border:1px solid #efc9c6;border-radius:12px;background:#fffafa">'
                    f'<h3 style="margin:0 0 6px;font-size:15px">Sources disagree · grade under review</h3>'
                    f'<p style="margin:0">The specialist database <a class="sourceopen" href="{esc(tt["url"])}" target="_blank" rel="noopener noreferrer">The Tortoise Table{NEWTAB}</a> classifies sweet pepper fruit as <strong>do not feed</strong>. '
                    f'Because of this disagreement the site grade ({esc(review["current_site_grade"])}) is under review; nutrient values alone were not used to raise or lower it.</p></div>') if tt else ""
        return ('<aside class="varietycompare" style="margin-top:14px;padding:14px;border:1px solid #d9e2da;border-radius:12px">'
                '<h3>Sweet pepper fruit by colour (USDA) · checked against the original records</h3>'
                '<p>Per 100 g raw edible fruit. Records are kept separate by colour and data type and are not averaged. Nutrient values do not mean the fruit is allowed.</p>'
                f'<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px"><caption class="sr-only">USDA Foundation Foods 2026-04 sweet pepper fruit calcium and phosphorus by colour</caption>'
                f'<thead><tr><th scope="col" {th}>Colour</th><th scope="col" {th}>Calcium</th><th scope="col" {th}>Phosphorus</th><th scope="col" {th}>Ca:P</th></tr></thead><tbody>{rows}</tbody></table></div>'
                + (f'<p><strong>Key point:</strong> in all {len(found)} colours in USDA Foundation Foods, phosphorus exceeds calcium. The calcium balance of a whole diet cannot be judged from one food.</p>' if all_p_gt_ca else '')
                + conflict +
                '<details style="margin-top:10px"><summary>Original records and additional data</summary><p class="small">Foundation Foods 2026-04: '
                + " · ".join(f'<a href="{esc(r["source_url"])}" target="_blank" rel="noopener noreferrer">{color[r["color"]]}</a>' for r in found)
                + '. SR Legacy 2018-04 ' + " · ".join(f'<a href="{esc(r["source_url"])}" target="_blank" rel="noopener noreferrer">{color[r["color"]]}</a>' for r in legacy)
                + ' are kept as separate records and not averaged.</p><p class="small">Verification data: <a href="../../../data/usda_bellpepper_original_csv_verified_20261008.json">USDA original-record check</a>. '
                'These records describe the fruit; they are not evidence about leaves or stems or a feeding trial in tortoises.</p></details></aside>')
    return ""


def render(p):
    pid = p["id"]
    name = p.get("en") or pid
    sci = p.get("scientific") or "Scientific name under review"
    rows = rows_by.get(pid, [])
    a = representative(rows)
    g = I.display_en(a)
    grade, label, meaning, tone = g["grade"], g["label"], g["meaning"], g["tone"]
    ko_url = f"{SITE_URL}/plant/{pid}/"
    en_url = f"{SITE_URL}/en/plant/{pid}/"

    # Reason: the same displayed Korean text (assessment_copy) translated; short reasons fall back to the source summary.
    summary_ko = assessment_copy((a or {}).get("why"), a)
    summary = T(summary_ko, f"{pid}.why") if summary_ko else ("There is no public assessment for Mediterranean Testudo or tortoises in general yet. The species-specific notes below apply only to those species." if not a else "Evidence review in progress.")
    linked = [evidence_by_id[e] for e in ((a or {}).get("evidence_ids") or []) if e in evidence_by_id]
    if a and summary_ko and len(summary_ko) < 55:
        facts = [en_text(e.get("supports"), f"{e['id']}.supports") for e in linked if e.get("supports")]
        fact = facts[0] if facts else ""
        if fact:
            bare = bool(re.search(r"(classif|recommend|safe to feed|feed in moderation|feed sparingly|do not feed|allows)", fact, re.I)) and not re.search(
                r"(because|oxal|calcium|toxi|alkaloid|glycoside|tannin|iodine|goitro|starch|sugar|laxative|nitrate|photo|absor|fibre|fiber|observ)", fact, re.I)
            summary = (f"The sources found so far give only a feeding category. They do not explain the biological reason for limiting or excluding the plant, "
                       f"or a safe amount. Tortoise Food DB has therefore set a conservative {grade} grade on that basis and does not add reasons that have not been confirmed."
                       if bare else f"{fact} The assessment therefore applies only to the plant parts and animals the sources actually covered.")

    # Header
    r = retail_by_id.get(pid)
    aliases = [x for x in (p.get("aliases") or []) + ((r or {}).get("aliases") or []) if x and "_" not in x and not I.HANGUL.search(x) and x.lower() != name.lower()]
    aliases = list(dict.fromkeys(aliases))[:6]
    alias_html = f'<div class="aliases">Also known as · {", ".join(esc(x) for x in aliases)}</div>' if aliases else ""
    img = image_by_plant.get(pid)
    cap = {"exact_species": "Reference photo verified to the exact species", "exact_subspecies": "Reference photo verified to the exact subspecies",
           "exact_variety": "Reference photo verified to the exact variety"}.get((img or {}).get("identity_scope"), "")
    photo = (f'<figure class="headphoto"><img src="{esc(img["image_url"])}" alt="{esc(name)} ({esc(sci)}) reference photo" loading="eager" width="132" height="112">'
             f'<figcaption class="small">{cap}{"<br>The plant part in the photo differs from the part that is fed." if img.get("part_match") == "mismatch" else ""}'
             f'<br><a href="{esc(img["source_url"])}" target="_blank" rel="noopener noreferrer">{credit_name(img.get("creator"))}</a> · {esc(img.get("license") or "")}</figcaption></figure>') if img else ""

    decision = (f'<section class="card {tone} decision" data-grade="{esc(grade)}" data-verdict="{esc((a or {}).get("verdict") or "none")}" aria-label="Feeding assessment · {esc(grade)} {esc(label)}">'
                f'<div class="verdictline"><div class="verdict">' + (f'<span class="verdictbadge">{esc(grade)}</span><span class="verdictlabel">{esc(label)}</span>' if grade in "ABCD" else esc(label)) +
                f'</div></div><p class="meaning">{esc(meaning)}</p><p class="decisionwhy"><b>Why this assessment</b>{rich(summary)}</p>'
                f'<a class="evidencelink" href="#evidence">See the evidence ↓</a></section>')

    # How to feed
    role = T((a or {}).get("role"), f"{pid}.role") if (a or {}).get("role") else ""
    parts = []
    for e in linked:
        cp = concise_part_en(e.get("plant_part_state"))
        if cp and cp not in parts:
            parts.append(cp)
    concrete = [x for x in parts if x != "plant"]
    part_note = " · ".join(concrete or parts) or "Plant part not specified"
    quantified = any(re.search(r"(percentage|percent|%|frequency|daily|weekly|per week)", str(e.get("supports") or ""), re.I) for e in linked)
    practical = (f'<section class="card practical"><h2>How to feed</h2><p><b>{esc(I.FEEDING_ACTION_EN.get(grade, I.FEEDING_ACTION_EN["On hold"]))}</b></p>'
                 + (f'<p class="roleline"><span>Role of this plant</span> {esc(role)}</p>' if role else "")
                 + f'<p class="partscope"><span class="partlabel">Part fed</span><strong class="partvalue">{rich(part_note)}</strong>'
                 + (" · Quantities only within the range stated by the source" if quantified else "") + '</p></section>') if a else ""

    # Cautions: grouped by the classification of the displayed Korean text, shown in English.
    ko_limits = dedupe(localize_specialist_labels(assessment_copy(x, a)) for x in ((a or {}).get("limits") or []))
    buckets = {k: [] for k in ("risk", "scope", "practice", "evidence")}
    for t in ko_limits:
        buckets[classify(t)].append(T(t, f"{pid}.limit"))
    caution_parts = []
    for k in ("risk", "scope", "practice", "evidence"):
        items = buckets[k]
        if not items:
            continue
        title, note = I.CAUTION_GROUPS_EN[k]
        lis = "".join(f"<li>{rich(x)}</li>" for x in items)
        if k == "evidence":
            caution_parts.append(f'<details class="cautionevidence" data-caution="evidence"><summary>{esc(title)} ({len(items)})</summary><p class="cautionnote">{esc(note)}</p><ul>{lis}</ul></details>')
        else:
            caution_parts.append(f'<div class="cautiongroup cg-{k}" data-caution="{k}"><h3>{esc(title)}</h3><p class="cautionnote">{esc(note)}</p><ul>{lis}</ul></div>')
    cautions = (f'<section class="card cautions" id="cautions"><h2>Feeding cautions</h2><p class="cautionintro">The detailed conditions of the assessment. Read them together with the grade above.</p>{"".join(caution_parts)}</section>' if caution_parts else "")

    # Species-specific notes (never replace the default verdict)
    sp_rows = []
    for x in species_notes(rows, a):
        xg = I.display_en(x)
        who = T(x.get("display_group"), "display_group") if x.get("display_group") else (x.get("species_group") or x.get("animal_taxon"))
        txt = T(assessment_copy(x.get("why") or x.get("role") or "", x), f"{pid}.species_note") if (x.get("why") or x.get("role")) else "There is a separate assessment for this species."
        sp_rows.append(f'<article class="speciesexception"><div><b>{esc(who)} <i class="small">{esc(x.get("animal_taxon"))}</i></b><span>{esc(xg["grade"] + " · " + xg["label"])}</span></div>'
                       f'<details class="speciesdetail"><summary>Why this species differs and what the evidence covers</summary><p>{rich(txt)}</p></details></article>')
    species_html = (f'<section class="card species-specific"><h2>Evidence confirmed for specific species or subspecies</h2><p class="small">Some evidence studied only a particular species or subspecies. It does not mean the same was confirmed for all tortoises.</p>{"".join(sp_rows)}</section>' if sp_rows else "")

    # Identification alert (same condition as the Korean page)
    identity_warning = bool((r and r.get("mapping_status") == "name_candidate_only") or p.get("identity_status") == "needs_species_level_mapping")
    scope_html = ""
    if identity_warning:
        cur = curated_identity.get(pid)
        cur_html = (f'<p><b>{rich(T(cur["headline"], f"{pid}.identity"))}</b></p><ul>{"".join(f"<li>{rich(T(x, f'{pid}.identity'))}</li>" for x in cur.get("items", []))}</ul>' if cur else "")
        scope_html = (f'<section class="card scopecard" id="scope"><div class="identity-alert" data-identity="alert"><h3>⚠ Check the plant identity</h3>'
                      f'<p>A Korean retail or common name is only a search hint, not a species identification. Confirm the scientific name of any product, cultivated plant or foraged plant.</p>{cur_html}</div></section>')

    # Nutrition
    nu = nutrition_by_id.get(pid)
    if nu:
        def nv(k, unit=""):
            v = nu.get(k)
            return "Not confirmed" if v is None else f"{v}{unit}"
        ratio = nu.get("calcium_phosphorus_ratio")
        note = ("The calcium-to-phosphorus ratio is useful when looking at the whole diet, but this value alone does not decide whether a plant is a good food." if ratio not in (None, "", "—")
                else "Without Ca:P data the ratio is not calculated or estimated.")
        water_cell = (f'<div><b>Dry matter</b><strong>{nu["dry_matter_pct"]}%</strong></div>' if nu.get("water_g") is None and nu.get("dry_matter_pct") is not None
                      else f'<div><b>Water</b><strong>{nv("water_g", " g")}</strong></div>')
        app_note = T(nu.get("applicability_note_ko"), f"{pid}.nutrition_scope") if nu.get("applicability_note_ko") else ""
        nbody = (f'<div class="nutgrid"><div><b>Ca:P</b><strong>{nv("calcium_phosphorus_ratio")}</strong></div><div><b>Calcium</b><strong>{nv("calcium_mg", " mg")}</strong></div>'
                 f'<div><b>Phosphorus</b><strong>{nv("phosphorus_mg", " mg")}</strong></div><div><b>Fibre</b><strong>{nv("fiber_g", " g")}</strong></div>{water_cell}'
                 f'<div><b>Protein</b><strong>{nv("protein_g", " g")}</strong></div></div>'
                 f'<p class="nutmeaning"><b>How this is used in the assessment</b><br>{esc(note)} Limiting compounds such as oxalate, nitrate and glycosides, and actual feeding evidence in tortoises, are covered separately in the evidence below.</p>'
                 f'<p class="small">{esc(nutrition_basis_en(nu.get("basis")))} · Source food name: {esc(T(nu.get("food_description"), f"{pid}.food_description"))} · Source: '
                 f'<a href="{esc(nu.get("source_url"))}" target="_blank" rel="noopener noreferrer">{esc(nu.get("source_name"))} {esc(nu.get("source_id"))}</a></p>'
                 + (f'<p class="small">Scope: {esc(app_note)}</p>' if app_note else "") + academic_nutrition_en(nu))
    else:
        nbody = ('<div class="nutrition-missing"><strong>No verified nutrition data</strong><p>No official nutrient values matching this plant and plant part have been confirmed yet.</p>'
                 '<p class="small">A lack of data does not mean the plant is safe or unsafe. See the feeding assessment and evidence above.</p></div>')
    nutrition = (f'<section class="card" id="nutrition"><h2>Key nutrients and limiting compounds</h2>{nbody}{special_nutrition_en(pid)}'
                 f'<p class="small">Nutrient values support the assessment but never override feeding, veterinary, toxicity or antinutrient evidence on their own. '
                 f'Only verified values are shown, and missing values are never treated as 0.</p></section>')

    # Evidence
    ordered = sorted(linked, key=lambda e: source_kind_en(e)[0])
    cards = []
    for e in ordered:
        url = e.get("url") or (f'https://doi.org/{e["doi"]}' if e.get("doi") else (f'https://pubmed.ncbi.nlm.nih.gov/{e["pmid"]}/' if e.get("pmid") else ""))
        title = en_text(e.get("source_title") or e.get("id"), f"{e['id']}.title")
        link = (f'<a class="sourceopen" href="{esc(url)}" target="_blank" rel="noopener noreferrer" aria-label="Open the source: {esc(title)} (opens in a new tab)">Open source <span aria-hidden="true">↗</span></a>' if url else "")
        rank, kind = source_kind_en(e)
        ids = " · ".join(x for x in ((f'DOI {esc(e["doi"])}' if e.get("doi") else ""), (f'PMID {esc(e["pmid"])}' if e.get("pmid") else ""), (esc(e.get("year")) if e.get("year") else "")) if x)
        cards.append(f'<article class="evcard" data-evidence-id="{esc(e.get("id"))}"><div class="evhead"><span class="{"paper" if rank == 0 else ""}">{esc(kind)}</span><span class="directness">{esc(I.DIRECTNESS_EN.get(e.get("directness"), "Indirect evidence"))}</span></div>'
                     f'<div class="evsummary"><strong>What the source says</strong><p>{rich(en_text(e.get("supports"), e["id"] + ".supports"))}</p></div>'
                     f'<p class="evidence-meaning"><b>Role in this assessment</b><br>{esc(evidence_role_en(e))}</p>'
                     f'<p class="limit"><b>What this source cannot show</b><br>{rich(en_text(e.get("does_not_support"), e["id"] + ".does_not_support"))}</p>'
                     f'<div class="evsource"><h3>{esc(title)}</h3><dl class="evmeta"><dt>Animals studied</dt><dd>{esc(en_text(e.get("animal_taxon"), "animal_taxon") or "Not stated")}</dd>'
                     f'<dt>Plant scope</dt><dd>{rich(en_text(e.get("plant_taxon"), e["id"] + ".plant_taxon") or "Not stated")}</dd>'
                     f'<dt>Part / state</dt><dd>{rich(en_text(e.get("plant_part_state"), e["id"] + ".part") or "Not stated")}</dd></dl>'
                     + (f'<p class="ids">{ids}</p>' if ids else "") + f'{link}</div></article>')
    cards_html = "".join(cards) or "<p>No individual evidence records are linked yet. Do not feed this plant until evidence that it is safe has been found.</p>"
    direct = sum(1 for e in linked if e.get("directness") == "direct")
    husbandry = sum(1 for e in linked if e.get("directness") == "expert_husbandry")
    chips = (f'<div class="evcountnote"><b>Evidence at a glance</b><div class="evstats"><div><span>Linked sources</span><strong>{len(linked)}</strong></div>'
             f'<div><span>Direct evidence</span><strong>{direct}</strong></div><div><span>Husbandry sources</span><strong>{husbandry}</strong></div></div>'
             f'<small>The number of sources is not a safety grade, and sources can overlap.</small>'
             f'<p class="certaintyline">Evidence certainty <b>{esc(I.certainty_en((a or {}).get("confidence")))}</b> · separate from the A–D feeding grade, this shows how direct and sufficient the evidence behind the assessment is. '
             f'<a href="../../guides/research-method/#certainty">What this means</a></p></div>')
    wild = wild_by_plant.get(pid, []); risk = risk_by_plant.get(pid); ib = ibera_by_plant.get(pid, [])
    conflict = ""
    if wild and risk and (risk.get("signals") or risk.get("publication_blocker")):
        items = "".join(f'<li><b>{esc(RISK_SIGNAL_EN.get(x.get("type"), "Risk signal"))}</b> — {rich(T(x.get("finding"), pid + ".risk"))}<br><span class="small">{rich(T(x.get("interpretation"), pid + ".risk"))}</span></li>' for x in risk.get("signals", []))
        conflict = (f'<div class="conflict"><b>⚠ Read this alongside the safety assessment</b><p>Even when a plant has been eaten in the wild, toxicity, antinutrient or veterinary risk information from other animals may also exist. '
                    f'Being eaten in the wild does not by itself make a plant safe in captivity.</p><ul>{items}</ul>'
                    f'<p><b>What would make the conclusion more certain:</b> {rich(T(risk.get("publication_blocker") or "추가 검토 필요", pid + ".risk"))}</p></div>')
    wild_cards = []
    appl = {"direct": "Direct observation of the tortoise concerned", "near_direct": "Wild observation in a related tortoise"}
    for w in wild:
        f = lambda k, d: rich(T(w.get(k), pid + ".wild." + k)) if w.get(k) else d
        wild_cards.append(f'<article class="evcard wildcard" data-evidence-id="{esc(w.get("id"))}"><div class="evhead"><span>Wild feeding record</span><span>{esc(appl.get(w.get("ibera_applicability"), "Which tortoise this applies to needs checking"))}</span></div>'
                          f'<h3>{f("tortoise_taxon", "Tortoise not stated in the source")} · {f("population_region", "Region not stated in the source")}</h3>'
                          f'<dl class="evmeta"><dt>Method</dt><dd>{f("study_method", "Not stated in the source")}</dd><dt>Part eaten</dt><dd>{f("plant_part", "Not stated in the source")}</dd>'
                          f'<dt>Season</dt><dd>{f("season", "Not stated in the source")}</dd><dt>Feeding record</dt><dd>{f("feeding_signal", "Recorded")}</dd></dl>'
                          f'<p class="limit"><b>What this record alone cannot show</b><br>{f("limitations", "A wild feeding record alone cannot set captive amounts or show that unlimited feeding is safe.")}</p>'
                          f'<p class="ids">Name in the source <i>{esc(w.get("plant_taxon_reported"))}</i> · accepted name <i>{esc(w.get("plant_taxon_accepted"))}</i> · {esc(w.get("source_id"))}</p></article>')
    for o in ib:
        s = ibera_sources.get(o.get("source_id"), {})
        scope_txt = "Matches the plant species" if o.get("identity_scope") == "exact_species" else "Genus-level observation — it does not show that this exact species was eaten"
        link = f'<a href="{esc(s.get("url"))}" target="_blank" rel="noopener noreferrer">Original study{NEWTAB}</a>' if s.get("url") else ""
        wild_cards.append(f'<article class="evcard wildcard" data-ibera-direct data-evidence-id="{esc(o.get("source_id"))}"><div class="evhead"><span>Direct wild observation in Greek tortoises</span><span>{esc(scope_txt)}</span></div>'
                          f'<h3><i>{esc(o.get("source_plant"))}</i> · {esc(en_text(s.get("location"), "ibera.location") or "Location to be confirmed")}</h3>'
                          f'<dl class="evmeta"><dt>Tortoise</dt><dd><i>{esc(s.get("taxon") or "Testudo graeca ibera")}</i></dd><dt>Period</dt><dd>{esc(en_text(s.get("study_period"), "ibera.period") or "To be confirmed")}</dd>'
                          f'<dt>Part eaten</dt><dd>{esc(en_text(o.get("observed_part"), "ibera.part") or "To be confirmed")}</dd></dl><p class="ids">{esc(s.get("citation"))} {link}</p></article>')
    wild_section = (f'<h3 style="margin-top:18px">What did tortoises actually eat in the wild?</h3><p class="small">Being eaten in the wild is important evidence, but it does not mean a captive feeding proportion, daily feeding or unlimited safety.</p>{"".join(wild_cards)}' if wild_cards else "")
    n_detail = len(linked) + len(wild_cards)
    detail = (f'<details class="evidencefold"><summary>Show {n_detail} source record{"s" if n_detail != 1 else ""}</summary><div class="evidence-list">{cards_html}{wild_section}</div></details>' if n_detail else cards_html)
    deep = (f'<section class="card evidence-deep" id="evidence"><div class="sectioneyebrow">The evidence in detail</div><h2>Evidence behind the assessment</h2>'
            f'<div class="evidence-core"><h3>What the evidence consists of</h3>{chips}</div>{conflict}{detail}</section>')

    footer = ('<section class="share"><button type="button" onclick="navigator.clipboard.writeText(location.href).then(()=>this.textContent=\'Link copied\')">Copy link</button>'
              '<a href="../../all-plants/">All plants →</a><a href="../../">Search other plants →</a></section>')

    ko_page = (ROOT / "plant" / pid / "index.html").read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", ko_page, re.S).group(1)
    title = f"Can tortoises eat {name}? Feeding assessment and evidence | Tortoise Food DB"
    desc = f"Can you feed {name} ({sci}) to tortoises? Feeding grade, plant identification, scope, cautions and the evidence behind them on one page."
    schema = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": en_url, "inLanguage": "en",
                         "isPartOf": {"@type": "WebSite", "name": "Tortoise Food DB", "url": SITE_URL + "/en/"}}, ensure_ascii=False, separators=(",", ":"))
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow">'
            f'<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{en_url}">'
            f'<link rel="alternate" hreflang="ko" href="{ko_url}"><link rel="alternate" hreflang="en" href="{en_url}"><link rel="alternate" hreflang="x-default" href="{en_url}">'
            f'<meta property="og:type" content="article"><meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="ko_KR"><meta property="og:site_name" content="Tortoise Food DB">'
            f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{en_url}">'
            + (f'<meta property="og:image" content="{esc(img["image_url"])}">' if img else "") +
            f'<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">'
            f'<script type="application/ld+json">{schema}</script><style>{style}{LANG_CSS}{DETAIL_ICON_CSS}</style></head>')
    body = (f'<body><a class="skiplink" href="#main-content">Skip to content</a><header class="detailnav"><nav class="detailnavlinks" aria-label="Page navigation">'
            f'<a href="../../" aria-label="Home" title="Home" class="iconnav-home"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 10 9-7 9 7"/><path d="M5 9v12h14V9"/><path d="M9 21v-7h6v7"/></svg></a><button type="button" aria-label="Back" title="Back" class="iconnav-back" onclick="if(history.length>1)history.back();else location.href=\'../../\'"><svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M5 12h14"/></svg></button></nav>'
            f'<div class="topmeta">{lang_switch(f"../../../plant/{pid}/")}</div></header>'
            f'<main id="main-content" tabindex="-1" data-plant-id="{esc(pid)}"><div class="planthead"><div class="plantidentity"><h1>{esc(name)}</h1><div class="scientific"><i>{esc(sci)}</i></div>{alias_html}</div>{photo}</div>'
            f'{decision}{practical}{cautions}{species_html}{scope_html}{nutrition}{deep}{footer}</main>'
            f'<footer class="pagefooter"><nav class="small" aria-label="Breadcrumb"><a href="../../">Tortoise Food DB</a> › {esc(name)}</nav></footer><script src=\"../../../detail-locale-history.js?v=20261010-2\" defer></script></body></html>')
    return head + body


def catalog_entry(p):
    a = representative(rows_by.get(p["id"], []))
    why = assessment_copy((a or {}).get("why"), a)
    return {"id": p["id"], "name": p.get("en") or p["id"],
            # No general assessment (only species-specific ones): same message as the Korean result card.
            "why": T(why, f"{p['id']}.why") if why else ("" if a else "There is no public assessment for Mediterranean Testudo or tortoises in general yet."),
            "role": T((a or {}).get("role"), f"{p['id']}.role") if (a or {}).get("role") else "",
            "market": I.market_en(p.get("market")),
            "aliases": [x for x in (p.get("aliases") or []) if x and not I.HANGUL.search(x)]}


def write_sitemap():
    """Bilingual sitemap: every Korean URL plus its English counterpart, linked with hreflang alternates."""
    sm = ROOT / "sitemap.xml"
    locs = re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8")) if sm.exists() else []
    ko_locs = [l for l in dict.fromkeys(locs) if "/en/" not in l]
    en_for = {}
    for l in ko_locs:
        rel = l[len(SITE_URL):] if l.startswith(SITE_URL) else None
        if rel is None:
            continue
        if rel == "/all-plants/":
            # The English catalog is a noindex redirect, not an indexable translation.
            continue
        if (ROOT / ("en" + rel) / "index.html").exists():
            en_for[l] = SITE_URL + "/en" + rel
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for l in ko_locs:
        en = en_for.get(l)
        alt = (f'<xhtml:link rel="alternate" hreflang="ko" href="{esc(l)}"/><xhtml:link rel="alternate" hreflang="en" href="{esc(en)}"/><xhtml:link rel="alternate" hreflang="x-default" href="{esc(en)}"/>' if en else "")
        out.append(f"  <url><loc>{esc(l)}</loc>{alt}</url>")
        if en:
            out.append(f"  <url><loc>{esc(en)}</loc>{alt}</url>")
    out.append("</urlset>")
    sm.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(ko_locs), len(en_for)


def main():
    pages = {p["id"]: render(p) for p in plants}
    catalog = [catalog_entry(p) for p in plants]
    if I.missing:
        out = ROOT / "data/i18n/en/_missing.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(I.missing, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if COLLECT:
            print(f"collect: {len(I.missing)} untranslated strings written to {out.relative_to(ROOT)}")
            return
        sys.exit(f"generate_en_pages: {len(I.missing)} Korean source strings have no English entry (see data/i18n/en/_missing.json)")
    if COLLECT:
        pt = ROOT / "data/i18n/en/_passthrough.json"
        pt.write_text(json.dumps(I.passthrough, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"collect: no untranslated strings; {len(I.passthrough)} English data strings shown as stored (see {pt.relative_to(ROOT)})")
        return
    for stale in (ROOT / "data/i18n/en/_missing.json", ROOT / "data/i18n/en/_passthrough.json"):
        if stale.exists():
            stale.unlink()
    root = ROOT / "en/plant"
    if root.exists():
        for d in root.iterdir():
            if d.is_dir() and d.name not in pages:
                import shutil
                shutil.rmtree(d)
    for pid, doc in pages.items():
        d = root / pid
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(doc, encoding="utf-8")
    def write(rel, doc):
        f = ROOT / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(doc, encoding="utf-8")
    hubs = en_hubs.build(plants, rows_by, write)
    (ROOT / "data/i18n/en/catalog_en.json").write_text(json.dumps({"schema_version": "1.0", "plants": catalog}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ko_n, en_n = write_sitemap()
    print(f"generated {len(pages)} English plant pages and {len(hubs)} English hub pages; sitemap {ko_n} Korean URLs, {en_n} with English alternates")


if __name__ == "__main__":
    main()
