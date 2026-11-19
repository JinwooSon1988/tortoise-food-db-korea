import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.link_plant_abstract_mentions import link


class BulkPlantAbstractTests(unittest.TestCase):
    def test_bulk_exact_mentions_not_verdicts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with (root / "taxa.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["plant_scientific_name"])
                writer.writeheader()
                writer.writerows([{"plant_scientific_name": "Taraxacum officinale"},
                                  {"plant_scientific_name": "Plantago major"}])
            (root / "papers.jsonl").write_text(json.dumps({
                "source_database": "MED", "source_record_id": "1",
                "title": "Plant study", "source_url": "https://europepmc.org/article/MED/1",
                "review_status": "unmatched_literature_lead", "feeding_verdict": None,
                "abstract_text": "Taraxacum officinale was sampled. Plantago major was also recorded."
            }) + "\n")
            result = link(root / "papers.jsonl", root / "taxa.csv", root / "links.jsonl", root / "report.json")
            self.assertEqual(result["unverified_plant_publication_links"], 2)
            rows = [json.loads(x) for x in (root / "links.jsonl").read_text().splitlines()]
            self.assertTrue(all(x["feeding_verdict"] is None for x in rows))
            self.assertTrue(all(x["tortoise_scientific_name"] is None for x in rows))
            self.assertTrue(all(x["review_status"] == "unverified_abstract_mention" for x in rows))

    def test_large_taxonomy_single_pass_exact_membership(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Large accepted-name input must not expand the regular expression.
            with (root / "taxa.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["plant_scientific_name"])
                writer.writeheader()
                writer.writerow({"plant_scientific_name": "Plantago major"})
                writer.writerow({"plant_scientific_name": "Taraxacum officinale"})
                for first in "abcdefghijklmnopqrstuvwxyz":
                    for second in "abcdefghijklmnopqrstuvwxyz":
                        for third in "abcdefghijklmnopqrstuvwxyz":
                            writer.writerow({"plant_scientific_name": f"Genus {first}{second}{third}"})
            (root / "papers.jsonl").write_text(json.dumps({
                "source_database": "MED", "source_record_id": "bulk",
                "review_status": "unmatched_literature_lead", "feeding_verdict": None,
                "abstract_text": "Plantago majoris; Plantago major; Taraxacum officinale. Genus abcde."
            }) + "\\n")
            counts = link(root / "papers.jsonl", root / "taxa.csv",
                          root / "links.jsonl", root / "report.json")
            self.assertEqual(counts["unverified_plant_publication_links"], 2)
            rows = [json.loads(x) for x in (root / "links.jsonl").read_text().splitlines()]
            self.assertEqual({x["plant_scientific_name"] for x in rows},
                             {"Plantago major", "Taraxacum officinale"})
            self.assertTrue(all(x["feeding_verdict"] is None for x in rows))

    def test_no_partial_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "taxa.csv").write_text("plant_scientific_name\nPlantago major\n")
            (root / "papers.jsonl").write_text(json.dumps({
                "source_database": "MED", "source_record_id": "2",
                "review_status": "unmatched_literature_lead", "feeding_verdict": None,
                "abstract_text": "Plantago majoris is not Plantago majoris."
            }) + "\n")
            result = link(root / "papers.jsonl", root / "taxa.csv", root / "links.jsonl", root / "report.json")
            self.assertEqual(result.get("unverified_plant_publication_links", 0), 0)


if __name__ == "__main__":
    unittest.main()
