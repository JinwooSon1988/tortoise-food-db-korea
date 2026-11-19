import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_research_taxonomy_provenance import audit


class ProvenanceAuditTests(unittest.TestCase):
    def test_retains_distinct_sources_without_claiming_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "accepted.csv"
            with source.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["plant_scientific_name", "taxonomic_status", "source_reference"])
                writer.writerows([
                    ["Plantago major", "accepted", "taxonomic-reference-A"],
                    ["Plantago major", "accepted", "taxonomic-reference-B"],
                    ["Plantago major", "accepted", "taxonomic-reference-A"],
                    ["Taraxacum officinale", "accepted", "taxonomic-reference-C"]])
            output = root / "audit.csv"
            report = root / "report.json"
            counts = audit(source, output, report)
            self.assertEqual(counts["unique_names"], 2)
            self.assertEqual(counts["unique_name_source_pairs"], 3)
            with output.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 3)
            self.assertEqual({r["verification_status"] for r in rows},
                             {"source_claim_unverified"})
            self.assertEqual({r["feeding_verdict"] for r in rows}, {""})
            self.assertIsNone(json.loads(report.read_text())["feeding_verdict"])
            with self.assertRaises(ValueError):
                audit(source, output, report)

    def test_rejects_unaccepted_taxa(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "accepted.csv"
            source.write_text("plant_scientific_name,taxonomic_status,source_reference\\n"
                              "Plantago major,synonym,reference\\n".replace("\\n", "\n"))
            with self.assertRaises(ValueError):
                audit(source, root / "audit.csv", root / "report.json")
            self.assertFalse((root / "audit.csv").exists())


if __name__ == "__main__":
    unittest.main()
