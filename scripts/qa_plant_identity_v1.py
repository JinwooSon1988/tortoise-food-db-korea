#!/usr/bin/env python3
"""Regression test for plant identity: duplicates, name/alias collisions, taxon overlaps and legacy alias IDs.

Every collision in data/plants.json must be declared, with its reason, in data/plant_identity_registry_v1.json.
A new plant that reuses a scientific name, a Korean/English name or a search alias of an existing plant fails this
test until the relation is reviewed and declared. Nothing is merged automatically: a shared scientific name alone
is not proof that two records are the same food (different parts and growth stages are separate records).

Also checks that data/plant_taxonomy_audit_v1.json (GBIF / Kew WCVP / WFO comparison) covers the current plant
list, so a renamed or added plant cannot skip the taxonomy check.
"""
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def norm(s):
    return " ".join(unicodedata.normalize("NFKC", s or "").lower().split())


def genus_level(sci):
    return sci.strip().endswith(("spp.", "spp"))


def species_key(sci):
    """Genus + epithet without hybrid sign, authors or infraspecific rank; None for genus-level names."""
    t = sci.replace("×", " ").split()
    return None if genus_level(sci) or len(t) < 2 else norm(t[0] + " " + t[1])


def main():
    plants = load("data/plants.json")
    reg = load("data/plant_identity_registry_v1.json")
    by_id = {p["id"]: p for p in plants}
    errors = []

    def err(msg):
        errors.append(msg)

    # --- registry refers only to existing plants
    aliases = {a["legacy_id"]: a["canonical_id"] for a in reg["canonical_aliases"]}
    declared_ids = set(aliases) | set(aliases.values())
    for g in reg["same_taxon_groups"]:
        declared_ids |= {m["id"] for m in g["members"]}
    for g in reg["taxon_overlaps"]:
        declared_ids |= set(g["broader_ids"]) | set(g["narrower_ids"])
    for c in reg["declared_name_collisions"]:
        declared_ids |= set(c["ids"])
    for pid in sorted(declared_ids - set(by_id)):
        err("registry names unknown plant id: " + pid)

    # --- 1. identical scientific names
    by_sci = defaultdict(list)
    for p in plants:
        by_sci[norm(p["scientific"])].append(p["id"])
    declared_groups = {frozenset(m["id"] for m in g["members"]) for g in reg["same_taxon_groups"]}
    alias_pairs = {frozenset((a, b)) for a, b in aliases.items()}  # only true duplicates may share names and search terms
    declared_groups |= alias_pairs
    for sci, ids in by_sci.items():
        if len(ids) > 1 and frozenset(ids) not in declared_groups:
            err("undeclared plants sharing scientific name %r: %s" % (sci, sorted(ids)))
    for g in reg["same_taxon_groups"]:
        ids = [m["id"] for m in g["members"]]
        if any(i in by_id for i in ids) and len({norm(by_id[i]["scientific"]) for i in ids if i in by_id}) != 1:
            err("same_taxon_group %s no longer shares one scientific name" % ids)
        if any(not m.get("part") for m in g["members"]) or not g.get("relation") or not g.get("decision"):
            err("same_taxon_group %s needs part, relation and decision" % ids)

    # --- 2. identical display names
    name_ok = {(c["field"], norm(c["value"])): frozenset(c["ids"]) for c in reg["declared_name_collisions"]}
    for field in ("ko", "en"):
        seen = defaultdict(list)
        for p in plants:
            seen[norm(p[field])].append(p["id"])
        for value, ids in seen.items():
            if len(ids) > 1 and frozenset(ids) not in alias_pairs and name_ok.get((field, value)) != frozenset(ids):
                err("undeclared plants sharing %s name %r: %s" % (field, value, sorted(ids)))

    # --- 3. search terms must resolve to one plant (declared name collisions and alias pairs excepted)
    terms = defaultdict(set)
    for p in plants:
        for t in [p["ko"], p["en"]] + list(p.get("aliases") or []) + list(p.get("search_aliases") or []):
            terms[norm(t)].add(p["id"])
    allowed_terms = {v for (_, v) in name_ok}
    for term, ids in sorted(terms.items()):
        if len(ids) > 1 and frozenset(ids) not in alias_pairs and term not in allowed_terms:
            err("search term %r resolves to several plants: %s" % (term, sorted(ids)))
    for p in plants:
        for t in list(p.get("aliases") or []) + list(p.get("search_aliases") or []):
            owners = [q["id"] for q in plants if q["id"] != p["id"] and norm(t) in (norm(q["ko"]), norm(q["en"]))]
            owners = [o for o in owners if frozenset((o, p["id"])) not in alias_pairs]
            if owners:
                err("alias %r of %s is the primary name of %s" % (t, p["id"], owners))

    # --- 4. broader and narrower taxa that coexist (genus-level vs species, species vs infraspecific)
    declared_overlap = {(b, n) for g in reg["taxon_overlaps"] for b in g["broader_ids"] for n in g["narrower_ids"]}
    by_genus, by_species = defaultdict(list), defaultdict(list)
    for p in plants:
        by_genus[norm(p["scientific"].split()[0])].append(p)
        if species_key(p["scientific"]):
            by_species[species_key(p["scientific"])].append(p)
    expected = set()
    for group in by_genus.values():
        for b in group:
            if genus_level(b["scientific"]):
                expected |= {(b["id"], n["id"]) for n in group if not genus_level(n["scientific"])}
    for key, group in by_species.items():
        for b in group:
            if norm(" ".join(b["scientific"].replace("×", " ").split()[:2])) == norm(b["scientific"].replace("×", " ")):
                expected |= {(b["id"], n["id"]) for n in group if norm(n["scientific"]) != norm(b["scientific"])}
    for pair in sorted(expected - declared_overlap):
        err("undeclared taxon overlap (broader, narrower): %s" % (pair,))
    for pair in sorted(declared_overlap - expected):
        err("declared taxon overlap no longer exists: %s" % (pair,))

    # --- 5. legacy alias IDs: same plant, same verdict, records only on the canonical ID
    assessments = defaultdict(list)
    for a in load("data/public_assessments.json"):
        assessments[a["plant_id"]].append(a)
    images = {i["plant_id"]: i for i in load("data/verified_plant_images_v56.json")["images"]}
    nutrition = load("data/plant_nutrition_v56.json")
    record_owners = {r["plant_id"] for r in nutrition["plants"]} | {r["plant_id"] for r in nutrition.get("part_state_records", [])} | \
                    {r["plant_id"] for r in load("data/plant_nutrition_reference_v1.json")["records"]} | \
                    {r["plant_id"] for r in load("data/rda_food_composition_v56.json")["records"]}
    for legacy, canonical in aliases.items():
        if legacy not in by_id or canonical not in by_id:
            continue
        if norm(by_id[legacy]["scientific"]) != norm(by_id[canonical]["scientific"]):
            err("alias %s -> %s: scientific names differ" % (legacy, canonical))

        def key(pid):
            return sorted((a["species_group"], a["verdict"], a["confidence"], tuple(sorted(a.get("evidence_ids", [])))) for a in assessments[pid])
        if key(legacy) != key(canonical):
            err("alias %s -> %s: feeding verdict, confidence or evidence differ" % (legacy, canonical))
        if (images.get(legacy) or {}).get("source_url") != (images.get(canonical) or {}).get("source_url"):
            err("alias %s -> %s: verified images differ" % (legacy, canonical))
        if legacy in record_owners:
            err("alias %s still owns nutrition records; move them to %s" % (legacy, canonical))
        missing = [t for t in [by_id[legacy]["ko"], by_id[legacy]["en"]] + list(by_id[legacy].get("aliases") or [])
                   if norm(t) not in {norm(x) for x in [by_id[canonical]["ko"], by_id[canonical]["en"]] + list(by_id[canonical].get("aliases") or [])}]
        if missing:
            err("alias %s -> %s: search terms missing on canonical record: %s" % (legacy, canonical, missing))

    # --- 6. taxonomy audit is current and every disputed name carries a decision
    audit = {r["plant_id"]: r for r in load("data/plant_taxonomy_audit_v1.json")["plants"]}
    decisions = {d["plant_id"]: d for d in reg["nomenclature_decisions"]}
    for p in plants:
        row = audit.get(p["id"])
        if not row or row["db_scientific"] != p["scientific"]:
            err("taxonomy audit is stale for %s: run scripts/build_plant_taxonomy_audit_v1.py" % p["id"])
            continue
        synonym_sources = [s for s in ("gbif", "wcvp", "wfo") if s + "_treats_as_synonym" in row["flags"]]
        ambiguous = [f for f in row["flags"] if f.endswith("_homonym_ambiguous")]
        needs = len(synonym_sources) >= 2 or (ambiguous and row["level"] != "genus")
        if needs and p["id"] not in decisions:
            err("%s (%s): %s but no nomenclature decision is recorded" % (p["id"], p["scientific"], ", ".join(synonym_sources + ambiguous)))
    for pid, d in decisions.items():
        if pid in by_id and d.get("db_scientific") != by_id[pid]["scientific"]:
            err("nomenclature decision for %s refers to %r, plants.json has %r" % (pid, d.get("db_scientific"), by_id[pid]["scientific"]))

    if errors:
        print("plant identity QA failed (%d):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("plant identity QA ok: %d plants, %d same-taxon groups, %d taxon overlaps, %d legacy aliases, %d nomenclature decisions"
          % (len(plants), len(reg["same_taxon_groups"]), len(declared_overlap), len(aliases), len(decisions)))


if __name__ == "__main__":
    main()
