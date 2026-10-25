#!/usr/bin/env python3
"""Offline tests for discover_incremental_literature: per-query paging, closing rules, budget, 429 cooldown."""
import argparse
import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discover_incremental_literature as d  # noqa: E402
from polite_http import FetchError  # noqa: E402


def work(i, title="Diet of Testudo hermanni in Italy"):
    return {"id": f"https://openalex.org/W{i}", "title": title, "publication_year": 2020,
            "best_oa_location": {"pdf_url": f"https://example.org/{i}.pdf"}, "ids": {"pmcid": f"https://pmc/PMC{i}"}}


class FakeClient:
    """Serves pages by (query, page); records every URL so tests can count requests."""
    def __init__(self, pages, remaining=900, error=None):
        self.pages, self.remaining, self.error, self.urls = pages, remaining, error, []
        self.stats = {}

    def get_json(self, url, purpose=""):
        self.urls.append(url)
        if self.error:
            raise self.error
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        query = qs["filter"][0].split(":", 1)[1]
        page = int(qs["page"][0])
        self.remaining -= 10
        return ({"results": self.pages.get((query, page), [])},
                {"ratelimit": {"x-ratelimit-remaining": str(self.remaining), "x-ratelimit-reset": "600"}})


def args(**kw):
    base = dict(max_requests=8, max_pages=5, per_page=2, reserve=200)
    base.update(kw)
    return argparse.Namespace(**base)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.plan = d.query_plan()
        self.q0, self.q1 = self.plan[0], self.plan[1]

    def test_revisit_fetches_next_page_not_page_one(self):
        pages = {(self.q0, 1): [work(1), work(2)], (self.q0, 2): [work(3), work(4)]}
        state, works = {"cursor": 0}, {}
        client = FakeClient(pages)
        d.run(state, works, client, args(max_requests=1))
        state["cursor"] = 0  # force the same query again
        m = d.run(state, works, client, args(max_requests=1))
        pages_requested = [urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)["page"][0] for u in client.urls]
        self.assertEqual(pages_requested, ["1", "2"])
        self.assertEqual(m["new_works"], 2)
        self.assertEqual(len(works), 4)

    def test_short_page_closes_query_and_exhausted_plan_sends_nothing(self):
        state, works = {"cursor": 0, "queries": {q: {"closed": True} for q in self.plan[1:]}}, {}
        client = FakeClient({(self.q0, 1): [work(1)]})
        d.run(state, works, client, args())
        self.assertEqual(state["queries"][self.q0]["reason"], "no_more_results")
        m = d.run(state, works, client, args())
        self.assertEqual(m["stopped"], "plan_exhausted")
        self.assertEqual(len(client.urls), 1)

    def test_page_without_new_tortoise_work_closes_query(self):
        noise = [work(10, "Oil palm yields"), work(11, "Urban heat islands")]
        state = {"cursor": 0, "queries": {self.q0: {"next_page": 2, "closed": False}}}
        d.run(state, {}, FakeClient({(self.q0, 2): noise}), args(max_requests=1))
        self.assertEqual(state["queries"][self.q0]["reason"], "no_new_tortoise_work")

    def test_budget_reserve_stops_before_spending_shared_credits(self):
        state = {"cursor": 0, "remaining_credits": 150, "credits_valid_until": 10 ** 12}
        client = FakeClient({})
        m = d.run(state, {}, client, args())
        self.assertEqual(m["stopped"], "budget_reserve")
        self.assertEqual(client.urls, [])

    def test_stale_budget_reading_does_not_block(self):
        state = {"cursor": 0, "remaining_credits": 10, "credits_valid_until": 1}
        client = FakeClient({(self.q0, 1): [work(1), work(2)]})
        m = d.run(state, {}, client, args(max_requests=1))
        self.assertEqual(m["ok"], 1)

    def test_429_sets_cooldown_and_next_run_sends_nothing(self):
        state = {"cursor": 0}
        client = FakeClient({}, error=FetchError("u", 429, "rate limited", final=False))
        m = d.run(state, {}, client, args())
        self.assertEqual(m["stopped"], "rate_limited")
        self.assertEqual(len(client.urls), 1)
        m = d.run(state, {}, client, args())
        self.assertEqual(m["stopped"], "cooldown")
        self.assertEqual(len(client.urls), 1)

    def test_metrics_count_new_tortoise_and_open_access(self):
        pages = {(self.q0, 1): [work(1), work(2, "Soil microbes")]}
        m = d.run({"cursor": 0}, {}, FakeClient(pages), args(max_requests=1))
        self.assertEqual((m["new_works"], m["new_tortoise_works"], m["new_open_access_pdf"]), (2, 1, 1))
        self.assertEqual(m["remaining_credits"], 890)

    def test_old_state_with_single_cursor_is_accepted(self):
        state = {"cursor": 27, "failures": [{"query": "x", "error": "HTTP Error 429", "time": 1}]}
        client = FakeClient({(self.plan[27], 1): [work(5), work(6)]})
        d.run(state, {}, client, args(max_requests=1))
        self.assertIn(self.plan[27], state["queries"])
        self.assertEqual(state["cursor"], 28)

    def test_records_are_unreviewed_leads(self):
        rec = d.normalized(work(1), "Testudo", "q")
        self.assertEqual(rec["review_state"], "bibliography_only_not_plant_evidence")
        self.assertIsNone(rec["feeding_verdict"])
        self.assertEqual(rec["pmcid"], "PMC1")


if __name__ == "__main__":
    unittest.main()
