#!/usr/bin/env python3
"""Bulk screening queue for Europe PMC abstracts. Signals are not feeding evidence."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

SIGNALS = {
    "plant_context": re.compile(r"\b(?:plant|plants|vegetation|forage|foraging|herbivor\w*|grass\w*|leaf|leaves|flower\w*|fruit\w*)\b", re.I),
    "diet_context": re.compile(r"\b(?:diet|dietary|feeding|feed|food|ingest\w*|consum\w*|graz\w*|browse|browsing)\b", re.I),
    "field_observation": re.compile(r"\b(?:field stud\w*|wild|observ\w*|fecal|faecal|stomach content\w*|diet composition)\b", re.I),
}
LATIN_BINOMIAL = re.compile(r"(?<![A-Za-z])([A-Z][a-z]{2,})\s+([a-z]{3,})(?![A-Za-z])")
EXCLUDE_GENERA = {"The", "This", "These", "Those", "There", "However", "Although", "Among",
                  "Results", "Methods", "Background", "Conclusions", "Testudo", "Geochelone",
                  "Centrochelys", "Chelonoidis", "Gopherus", "Aldabrachelys", "Stigmochelys",
                  "Agrionemys", "Astrochelys", "Manouria", "Kinixys", "Pyxis", "Indotestudo",
                  "Homopus", "Chersobius", "Psammobates", "Malacochersus"}


def contextual_excerpts(abstract, limit=5):
    """Return short review excerpts with both plant and diet terms, without asserting feeding."""
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"<[^>]+>", " ", abstract))
    return [sentence.strip()[:600] for sentence in sentences
            if SIGNALS["plant_context"].search(sentence) and SIGNALS["diet_context"].search(sentence)][:limit]


def screen(input_path, output_path, report_path):
    if len({p.resolve() for p in (input_path, output_path, report_path)}) != 3:
        raise ValueError("paths must be distinct")
    if output_path.exists() or report_path.exists():
        raise FileExistsError("will not overwrite existing outputs")
    rows = []
    totals = Counter()
    with input_path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            if not isinstance(item, dict) or item.get("review_status") != "unmatched_literature_lead":
                raise ValueError(f"invalid unmatched lead at line {line_number}")
            abstract = item.get("abstract_text")
            if abstract is not None and not isinstance(abstract, str):
                raise ValueError(f"invalid abstract at line {line_number}")
            abstract = abstract or ""
            flags = {name: bool(pattern.search(abstract)) for name, pattern in SIGNALS.items()}
            candidates = sorted({f"{genus} {species}" for genus, species in LATIN_BINOMIAL.findall(abstract)
                                 if genus not in EXCLUDE_GENERA})
            excerpts = contextual_excerpts(abstract)
            # Latin-shaped phrases are only screening hints, NOT verified plant identities.
            priority = "abstract_review" if flags["plant_context"] and flags["diet_context"] else "manual_screen"
            rows.append({"source_record_id": item["source_record_id"],
                         "source_database": item["source_database"],
                         "source_url": item["source_url"], "doi": item.get("doi"),
                         "review_priority": priority, "signals": flags,
                         "unverified_binomial_strings": candidates,
                         "plant_diet_context_excerpts": excerpts,
                         "review_status": "manual_validation_required",
                         "feeding_verdict": None})
            totals["publications"] += 1
            totals[priority] += 1
            totals["with_abstract"] += bool(abstract)
    if not rows:
        raise ValueError("empty literature screening input")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # Both files are review-only, not read by the public site.
    output_path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows),
                           encoding="utf-8")
    report_path.write_text(json.dumps({"counts": dict(totals),
                                       "status": "screening_hints_only_no_verified_plant_evidence"},
                                      indent=2) + "\n", encoding="utf-8")
    return dict(totals)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(screen(args.input, args.output, args.report), sort_keys=True))
