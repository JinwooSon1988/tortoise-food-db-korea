import json
import tempfile
import unittest
from pathlib import Path
from scripts.merge_gbif_identity_batches import merge


def row(key, name="Plantus testus"):
    return {"candidate_id": f"gbif:{key}", "canonical_scientific_name": name,
            "source_id": "GBIF", "source_record_id": str(key),
            "source_url": f"https://www.gbif.org/species/{key}",
            "taxonomic_status": "accepted", "family": "Testaceae",
            "reconciliation_status": "pending", "feed_review_status": "identity_only",
            "observed_at": "2026-11-16"}


class MergeTests(unittest.TestCase):
    def test_cross_batch_dedup_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            a, b = base / "a.jsonl", base / "b.jsonl"
            a.write_text("\n".join(json.dumps(row(i)) for i in (1, 2)) + "\n")
            b.write_text("\n".join(json.dumps(row(i)) for i in (2, 3)) + "\n")
            result = merge([a, b], base / "merged.jsonl", base / "report.json")
            self.assertEqual(result["read"], 4)
            self.assertEqual(result["unique"], 3)
            self.assertEqual(result["duplicate"], 1)
            self.assertEqual(result["conflicts"], 0)
            self.assertEqual(result["canonical_name_collision_groups"], 1)
            self.assertEqual(result["canonical_name_collision_records"], 3)
            self.assertEqual(len((base / "merged.jsonl").read_text().splitlines()), 3)

    def test_distinct_names_no_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            a = base / "a.jsonl"
            a.write_text(json.dumps(row(1, "Plantus alpha")) + "\n" +
                         json.dumps(row(2, "Plantus beta")) + "\n")
            result = merge([a], base / "merged.jsonl", base / "report.json")
            self.assertEqual(result["distinct_canonical_names"], 2)
            self.assertEqual(result["canonical_name_collision_groups"], 0)

    def test_conflict_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            a, b = base / "a.jsonl", base / "b.jsonl"
            a.write_text(json.dumps(row(1)) + "\n")
            b.write_text(json.dumps(row(1, "Different name")) + "\n")
            with self.assertRaises(ValueError):
                merge([a, b], base / "merged.jsonl", base / "report.json")
            self.assertFalse((base / "merged.jsonl").exists())
            self.assertFalse((base / "report.json").exists())

    def test_feeding_claim_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            a = base / "a.jsonl"
            candidate = row(1)
            candidate["safe"] = True
            a.write_text(json.dumps(candidate) + "\n")
            with self.assertRaises(ValueError):
                merge([a], base / "merged.jsonl", base / "report.json")
            self.assertFalse((base / "merged.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
