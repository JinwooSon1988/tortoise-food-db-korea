#!/usr/bin/env python3
"""Offline tests for polite_http: robots.txt rules and failures, per-host spacing and Crawl-delay, Retry-After on 429,
no retry on 404, provenance rows, checkpoint resume after an interruption, bounded worker pool."""
import http.server
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import polite_http as ph  # noqa: E402

HITS = []


class Handler(http.server.BaseHTTPRequestHandler):
    robots = "User-agent: *\nDisallow: /private\nCrawl-delay: 0.3\n"
    robots_status = 200
    flaky = {"n": 0}

    def log_message(self, *a):
        pass

    def do_GET(self):
        HITS.append((self.path, time.monotonic()))
        if self.path == "/robots.txt":
            self.send_response(self.robots_status); self.end_headers()
            if self.robots_status == 200:
                self.wfile.write(self.robots.encode())
            return
        if self.path == "/limited":
            Handler.flaky["n"] += 1
            if Handler.flaky["n"] == 1:
                self.send_response(429); self.send_header("Retry-After", "0.2"); self.end_headers(); return
        if self.path == "/missing":
            self.send_response(404); self.end_headers(); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"path": self.path}).encode())


def serve():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


class PoliteTests(unittest.TestCase):
    def setUp(self):
        HITS.clear(); Handler.flaky["n"] = 0; Handler.robots_status = 200
        self.srv, self.base = serve()
        self.tmp = Path(tempfile.mkdtemp())
        self.client = ph.PoliteClient(provenance=self.tmp / "prov.jsonl", timeout=5, retries=2)

    def tearDown(self):
        self.srv.shutdown()

    def prov(self):
        return [json.loads(l) for l in (self.tmp / "prov.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_robots_disallow_and_crawl_delay(self):
        with self.assertRaises(ph.RobotsDisallowed):
            self.client.get(self.base + "/private/x")
        self.assertNotIn("/private/x", [p for p, _ in HITS])
        self.client.get(self.base + "/a"); self.client.get(self.base + "/b")
        times = [t for p, t in HITS if p in ("/a", "/b")]
        self.assertGreaterEqual(times[1] - times[0], 0.95)  # spacing is the larger of the policy (1 s) and Crawl-delay
        self.assertEqual(sum(1 for p, _ in HITS if p == "/robots.txt"), 1)
        rows = self.prov()
        self.assertTrue(any(r["kind"] == "fetch" and r.get("robots") == "disallowed" for r in rows))
        ok = [r for r in rows if r["kind"] == "fetch" and r.get("status") == 200]
        self.assertTrue(all(len(r["sha256"]) == 64 and r["final_url"] and r["fetched_at"] for r in ok))

    def test_robots_5xx_means_disallow_and_4xx_allow(self):
        Handler.robots_status = 503
        self.assertFalse(self.client.allowed(self.base + "/a"))
        Handler.robots_status = 404
        other = ph.PoliteClient(timeout=5)
        self.assertTrue(other.allowed(self.base + "/a"))

    def test_retry_after_then_success_and_no_retry_on_404(self):
        data, row = self.client.get_json(self.base + "/limited")
        self.assertEqual(data["path"], "/limited")
        self.assertEqual(row["attempt"], 1)
        with self.assertRaises(ph.FetchError) as cm:
            self.client.get(self.base + "/missing")
        self.assertTrue(cm.exception.final)
        self.assertEqual(sum(1 for p, _ in HITS if p == "/missing"), 1)

    def test_default_spacing_one_second_for_unknown_hosts(self):
        Handler.robots = "User-agent: *\nAllow: /\n"
        try:
            c = ph.PoliteClient(timeout=5)
            c.get(self.base + "/x"); c.get(self.base + "/y")
            t = {p: s for p, s in HITS}
            self.assertGreaterEqual(t["/y"] - t["/x"], 0.95)
        finally:
            Handler.robots = "User-agent: *\nDisallow: /private\nCrawl-delay: 0.3\n"

    def test_checkpoint_resume_and_bounded_pool(self):
        cp_path = self.tmp / "cp.jsonl"
        cp = ph.Checkpoint(cp_path)
        seen, active, peak, lock = [], [0], [0], threading.Lock()

        def fn(i):
            with lock:
                active[0] += 1; peak[0] = max(peak[0], active[0])
            time.sleep(0.01)
            with lock:
                active[0] -= 1; seen.append(i)
            if i == 3:
                raise ph.FetchError("u", 503, "busy", final=False)
            if i == 4:
                raise ph.FetchError("u", 404, "gone", final=True)
            return "ok", {"value": i}

        summary = ph.run_tasks(((f"k{i}", i) for i in range(10)), fn, cp, workers=3)
        self.assertEqual(summary, {"ok": 8, "retry": 1, "final": 1})
        self.assertLessEqual(peak[0], 3)
        with cp_path.open("a", encoding="utf-8") as f:
            f.write('{"key": "k9", "status": "ok"')  # a line cut by an interruption
        seen.clear()
        resumed = ph.Checkpoint(cp_path)
        ph.run_tasks(((f"k{i}", i) for i in range(10)), fn, resumed, workers=3)
        self.assertEqual(sorted(seen), [3])  # only the transient failure runs again


if __name__ == "__main__":
    unittest.main(verbosity=1)
