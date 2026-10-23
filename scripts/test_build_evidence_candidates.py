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


if __name__ == "__main__":
    unittest.main(verbosity=1)
