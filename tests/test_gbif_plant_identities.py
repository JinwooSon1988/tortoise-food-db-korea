import json
import tempfile
import unittest
from pathlib import Path
from scripts.collect_gbif_plant_identities import collect


class GbifCollectorTests(unittest.TestCase):
    def test_pages_filter_nonplants_and_reject_unsafe_status(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "gbif.jsonl"
            def fetch(offset, limit):
                return {"results": [
                    {"key": offset + 1, "canonicalName": "Plantus alba", "kingdom": "Plantae",
                     "rank": "SPECIES", "taxonomicStatus": "ACCEPTED", "family": "Plantaceae"},
                    {"key": offset + 2, "canonicalName": "Animalus alba", "kingdom": "Animalia",
                     "rank": "SPECIES", "taxonomicStatus": "ACCEPTED"},
                    {"key": offset + 3, "canonicalName": "Plantus synonym", "kingdom": "Plantae",
                     "rank": "SPECIES", "taxonomicStatus": "SYNONYM"}]}
            result = collect(out, pages=3, page_size=10, fetcher=fetch)
            self.assertEqual(result["candidates"], 3)
            records = [json.loads(x) for x in out.read_text().splitlines()]
            self.assertEqual(len(records), 3)
            self.assertTrue(all(x["source_id"] == "GBIF" for x in records))
            self.assertTrue(all("verdict" not in x for x in records))

    def test_disjoint_offsets_and_invalid_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "offset.jsonl"
            requested = []
            def fetch(offset, limit):
                requested.append((offset, limit))
                return {"results": [{"key": offset + 1, "canonicalName": f"Plantus {offset}",
                                    "kingdom": "Plantae", "rank": "SPECIES",
                                    "taxonomicStatus": "ACCEPTED"}]}
            result = collect(out, pages=3, page_size=100, fetcher=fetch, start_offset=500)
            self.assertEqual(result["candidates"], 3)
            self.assertEqual(requested, [(500, 100), (600, 100), (700, 100)])
            with self.assertRaises(ValueError):
                collect(Path(directory) / "invalid.jsonl", pages=1, page_size=100,
                        fetcher=fetch, start_offset=550)

    def test_empty_and_failure_never_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "gbif.jsonl"
            with self.assertRaises(ValueError):
                collect(out, pages=1, fetcher=lambda offset, limit: {"results": []})
            self.assertFalse(out.exists())
            with self.assertRaises(ValueError):
                collect(out, pages=1, fetcher=lambda offset, limit: {"wrong": []})
            self.assertFalse(out.exists())

    def test_existing_file_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "gbif.jsonl"
            out.write_text("existing", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                collect(out, fetcher=lambda offset, limit: {"results": []})
            self.assertEqual(out.read_text(), "existing")


if __name__ == "__main__":
    unittest.main()
