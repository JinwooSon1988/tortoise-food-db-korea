import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.build_research_taxonomy_index import build


class ResearchTaxonomyIndexTests(unittest.TestCase):
    def test_bulk_dedup_and_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog = root / "catalog.csv"
            accepted = root / "accepted.csv"
            output = root / "out.csv"
            report = root / "report.json"
            catalog.write_text("plant_scientific_name\nPlantago major\n", encoding="utf-8")
            with accepted.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["plant_scientific_name", "taxonomic_status", "source_reference"])
                writer.writerow(["Plantago major", "accepted", "source-1"])
                for n in range(22765):
                    genus = ("A" if n < 17576 else "B") + "".join(
                        chr(97 + digit) for digit in ((n % 17576) // 676,
                                                      ((n % 17576) // 26) % 26,
                                                      n % 26))
                    writer.writerow([genus + " officinale", "accepted", "source-1"])
            counts = build(catalog, accepted, output, report)
            self.assertEqual(counts["unique_binomials"], 22766)
            self.assertEqual(counts["duplicates"], 1)
            self.assertEqual(len(output.read_text().splitlines()), 22767)
            self.assertIsNone(json.loads(report.read_text())["feeding_verdict"])

    def test_rejects_unaccepted_or_untraceable_taxa(self):
        for status, source in (("synonym", "source-1"), ("accepted", "")):
            with self.subTest(status=status, source=source):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    (root / "catalog.csv").write_text("plant_scientific_name\nPlantago major\n")
                    (root / "accepted.csv").write_text(
                        "plant_scientific_name,taxonomic_status,source_reference\n"
                        f"Taraxacum officinale,{status},{source}\n")
                    with self.assertRaises(ValueError):
                        build(root / "catalog.csv", root / "accepted.csv",
                              root / "out.csv", root / "report.json")
                    self.assertFalse((root / "out.csv").exists())


if __name__ == "__main__":
    unittest.main()
