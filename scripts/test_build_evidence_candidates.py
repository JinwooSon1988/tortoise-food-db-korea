#!/usr/bin/env python3
"""Offline test for build_evidence_candidates.py on a synthetic saved text: evidence classes, readiness rules and
the guarantee that nothing is marked verified or promoted."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = """Diet of Testudo graeca in the study area.

Testudo graeca tortoises ate the flowers of Abelmoschus esculentus in spring.

Abelmoschus manihot grows along the roads of the study area.

Testudo graeca tortoises never eaten Abutilon auritum in the enclosure trial.

The leaves of Abutilon fruticosum contain oxalate and were analysed for crude protein.
"""


class CandidateTests(unittest.TestCase):
    def test_classes_and_readiness(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "doc.txt").write_text(TEXT, encoding="utf-8")
        (tmp / "docs.jsonl").write_text(json.dumps({"doc_id": "synthetic", "path": str(tmp / "doc.txt"), "kind": "txt",
                                                    "citation": "Synthetic test document", "url": "https://example.org/synthetic",
                                                    "source_class": "peer_reviewed", "tortoise_hint": "Testudo graeca"}) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/build_evidence_candidates.py"), "--bibliography", str(tmp / "none.json"),
                            "--docs", str(tmp / "docs.jsonl"), "--output", str(tmp / "c.json"), "--drafts", str(tmp / "d.json")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        c = {x["reported_name"]: x for x in json.loads((tmp / "c.json").read_text(encoding="utf-8"))["candidates"]}
        self.assertEqual(c["Abelmoschus esculentus"]["evidence_class"], "ingestion_observation")
        self.assertEqual(c["Abelmoschus esculentus"]["state"], "ready_for_reviewer")
        self.assertEqual(c["Abelmoschus manihot"]["evidence_class"], "name_mention")
        self.assertEqual(c["Abutilon auritum"]["evidence_class"], "not_eaten_or_avoided")
        self.assertEqual(c["Abutilon fruticosum"]["evidence_class"], "toxicity_or_nutrition")
        for name in ("Abelmoschus manihot", "Abutilon auritum", "Abutilon fruticosum"):
            self.assertEqual(c[name]["state"], "needs_human_review")
        self.assertTrue(all(x["verified_feeding_evidence"] is False for x in c.values()))
        drafts = json.loads((tmp / "d.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual([d["reported_name"] for d in drafts], ["Abelmoschus esculentus"])
        self.assertTrue(all(d["reviewed"] is False and d["original_inspected"] is False for d in drafts))


def run(tmp, docs, bibliography=None, reviews=None):
    if bibliography is not None:
        (tmp / "bib.json").write_text(json.dumps({"works": bibliography}), encoding="utf-8")
    (tmp / "docs.jsonl").write_text("".join(json.dumps(d) + "\n" for d in docs), encoding="utf-8")
    rdir = tmp / "reviews"
    if reviews:
        (rdir / "reviewed-test").mkdir(parents=True, exist_ok=True)
        (rdir / "reviewed-test" / "review-decisions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in reviews), encoding="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "scripts/build_evidence_candidates.py"), "--bibliography", str(tmp / "bib.json"),
                        "--docs", str(tmp / "docs.jsonl"), "--output", str(tmp / "c.json"), "--drafts", str(tmp / "d.json"),
                        "--reviews-dir", str(rdir)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = json.loads((tmp / "c.json").read_text(encoding="utf-8"))
    return out, json.loads((tmp / "d.json").read_text(encoding="utf-8"))["records"]


class DeduplicationTests(unittest.TestCase):
    DOC = {"doc_id": "dup", "kind": "txt", "citation": "Duplicate test document", "doi": "10.0000/dup-test",
           "url": "https://example.org/dup.pdf", "source_class": "peer_reviewed", "tortoise_hint": "Testudo graeca"}

    def test_most_complete_duplicate_is_kept(self):
        tmp = Path(tempfile.mkdtemp())
        # page 1 names the plant without a part; page 2 states the part: one candidate, the page-2 one, is kept
        (tmp / "dup.txt").write_text("Testudo graeca tortoises ate Abelmoschus esculentus often.\n\f"
                                     "Testudo graeca tortoises ate the flowers of Abelmoschus esculentus in spring.\n", encoding="utf-8")
        out, drafts = run(tmp, [dict(self.DOC, path=str(tmp / "dup.txt"))])
        c = [x for x in out["candidates"] if x["reported_name"] == "Abelmoschus esculentus"]
        self.assertEqual(len(c), 1)
        self.assertEqual((c[0]["plant_part"], c[0]["locator"], c[0]["alternate_locators"]), ("flower", "PDF p.2", ["PDF p.1"]))
        self.assertEqual(c[0]["state"], "ready_for_reviewer")
        self.assertEqual(out["counts"]["duplicate_candidates"], 1)

    def test_full_text_preferred_over_title_or_abstract(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "dup.txt").write_text("Testudo graeca tortoises ate the flowers of Abelmoschus esculentus in spring.\n", encoding="utf-8")
        bib = [{"id": "W1", "doi": "https://doi.org/10.0000/dup-test", "title": "Diet of Testudo graeca",
                "abstract": "Testudo graeca tortoises ate the flowers of Abelmoschus esculentus in spring."}]
        out, _ = run(tmp, [dict(self.DOC, path=str(tmp / "dup.txt"))], bibliography=bib)
        c = [x for x in out["candidates"] if x["reported_name"] == "Abelmoschus esculentus"]
        self.assertEqual([(x["source"], x["full_text"]) for x in c], [("full_text", True)])
        self.assertEqual(out["counts"]["duplicate_full_text_preferred"], 1)

    def test_prior_review_is_kept_and_not_requeued(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "dup.txt").write_text("Testudo graeca tortoises ate the flowers of Abelmoschus esculentus in spring.\n", encoding="utf-8")
        reviews = [{"doc_id": "dup", "reported_name": "Abelmoschus esculentus", "evidence_class": "ingestion_observation",
                    "decision": "reject", "reason": "test rejection", "reviewed": "2026-10-24", "reviewer": "test"}]
        out, drafts = run(tmp, [dict(self.DOC, path=str(tmp / "dup.txt"))], reviews=reviews)
        c = [x for x in out["candidates"] if x["reported_name"] == "Abelmoschus esculentus"][0]
        self.assertEqual((c["state"], c["prior_review"]["decision"], c["prior_review"]["reason"]), ("previously_reviewed", "reject", "test rejection"))
        self.assertEqual(drafts, [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
