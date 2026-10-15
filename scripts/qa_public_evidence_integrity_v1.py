#!/usr/bin/env python3
"""Integrity QA for the public evidence layer (data/public_evidence_records.json, data/public_assessments.json).

Fails on problems a script can decide:
  1. an assessment cites an evidence_id that does not exist;
  2. an assessment cites a record whose plant_ids do not include the assessed plant;
  3. identifiers: a record's source_id does not follow from its DOI/PMID/PMCID/URL, its DOI or PMID field disagrees
     with its URL, one DOI/PMID/PMCID/page carries several source_ids, or one source_id carries several DOIs/PMIDs;
  4. same_finding_as points at a missing record, at a record of another source, or at a record that is itself folded;
  5. one assessment cites the same original more than once without saying how the records differ
     (fold a restatement with same_finding_as, or declare the relation in the integrity review);
  6. a record links to a search or listing page instead of the page of the plant;
  7. a The Tortoise Table entry does not name the assessed plant's genus and the record does not declare the transfer;
  8. a record names a species the cited The Tortoise Table entry does not name, without declaring it.

Academic questions a script cannot settle are not passed or failed: they are written to the manual review list in
data/public_evidence_integrity_qa_v1.json (genus-level evidence only, combined entries, multi-plant guidance records
without a per-plant taxon, declared related-taxon use, same-source records whose relation is unread, papers
without DOI/PMID, uncited records).

  python scripts/qa_public_evidence_integrity_v1.py           # CI: run the checks and require the committed report to be current
  python scripts/qa_public_evidence_integrity_v1.py --write   # rewrite the report
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evidence_sources import TT_PLANT, computed_source_id, identifiers, is_listing_url, shown_records, source_of

DATA = ROOT / "data"
REPORT = DATA / "public_evidence_integrity_qa_v1.json"
REVIEW = DATA / "public_evidence_integrity_review_20261015.json"
# Genus names that refer to the same plants under another or older name (accepted name first).
GENUS_SYNONYMS = {"Salvia": {"Rosmarinus"}, "Schedonorus": {"Festuca"}, "Glebionis": {"Chrysanthemum"}, "Pilosella": {"Hieracium"},
                  "Buddleja": {"Buddleia"}, "Solanum": {"Lycopersicon"},
                  "Cucurbita": {"Curcurbita"}}  # "Curcurbita" as printed by the Pumpkin entry
SPECIES_SYNONYMS = {"salvia rosmarinus": {"rosmarinus officinalis"}, "schedonorus arundinaceus": {"festuca arundinacea"},
                    "solanum lycopersicum": {"solanum lycopersicon", "lycopersicon esculentum"}, "citrullus lanatus": {"citrullus lanatis"},
                    "mentha suaveolens": {"mentha sauveolens"}}  # spellings as printed by the source entry
# Words in a record's plant_taxon that declare a deliberate related-taxon or food-concept use of a broader source.
DECLARED = re.compile(r"related|not [A-Z]\. ?[a-z]+|food concept|과거 학명|국내 기준|국화류 맥락|source uses|따로 언급하지 않", re.I)
BINOMIAL = re.compile(r"\b([A-Z][a-z]+) (?:× ?)?([a-z][a-z-]{2,})\b")
NOT_EPITHET = {"spp", "ssp", "sp", "var", "subsp", "and", "esp", "syn", "agg", "included", "tall", "taxa", "taxon", "context", "food", "concept",
               "within", "reported", "only", "leaves", "leaf", "plant", "genus", "group", "fescue", "entry", "related", "formerly"}
PAPER_TYPES = re.compile(r"peer_reviewed|academic_study|journal", re.I)
GENERIC_TAXON = re.compile(r"^(See linked plant concept|Multiple identified|Grasses as a broad|Dandelion, plantain)", re.I)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def binomials(text):
    return {(g, s) for g, s in BINOMIAL.findall(str(text or "")) if s not in NOT_EPITHET}


def genera_named(text):
    return set(re.findall(r"\b([A-Z][a-z]{2,})\b", str(text or "")))


def genera_in_latin(latin):
    """Genera an entry's Latin name covers, without synonyms ("syn.", "formerly") and without cultivar groups."""
    main = re.split(r";? ?syn\.|\(formerly|\(syn", str(latin or ""))[0]
    return {g for g, _ in binomials(main)} | set(re.findall(r"\b([A-Z][a-z]+) s?spp?\b", main))


