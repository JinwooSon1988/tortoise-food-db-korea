"""Safety and rendering regression checks for taxonomy-only directory."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_taxonomy_directory import build


def record(**overrides):
    base = {
        "scientific": "Bellis perennis",
        "family": "Asteraceae",
        "rank": "species",
        "taxon_id": "123",
        "taxonomy_source_url": "https://www.gbif.org/species/123",
        "feeding_status": "unverified",
        "feeding_grade": None,
        "publication_status": "staged_not_public",
    }
    base.update(overrides)
    return base


class DirectoryTests(unittest.TestCase):
    def test_bilingual_hold_and_search(self):
        page = build([record()])
        for text in ("급여 안전성 미확정", "Feeding safety not established", "Bellis perennis", "taxa.filter", "aria-live"):
            self.assertIn(text, page)

    def test_rejects_any_grading(self):
        with self.assertRaises(ValueError):
            build([record(feeding_grade="A")])
        with self.assertRaises(ValueError):
            build([record(feeding_status="reviewed")])

    def test_rejects_duplicates(self):
        with self.assertRaises(ValueError):
            build([record(), record(scientific="bellis perennis", taxon_id="456")])

    def test_escapes_html_in_embedded_json(self):
        page = build([record(family="Asteraceae</script><script>alert(1)</script>")])
        self.assertNotIn("Asteraceae</script><script>", page)
        self.assertIn("\\u003c", page)

    def test_missing_identity_rejected(self):
        with self.assertRaises(ValueError):
            build([record(taxon_id="")])


if __name__ == "__main__":
    unittest.main()
