import csv
import json
import tempfile
import unittest
from pathlib import Path
from scripts.export_site_plant_binomials import export


class CatalogTaxonExportTests(unittest.TestCase):
    def test_infraspecific_names_collapse_without_inventing_species(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plants.json").write_text(json.dumps([
                {"scientific": "Brassica oleracea var. italica"},
                {"scientific": "Brassica oleracea"},
                {"scientific": "Brassica rapa subsp. chinensis"},
                {"scientific": "Taraxacum spp."},
                {"scientific": "Plantago major"}]))
            stats = export(root / "plants.json", root / "taxa.csv")
            self.assertEqual(stats["unique_valid_binomials"], 3)
            self.assertEqual(stats["normalized_infraspecific_records"], 2)
            self.assertEqual(stats["skipped_non_binomials"], 1)
            with (root / "taxa.csv").open(newline="") as stream:
                names = {x["plant_scientific_name"] for x in csv.DictReader(stream)}
            self.assertEqual(names, {"Brassica oleracea", "Brassica rapa", "Plantago major"})


if __name__ == "__main__":
    unittest.main()
