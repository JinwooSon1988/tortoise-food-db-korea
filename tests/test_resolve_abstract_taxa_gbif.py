import unittest
from scripts.resolve_abstract_taxa_gbif import classify, process


class TaxonomyTests(unittest.TestCase):
    def test_exact_plant(self):
        match = {"matchType": "EXACT", "kingdom": "Plantae", "rank": "SPECIES",
                 "canonicalName": "Erodium cicutarium", "usageKey": 123}
        self.assertEqual(classify("Erodium cicutarium", match), "exact_plant_taxon_candidate")

    def test_rejects_fuzzy_animal_and_wrong_canonical(self):
        for patch in ({"matchType": "FUZZY"}, {"kingdom": "Animalia"},
                      {"canonicalName": "Erodium malacoides"}, {"rank": "GENUS"}):
            match = {"matchType": "EXACT", "kingdom": "Plantae", "rank": "SPECIES",
                     "canonicalName": "Erodium cicutarium", **patch}
            self.assertEqual(classify("Erodium cicutarium", match), "not_exact_plant_match")

    def test_failed_lookup_and_ambiguity(self):
        self.assertEqual(classify("X y", {"error": "TimeoutError"}), "lookup_failed")
        self.assertEqual(classify("Erodium cicutarium", {"matchType": "EXACT", "kingdom": "Plantae",
            "rank": "SPECIES", "canonicalName": "Erodium cicutarium", "status": "DOUBTFUL"}),
            "ambiguous_plant_match")

    def test_dedupes_requests_and_never_approves_feeding(self):
        calls = []
        def fake(name):
            calls.append(name)
            return {"matchType": "EXACT", "kingdom": "Plantae", "rank": "SPECIES",
                    "canonicalName": name, "usageKey": 10}
        rows = process([{"candidate_binomial": "Erodium cicutarium"},
                        {"candidate_binomial": "Erodium cicutarium"}], resolver=fake)
        self.assertEqual(calls, ["Erodium cicutarium"])
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(x["feeding_evidence_status"] == "unverified" and
                            x["safety_verdict"] == "not_assessed" for x in rows))


if __name__ == "__main__":
    unittest.main()