def unhybrid(text):
    """'Viola x wittrockiana' and 'Fragaria × ananassa' -> 'viola wittrockiana', 'fragaria ananassa'."""
    t = str(text or "").lower().replace("×", " x ")
    return re.sub(r"\s+", " ", re.sub(r"\b([a-z]+\.?) x (?=[a-z])", r"\1 ", t))


def species_on(page_text, genus, epithet):
    """True if the text names genus + epithet, allowing 'G. epithet' abbreviations, spelling variants and synonyms."""
    t = unhybrid(page_text)
    want = {f"{genus} {epithet}".lower()} | SPECIES_SYNONYMS.get(f"{genus} {epithet}".lower(), set())
    for w in want:
        g, e = w.split(" ", 1)
        if w in t or f"{g[0]}. {e}" in t or f"{g[0]}.{e}" in t or re.search(rf"\b{re.escape(g)} {re.escape(e[:5])}", t):
            return True
    return False


def genus_on(page_text, genus):
    names = genera_named(page_text)
    return genus in names or bool(GENUS_SYNONYMS.get(genus, set()) & names)


def run():
    recs = load("public_evidence_records.json")["records"]
    E = {r["id"]: r for r in recs}
    A = load("public_assessments.json")
    P = {p["id"]: p for p in load("plants.json")}
    pages = load("tortoise_table_page_taxa_v1.json")["pages"]
    review_doc = json.loads(REVIEW.read_text(encoding="utf-8"))
    declared_rel = {}
    for s in review_doc["same_source_relations"]:
        if s.get("records"):
            declared_rel[(s["source_id"], s["assessment"][0], s["assessment"][1])] = s
    errors = defaultdict(list)
    manual = defaultdict(list)

    def page_of(r):
        m = TT_PLANT.search(str(r.get("url") or ""))
        return pages.get(str(int(m.group(1)))) if m else None

    def page_text(pg):
        return " ".join([pg.get("latin") or ""] + pg.get("taxa_named_in_text", []))

    # 1, 2
    for a in A:
        for eid in a.get("evidence_ids", []):
            r = E.get(eid)
            if r is None:
                errors["1_unresolved_evidence_id"].append(f"{a['plant_id']}|{a['species_group']}: {eid}")
            elif a["plant_id"] not in (r.get("plant_ids") or []):
                errors["2_plant_not_covered_by_record"].append(f"{a['plant_id']}|{a['species_group']}: {eid} covers {r.get('plant_ids')}")

    # 3
    by_identifier = defaultdict(set)
    by_source = defaultdict(lambda: {"doi": set(), "pmid": set()})
    for r in recs:
        i = identifiers(r)
        sid = source_of(r)  # the stored source_id, or the one its identifiers give when it is missing
        if r.get("source_id") is None:
            errors["3_identifiers"].append(f"{r['id']}: no source_id")
        elif r.get("source_id") != computed_source_id(r):
            errors["3_identifiers"].append(f"{r['id']}: source_id {r.get('source_id')!r} but identifiers give {computed_source_id(r)!r}")
        if i["doi"] and i["doi_in_url"] and i["doi"] != i["doi_in_url"]:
            errors["3_identifiers"].append(f"{r['id']}: doi {i['doi']} differs from the DOI in its URL {i['doi_in_url']}")
        if i["pmid"] and i["pmid_in_url"] and i["pmid"] != i["pmid_in_url"]:
            errors["3_identifiers"].append(f"{r['id']}: pmid {i['pmid']} differs from the PMID in its URL {i['pmid_in_url']}")
        for k in ("doi", "doi_in_url", "pmid", "pmid_in_url", "pmcid", "url_key"):
            if i[k]:
                by_identifier[(k.replace("_in_url", ""), i[k])].add(sid)
        for k in ("doi", "doi_in_url"):
            if i[k]:
                by_source[sid]["doi"].add(i[k])
        for k in ("pmid", "pmid_in_url"):
            if i[k]:
                by_source[sid]["pmid"].add(i[k])
    for (k, v), s in sorted(by_identifier.items()):
        if len(s) > 1:
            errors["3_identifiers"].append(f"{k} {v} is registered under {len(s)} source_ids: {sorted(s)}")
    for s, d in sorted(by_source.items()):
        for k in ("doi", "pmid"):
            if len(d[k]) > 1:
                errors["3_identifiers"].append(f"source {s} carries several {k}s: {sorted(d[k])}")

    # 4
    for r in recs:
        t = r.get("same_finding_as")
        if not t:
            continue
        if t not in E:
            errors["4_same_finding_as"].append(f"{r['id']}: same_finding_as {t} does not exist")
        elif E[t].get("source_id") != r.get("source_id"):
            errors["4_same_finding_as"].append(f"{r['id']}: same_finding_as {t} is another source")
        elif E[t].get("same_finding_as"):
            errors["4_same_finding_as"].append(f"{r['id']}: same_finding_as {t}, which is itself folded")

    # 5
    for a in A:
        linked = [E[i] for i in a.get("evidence_ids", []) if i in E]
        groups = defaultdict(list)
        for r in shown_records(linked):
            groups[source_of(r)].append(r["id"])
        for s, ids in groups.items():
            if len(ids) < 2:
                continue
            rel = declared_rel.get((s, a["plant_id"], a["species_group"]))
            if not rel or sorted(rel["records"]) != sorted(ids):
                errors["5_same_original_cited_twice"].append(f"{a['plant_id']}|{a['species_group']}: {s} cited by {ids}")
            else:
                manual["same_source_records_to_confirm"].append({"plant_id": a["plant_id"], "source_id": s, "records": ids, "relation": rel["relation"],
                                                                 "verification": rel["verification"]["status"]})

    # 6
    cited = defaultdict(list)
    for a in A:
        for i in a.get("evidence_ids", []):
            cited[i].append(a["plant_id"])
    for r in recs:
        if is_listing_url(r.get("url")):
            errors["6_listing_or_search_page"].append(f"{r['id']}: {r.get('url')}" + (f" (cited by {sorted(set(cited[r['id']]))})" if cited[r["id"]] else " (not cited)"))
        elif "thetortoisetable" in str(r.get("url")) and not TT_PLANT.search(str(r.get("url"))):
            errors["6_listing_or_search_page"].append(f"{r['id']}: The Tortoise Table link without a plant entry: {r.get('url')}")

    # 7, 8
    for r in recs:
        pg = page_of(r)
        if not pg:
            continue
        txt = page_text(pg)
        declared = bool(DECLARED.search(str(r.get("plant_taxon") or "")))
        for g, s in sorted(binomials(r.get("plant_taxon"))):
            if not species_on(txt, g, s):
                item = f"{r['id']}: names {g} {s}; the entry names {pg.get('latin')!r}" + (f" and {pg['taxa_named_in_text']}" if pg.get("taxa_named_in_text") else "")
                if declared or not cited[r["id"]]:
                    manual["species_named_by_record_not_by_entry"].append({"evidence_id": r["id"], "record_taxon": r.get("plant_taxon"), "entry_latin": pg.get("latin"),
                                                                            "cited": bool(cited[r["id"]]), "declared": declared})
                else:
                    errors["8_species_claim_not_in_source"].append(item)
        for pid in sorted(set(cited[r["id"]])):
            sci = str(P.get(pid, {}).get("scientific") or "")
            genus = sci.split(" ")[0] if sci else ""
            if genus and not genus_on(txt, genus):
                if declared:
                    manual["declared_related_taxon_use"].append({"plant_id": pid, "plant_scientific": sci, "evidence_id": r["id"], "entry_latin": pg.get("latin"),
                                                                 "record_taxon": r.get("plant_taxon")})
                else:
                    errors["7_entry_does_not_name_plant_genus"].append(f"{pid} ({sci}): {r['id']} -> entry {pg.get('name')!r} / {pg.get('latin')!r}")

    # manual review: genus-level evidence only, combined entries, generic multi-plant records, identifiers, uncited records
    for a in A:
        pid = a["plant_id"]
        sci = str(P.get(pid, {}).get("scientific") or "")
        b = binomials(sci)
        if not b:
            continue
        g, s = sorted(b)[0]
        feeding = [E[i] for i in a.get("evidence_ids", []) if i in E and E[i].get("directness") != "composition_only"]
        named = []
        for r in feeding:
            pg = page_of(r)
            # What the source covers: the record's taxon field and, for a specialist entry, the entry's own names.
            # The summary is not used: it can say that a species is NOT named.
            txt = str(r.get("plant_taxon") or "") + (" " + page_text(pg) if pg else "")
            if species_on(txt, g, s):
                named.append(r["id"])
        if feeding and not named:
            manual["no_species_level_feeding_evidence"].append({"plant_id": pid, "species_group": a["species_group"], "plant_scientific": sci, "verdict": a["verdict"],
                                                                "confidence": a.get("confidence"), "feeding_evidence": [r["id"] for r in feeding],
                                                                "evidence_taxa": sorted({str(r.get("plant_taxon")) for r in feeding})})
    seen_pages = set()
    for r in recs:
        pg = page_of(r)
        if pg and cited[r["id"]]:
            gen = genera_in_latin(pg.get("latin"))
            if len(gen) > 1 and pg["url"] not in seen_pages:
                seen_pages.add(pg["url"])
                users = sorted({p for x in recs if page_of(x) is pg for p in cited[x["id"]]})
                manual["combined_entry_covers_several_taxa"].append({"url": pg["url"], "entry": pg.get("name"), "entry_latin": pg.get("latin"), "assessed_plants": users})
        if GENERIC_TAXON.search(str(r.get("plant_taxon") or "")) and cited[r["id"]]:
            manual["multi_plant_record_without_per_plant_taxon"].append({"evidence_id": r["id"], "source_title": r.get("source_title"), "plants": sorted(set(cited[r["id"]]))})
        i = identifiers(r)
        if PAPER_TYPES.search(str(r.get("source_type"))) and not (i["doi"] or i["doi_in_url"] or i["pmid"] or i["pmid_in_url"]):
            manual["paper_without_doi_or_pmid"].append({"evidence_id": r["id"], "source_title": r.get("source_title"), "url": r.get("url")})
        if not cited[r["id"]]:
            manual["uncited_records"].append(r["id"])

    checks = ["1_unresolved_evidence_id", "2_plant_not_covered_by_record", "3_identifiers", "4_same_finding_as", "5_same_original_cited_twice",
              "6_listing_or_search_page", "7_entry_does_not_name_plant_genus", "8_species_claim_not_in_source"]
    report = {"schema_version": "1.0", "generated_by": "scripts/qa_public_evidence_integrity_v1.py",
              "inputs": ["data/public_evidence_records.json", "data/public_assessments.json", "data/plants.json", "data/tortoise_table_page_taxa_v1.json",
                         "data/public_evidence_integrity_review_20261015.json"],
              "summary": {"evidence_records": len(recs), "assessments": len(A), "distinct_sources": len({r.get("source_id") for r in recs}),
                          "records_sharing_a_source": sum(1 for r in recs if sum(1 for x in recs if x.get("source_id") == r.get("source_id")) > 1),
                          "records_folded_as_same_finding": sum(1 for r in recs if r.get("same_finding_as")),
                          "errors": sum(len(errors[c]) for c in checks), "manual_review": {k: len(v) for k, v in sorted(manual.items())}},
              "checks": [{"check": c, "status": "fail" if errors[c] else "pass", "failures": errors[c]} for c in checks],
              "manual_review_note": "Not passed or failed by the script: each item needs a person to read the source. Listing an item is not a finding that the verdict is wrong.",
              "manual_review": {k: v for k, v in sorted(manual.items())}}
    return report


def main():
    report = run()
    text = json.dumps(report, ensure_ascii=False, indent=1) + "\n"
    s = report["summary"]
    for c in report["checks"]:
        print(f"{c['status'].upper():4} {c['check']}" + (f" ({len(c['failures'])})" if c["failures"] else ""))
        for f in c["failures"][:20]:
            print("     -", f)
    print(f"records {s['evidence_records']}, assessments {s['assessments']}, sources {s['distinct_sources']}, folded {s['records_folded_as_same_finding']}; manual review {s['manual_review']}")
    if "--write" in sys.argv:
        REPORT.write_text(text, encoding="utf-8", newline="\n")
        print("wrote", REPORT.relative_to(ROOT))
    elif not REPORT.exists() or REPORT.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
        sys.exit("Public evidence integrity report is out of date: run python scripts/qa_public_evidence_integrity_v1.py --write")
    if s["errors"]:
        sys.exit(f"Public evidence integrity QA FAILED: {s['errors']} error(s)")
    print("Public evidence integrity QA passed")


if __name__ == "__main__":
    main()
