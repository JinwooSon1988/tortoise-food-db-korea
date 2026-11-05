import unittest
from scripts.extract_jats_botanical_mentions import candidates_from_xml

class JatsBotanicalMentionsTests(unittest.TestCase):
    def test_extracts_context_without_feeding_claim(self):
        xml=b'<article><body><sec><p id="p1">The plant Mirabilis laevis was measured in the transect.</p></sec></body></article>'
        result=candidates_from_xml(xml,"https://doi.org/example","PMC123")
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["candidate_plant_name"],"Mirabilis laevis")
        self.assertEqual(result[0]["source_element_id"],"p1")
        self.assertIn("Mirabilis laevis",result[0]["exact_context_excerpt"])
        self.assertEqual(result[0]["name_end_offset"]-result[0]["name_start_offset"],len("Mirabilis laevis"))
        self.assertEqual(result[0]["feeding_observation_status"],"not_verified")
        self.assertEqual(result[0]["feeding_safety_status"],"unassessed")
        self.assertEqual(result[0]["verified_plant_links"],[])
    def test_sentence_starters_not_botanical_names(self):
        xml=b'<article><body><p>The plant is common. This species is widespread. Mirabilis laevis grows here.</p></body></article>'
        names=[x["candidate_plant_name"] for x in candidates_from_xml(xml,"url","PMC1")]
        self.assertEqual(names,["Mirabilis laevis"])
    def test_repeated_name_mentions_preserve_distinct_offsets(self):
        xml=b'<article><body><p id="p2">Mirabilis laevis grows. Mirabilis laevis flowers.</p></body></article>'
        rows=candidates_from_xml(xml,"url","PMC1")
        self.assertEqual(len(rows),2)
        self.assertEqual([r["name_start_offset"] for r in rows],[0,24])
        self.assertTrue(all(r["feeding_observation_status"]=="not_verified" for r in rows))
    def test_table_cells_extract_without_double_counting(self):
        xml=b'<article><body><table-wrap><caption><p>Recorded food taxa</p></caption><table><thead><tr><th id="h1">Plant species</th></tr></thead><tbody><tr><td id="c1"><italic>Rumex crispus</italic></td><td id="c2">Plantago major</td></tr></tbody></table></table-wrap></body></article>'
        rows=candidates_from_xml(xml,"url","PMC1")
        names=[r["candidate_plant_name"] for r in rows]
        self.assertEqual(names,["Rumex crispus","Plantago major"])
        self.assertEqual([r["source_element"] for r in rows],["td","td"])
        self.assertEqual([r["source_element_id"] for r in rows],["c1","c2"])
        self.assertTrue(all(r["feeding_observation_status"]=="not_verified" and r["feeding_safety_status"]=="unassessed" for r in rows))
    def test_rejects_wrong_root(self):
        with self.assertRaises(ValueError):
            candidates_from_xml(b'<error/>',"url","PMC1")
    def test_no_names(self):
        self.assertEqual(candidates_from_xml(b'<article><body><p>No botanical name.</p></body></article>',"url","PMC1"),[])
if __name__=="__main__":
    unittest.main()
