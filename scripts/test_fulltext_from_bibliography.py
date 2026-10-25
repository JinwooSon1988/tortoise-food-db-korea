#!/usr/bin/env python3
"""Offline tests: access classification of bibliography works (the reviewer queue is tested in test_build_evidence_candidates)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "evidence_corpus"))
import fulltext_from_bibliography as f  # noqa: E402


class AccessTests(unittest.TestCase):
    known = ({"10.1/read"}, set())

    def test_access_routes(self):
        self.assertEqual(f.access_of({"doi": "https://doi.org/10.1/READ"}, self.known, {}), "already_read")
        self.assertEqual(f.access_of({"pmcid": "PMC1"}, self.known, {}), "pmc_open_access")
        self.assertEqual(f.access_of({"openalex_id": "W1"}, self.known, {"W1": {"pdf_url": "x.pdf"}}), "oa_pdf")
        self.assertEqual(f.access_of({"is_oa": True}, self.known, {}), "oa_landing_only")
        self.assertEqual(f.access_of({"abstract": "text"}, self.known, {}), "abstract_only")
        self.assertEqual(f.access_of({}, self.known, {}), "metadata_only")

    def test_tortoise_beetles_are_not_tortoise_works(self):
        self.assertTrue(f.tortoise_related({"title": "Diet of Gopherus polyphemus"}))
        self.assertFalse(f.tortoise_related({"title": "Oil palm yield in Malaysia"}))

    def test_summary_counts(self):
        rows = [{"access": "oa_pdf", "tortoise_related": True}, {"access": "abstract_only", "tortoise_related": True},
                {"access": "oa_pdf", "tortoise_related": False}]
        s = f.summary_of(rows)
        self.assertEqual((s["full_text_obtainable_tortoise"], s["abstract_or_metadata_only_tortoise"]), (1, 1))
        self.assertEqual(s["access_all"]["oa_pdf"], 2)


class SavedPathTests(unittest.TestCase):
    def test_copied_work_dir_recovers_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "txt").mkdir()
            (work / "txt" / "W1.txt").write_text("x", encoding="utf-8")
            row = {"kind": "txt", "path": "..\elsewhere\worker-output\fulltext\txt\W1.txt".replace("\\", "/")}
            self.assertEqual(f.saved_path(work, row), work / "txt" / "W1.txt")
            self.assertIsNone(f.saved_path(work, {"kind": "jats", "path": "gone/PMC1.xml"}))


if __name__ == "__main__":
    unittest.main()
