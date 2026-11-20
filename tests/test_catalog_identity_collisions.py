import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_catalog_identity_collisions import audit


class CatalogIdentityAuditTests(unittest.TestCase):
    def test_preserves_distinct_parts_and_flags_identical_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog = root / "plants.json"
            catalog.write_text(json.dumps([
                {"id": "leaf", "scientific": "Hibiscus syriacus", "ko": "무궁화잎", "en": "Leaf"},
                {"id": "flower", "scientific": "Hibiscus syriacus", "ko": "무궁화꽃", "en": "Flower"},
                {"id": "dup1", "scientific": "Oenanthe javanica", "ko": "미나리", "en": "Minari"},
                {"id": "dup2", "scientific": "Oenanthe javanica", "ko": "미나리", "en": "Minari"}
            ]))
            result = audit(catalog, root / "report.json")
            self.assertEqual(result["catalog_records"], 4)
            self.assertEqual(result["shared_scientific_name_groups"], 2)
            self.assertEqual(result["potential_identical_display_label_groups"], 1)
            self.assertTrue(all(c["review_status"] == "human_review_required"
                                for c in result["collisions"]))
            with self.assertRaises(ValueError):
                audit(catalog, root / "report.json")

    def test_duplicate_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog = root / "plants.json"
            catalog.write_text(json.dumps([
                {"id": "same", "scientific": "Plantago major"},
                {"id": "same", "scientific": "Taraxacum officinale"}]))
            with self.assertRaises(ValueError):
                audit(catalog, root / "report.json")
            self.assertFalse((root / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
