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

    def test_diverse_candidate_batch_preserves_research_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "taxa-01.json"
            raw = json.dumps({"records": [{
                "scientific_name": "Abies alba", "source_scope": "taxonomy_only",
                "identity_status": "taxonomy_candidate",
                "feeding_safety_status": "not_assessed", "safety_grade": None,
                "source_taxon_url": "https://www.gbif.org/species/123"}]}).encode()
            source.write_bytes(raw)
            (root / "index.json").write_text(json.dumps({
                "count": 1, "shards": [{"file": source.name, "count": 1,
                "sha256": hashlib.sha256(raw).hexdigest()}]}))
            (root / "site.csv").write_text("plant_scientific_name\nPlantago major\n")
            (root / "diverse.json").write_text(json.dumps({"record_count": 2, "records": [
                {"scientific_name": "Taraxacum officinale", "safety_grade": None, "source_scope": "taxonomy_only",
                 "identity_status": "taxonomy_candidate",
                 "source_taxon_url": "https://www.gbif.org/species/123",
                 "feeding_safety_status": "not_assessed"},
                {"scientific_name": "Abies alba", "safety_grade": None, "source_scope": "taxonomy_only",
                 "identity_status": "taxonomy_candidate",
                 "source_taxon_url": "https://www.gbif.org/species/123",
                 "feeding_safety_status": "not_assessed"}]}))
            result = export(root / "index.json", root / "site.csv",
                            root / "out.csv", root / "report.json", root / "diverse.json")
            self.assertEqual(result["diverse_taxonomy_candidate_records"], 2)
            self.assertEqual(result["unique_matching_binomials"], 3)
            self.assertIsNone(result["feeding_verdict"])

    def test_diverse_unsafe_record_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "taxa-01.json"
            raw = json.dumps({"records": [{
                "scientific_name": "Abies alba", "source_scope": "taxonomy_only",
                "identity_status": "taxonomy_candidate",
                "feeding_safety_status": "not_assessed", "safety_grade": None,
                "source_taxon_url": "https://www.gbif.org/species/123"}]}).encode()
            source.write_bytes(raw)
            (root / "index.json").write_text(json.dumps({
                "count": 1, "shards": [{"file": source.name, "count": 1,
                "sha256": hashlib.sha256(raw).hexdigest()}]}))
            (root / "site.csv").write_text("plant_scientific_name\nPlantago major\n")
            (root / "diverse.json").write_text(json.dumps({"record_count": 1, "records": [
                {"scientific_name": "Taraxacum officinale", "safety_grade": "A",
                 "feeding_safety_status": "safe"}]}))
            with self.assertRaisesRegex(ValueError, "unsafe diverse"):
                export(root / "index.json", root / "site.csv",
                       root / "out.csv", root / "report.json", root / "diverse.json")
            self.assertFalse((root / "out.csv").exists())

    def test_rejects_malformed_gbif_urls_in_both_sources(self):
        bad_urls = (
            "https://www.gbif.org/species/",
            "https://www.gbif.org/species/not-a-number",
            "https://www.gbif.org/species/123/extra",
            "https://www.gbif.org/species/123?redirect=1",
            "https://www.gbif.org/species/123.evil.example",
        )
        for bad_url in bad_urls:
            for in_diverse in (False, True):
                with self.subTest(url=bad_url, diverse=in_diverse):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        record = {
                            "scientific_name": "Abies alba",
                            "source_scope": "taxonomy_only",
                            "identity_status": "taxonomy_candidate",
                            "feeding_safety_status": "not_assessed",
                            "safety_grade": None,
                            "source_taxon_url": "https://www.gbif.org/species/123",
                        }
                        shard_record = dict(record)
                        diverse_record = dict(record)
                        if in_diverse:
                            diverse_record["source_taxon_url"] = bad_url
                        else:
                            shard_record["source_taxon_url"] = bad_url
                        raw = json.dumps({"records": [shard_record]}).encode()
                        (root / "taxa-01.json").write_bytes(raw)
                        (root / "index.json").write_text(json.dumps({
                            "count": 1,
                            "shards": [{"file": "taxa-01.json", "count": 1,
                                        "sha256": hashlib.sha256(raw).hexdigest()}],
                        }))
                        (root / "site.csv").write_text("plant_scientific_name\nPlantago major\n")
                        if in_diverse:
                            (root / "diverse.json").write_text(json.dumps({
                                "record_count": 1, "records": [diverse_record],
                            }))
                        with self.assertRaisesRegex(ValueError, "unsafe"):
                            export(root / "index.json", root / "site.csv",
                                   root / "out.csv", root / "report.json",
                                   root / "diverse.json" if in_diverse else None)
                        self.assertFalse((root / "out.csv").exists())
                        self.assertFalse((root / "report.json").exists())

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
