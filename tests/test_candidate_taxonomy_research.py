import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.export_candidate_taxonomy_for_research import export


class CandidateTaxonomyResearchTests(unittest.TestCase):
    def test_real_repository_shards_and_site_names_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "site.csv"
            site.write_text("plant_scientific_name\nPlantago major\n", encoding="utf-8")
            result = export(Path("data/taxonomy-shards/index.json"), site,
                            root / "taxa.csv", root / "report.json")
            self.assertEqual(result["taxonomy_candidate_records"], 9995)
            self.assertGreater(result["unique_matching_binomials"], 1000)
            self.assertIsNone(result["feeding_verdict"])
            with (root / "taxa.csv").open(encoding="utf-8") as stream:
                names = {row["plant_scientific_name"] for row in csv.DictReader(stream)}
            self.assertIn("Plantago major", names)
            self.assertIn("Abies alba", names)

    def test_corrupt_shard_rejected_without_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "taxa-01.json").write_text(json.dumps({"records": [{
                "scientific_name": "Abies alba", "source_scope": "taxonomy_only",
                "identity_status": "taxonomy_candidate",
                "feeding_safety_status": "not_assessed", "safety_grade": None,
                "source_taxon_url": "https://www.gbif.org/species/123"}]}))
            (root / "index.json").write_text(json.dumps({
                "count": 1, "shards": [{"file": "taxa-01.json", "count": 1,
                                        "sha256": "0" * 64}]}))
            (root / "site.csv").write_text("plant_scientific_name\nPlantago major\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                export(root / "index.json", root / "site.csv",
                       root / "out.csv", root / "report.json")
            self.assertFalse((root / "out.csv").exists())

    def test_taxonomy_candidates_cannot_claim_feeding_safety(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shard = {"records": [{
                "scientific_name": "Abies alba", "source_scope": "taxonomy_only",
                "identity_status": "taxonomy_candidate",
                "feeding_safety_status": "safe", "safety_grade": "A",
                "source_taxon_url": "https://www.gbif.org/species/123"}]}
            raw = json.dumps(shard).encode()
            (root / "taxa-01.json").write_bytes(raw)
            (root / "index.json").write_text(json.dumps({
                "count": 1, "shards": [{"file": "taxa-01.json", "count": 1,
                                        "sha256": hashlib.sha256(raw).hexdigest()}]}))
            (root / "site.csv").write_text("plant_scientific_name\nPlantago major\n")
            with self.assertRaisesRegex(ValueError, "unsafe/unverified"):
                export(root / "index.json", root / "site.csv",
                       root / "out.csv", root / "report.json")
            self.assertFalse((root / "out.csv").exists())


if __name__ == "__main__":
    unittest.main()
