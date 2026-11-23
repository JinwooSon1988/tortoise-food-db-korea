#!/usr/bin/env python3
"""Verification queue for the live records whose cited original has not been read (units 1-5): one entry per cited
publication, with what has been tried, what is needed next, and the records waiting on it.

The queue is derived from data/research/research_gap_register_v6.json and evidence_index_v5.json, so it changes only
when the research layer changes. A record leaves the queue only when its original is read and recorded in a unit
build (a source with the full text read, and a ledger or record status that says what the original shows). Reading
the original never turns a secondary citation into a direct observation: an observation found in the original
becomes a new record from that original, with its own method, and the account's record stays a secondary citation.

Writes data/research/primary_verification_queue_v6.json. Offline.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data/research"

NEXT_STEP = {
    "not_searched": "search for the original (bibliographic databases, publisher site, library catalogues)",
    "searched_no_open_full_text_found": "obtain the full text through a library or interlibrary loan; no open copy was found",
    "searched_paywalled": "obtain the licensed full text through a library",
    "blocked_by_host": "request a copy from the host or a library; the host refused automated access",
    "located_download_failed": "retry the download of the located copy",
    "searched_unit_6_no_copy_found": "request the original through a library; the unit-6 web search found no copy",
    "secondary_citation_primary_not_read": "search for the original",
    "not_in_the_cited_source_read_other_cited_sources_unread": "read the other cited sources; the one that was read does not name the plant",
}
ALLOWED_STATUS = ["awaiting_original"]


def load(name):
    return json.loads((RES / name).read_text(encoding="utf-8"))


def main():
    reg = load("research_gap_register_v6.json")
    idx = {x["evidence_id"]: x for x in load("evidence_index_v5.json")["records"]}

    def independent(i):
        x = idx[i]
        return sorted(p["evidence_id"] for p in idx.values() if x["plant_accepted_name"] and p["plant_accepted_name"] == x["plant_accepted_name"]
                      and p["tortoise_key"] == x["tortoise_key"] and p["source_id"] != x["source_id"] and p["evidence_directness"] == "primary_study_read"
                      and not p["on_hold"] and not p["is_negative_record"] and not p.get("superseded_by"))

    entries = []
    for section, group in [("unit_1_citations_not_read", c) for c in reg["unit_1_citations_not_read"]] + [("other_citations_not_read", c) for c in reg["other_citations_not_read"]]:
        search = group["original_status"] if section == "unit_1_citations_not_read" else group["status"][0]
        records = [{"evidence_id": i, "unit": idx[i]["unit"], "source_id": idx[i]["source_id"], "tortoise": idx[i]["tortoise"], "plant_as_printed": idx[i]["plant_name_as_printed"],
                    "plant_accepted_name": idx[i]["plant_accepted_name"], "evidence_tier_now": idx[i]["evidence_tier"], "evidence_directness_now": idx[i]["evidence_directness"],
                    "independent_primary_records_same_tortoise_and_plant": independent(i)} for i in group["evidence_ids"]]
        entries.append({
            "cited_as": group["cited_as"], "register_section": section, "records": len(records),
            "cited_by_sources": sorted({r["source_id"] for r in records}), "tortoise_species": group["tortoise_species"],
            "bibliographic_note": group.get("original_note") or "; ".join(group.get("notes") or []) or None,
            "search_status": search, "unit_6_search": group.get("unit_6_search"), "audit_document": group.get("audit_document"),
            "next_step": NEXT_STEP[search], "verification_status": "awaiting_original",
            "evidence_level_now": "secondary citation only; not a confirmed observation",
            "records_without_an_independent_primary_record": sum(1 for r in records if not r["independent_primary_records_same_tortoise_and_plant"]),
            "evidence_records": records})
    # citations whose every record lacks an independent primary record first, then by size
    entries.sort(key=lambda e: (-e["records_without_an_independent_primary_record"], -e["records"], e["cited_as"]))
    for n, e in enumerate(entries, 1):
        e["queue_position"] = n

    doc = {"schema_version": "6.0", "generated_by": "scripts/build_primary_verification_queue_v6.py",
           "derived_from": ["data/research/research_gap_register_v6.json", "data/research/evidence_index_v5.json"],
           "rules": ["A verification status changes only after the original itself is obtained and read; a search, an abstract or another secondary account does not change it.",
                     "Reading the original never raises the account's record: it stays a secondary citation. What the original shows is recorded as a new record from the original, with its own method and tier.",
                     "If the original is read and does not contain the statement, the account's record is put on hold (as for crm109_agassizii_2019-05/06), not deleted.",
                     "Personal observations and unpublished reports that cannot be obtained stay in the queue with that reason; they are never confirmed.",
                     "Nothing here is a feeding grade or a safety statement."],
           "allowed_verification_status": ALLOWED_STATUS,
           "not_in_queue": {"cited_source_read_does_not_support_the_statement": [r["evidence_id"] for r in reg["unit_1_citations_read_not_supporting"]],
                            "note": "the cited source was read and does not support the statement; these records are on hold (review_queue_v4 records_on_hold)"},
           "queue": entries,
           "totals": {"citations": len(entries), "records": sum(e["records"] for e in entries),
                      "records_without_an_independent_primary_record": sum(e["records_without_an_independent_primary_record"] for e in entries),
                      "by_search_status": {s: sum(1 for e in entries if e["search_status"] == s) for s in sorted({e["search_status"] for e in entries})}}}
    (RES / "primary_verification_queue_v6.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
