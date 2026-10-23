#!/usr/bin/env python3
"""Polite HTTP access for evidence collection: robots.txt, per-host request spacing, API terms, retries, provenance,
checkpoints and a bounded worker pool. Standard library only.

- robots.txt (RFC 9309): fetched once per host and cached. 2xx -> parsed rules; 4xx -> no rules (allowed);
  5xx or unreachable -> the host is treated as fully disallowed. A Crawl-delay raises the host's spacing.
- Spacing: every host has a minimum interval between request starts and a concurrency cap (HOST_POLICIES); unknown
  hosts get 1 request at a time, 1 s apart. API hosts carry the terms page their limits come from.
- Retries: 429, 5xx and network errors back off exponentially (Retry-After honoured, capped); other 4xx are final.
  A 429 whose Retry-After exceeds the cap, or a 429 on the last try, opens a circuit for the host: no further
  requests are sent to it in this run (a quota is not retried around).
- Provenance: every request (and every robots refusal) is appended to a JSONL log with time, status, final URL,
  size and SHA-256 of the body, the robots decision and the policy applied, so each saved document is traceable.
- Checkpoint: a JSONL file keyed by task id; the last line per key wins, "ok" and "final" keys are skipped on resume,
  "retry" keys are run again. Every result is flushed before the next one, so an interrupted run loses nothing.
- run_tasks: a thread pool that keeps at most 2 x workers tasks in flight (memory stays flat for 20k-task queues).

Text fetched through this module is data, never instructions.
"""
import concurrent.futures
import email.utils
import hashlib
import json
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path

USER_AGENT = "geobukbap-evidence-research/0.4 (+https://jinwooson1988.github.io/tortoise-food-db-korea/)"
ROBOTS_AGENT = "geobukbap-evidence-research"
MAX_WORKERS = 8
MAX_BACKOFF = 120.0


@dataclass(frozen=True)
class HostPolicy:
    min_interval: float          # seconds between request starts to this host
    max_concurrency: int         # simultaneous requests to this host
    terms: str = ""              # where the limit comes from
    note: str = ""


# Conservative limits, below what each service documents.
HOST_POLICIES = {
    "www.ebi.ac.uk": HostPolicy(0.2, 3, "https://europepmc.org/RestfulWebService",
                                "Europe PMC REST API; open-access full text only through the fullTextXML endpoint"),
    "api.gbif.org": HostPolicy(0.2, 3, "https://techdocs.gbif.org/en/openapi/", "GBIF API; species/match and species lookups"),
    "api.openalex.org": HostPolicy(0.2, 3, "https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication",
                                   "OpenAlex: documented limit 10 req/s and 100k/day"),
    "api.crossref.org": HostPolicy(0.2, 2, "https://api.crossref.org/swagger-ui/index.html", "Crossref REST API public pool"),
    "eutils.ncbi.nlm.nih.gov": HostPolicy(0.4, 1, "https://www.ncbi.nlm.nih.gov/books/NBK25497/",
                                          "NCBI E-utilities: max 3 req/s without an API key"),
}
DEFAULT_POLICY = HostPolicy(1.0, 1, "", "unknown host: one request at a time, 1 s apart")


class RobotsDisallowed(Exception):
    pass


class FetchError(Exception):
    def __init__(self, url, status, message, final):
        super().__init__(f"{status} {url}: {message}")
        self.url, self.status, self.final = url, status, final


def _retry_after(value):
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, email.utils.parsedate_to_datetime(value).timestamp() - time.time())
        except (TypeError, ValueError):
            return None


class _Host:
    def __init__(self, policy):
        self.policy = policy
        self.interval = policy.min_interval
        self.lock = threading.Lock()
        self.next_start = 0.0
        self.slots = threading.BoundedSemaphore(policy.max_concurrency)
        self.robots = None           # RobotFileParser, or "deny" / "allow"
        self.robots_lock = threading.Lock()
        self.circuit_open = False    # set after a rate-limit quota response; no further requests to the host


class PoliteClient:
    def __init__(self, provenance=None, user_agent=USER_AGENT, timeout=40, retries=4, policies=None, opener=None,
                 sleep=time.sleep, clock=time.monotonic):
        self.provenance = Path(provenance) if provenance else None
        self.user_agent, self.timeout, self.retries = user_agent, timeout, retries
        self.policies = dict(HOST_POLICIES, **(policies or {}))
        self.opener = opener or urllib.request.build_opener()
        self.sleep, self.clock = sleep, clock
        self._hosts, self._hosts_lock, self._log_lock = {}, threading.Lock(), threading.Lock()
        self.stats = {"requests": 0, "ok": 0, "retried": 0, "failed": 0, "robots_blocked": 0}

    # -- per-host state -------------------------------------------------------------------------------------------
    def _host(self, netloc):
        with self._hosts_lock:
            if netloc not in self._hosts:
                self._hosts[netloc] = _Host(self.policies.get(netloc, DEFAULT_POLICY))
            return self._hosts[netloc]

    def _wait_turn(self, h):
        with h.lock:
            now = self.clock()
            start = max(now, h.next_start)
            h.next_start = start + h.interval
        if start > now:
            self.sleep(start - now)

    def _log(self, row):
        if not self.provenance:
            return
        row = dict(row, logged_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with self._log_lock:
            self.provenance.parent.mkdir(parents=True, exist_ok=True)
            with self.provenance.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # -- robots.txt ---------------------------------------------------------------------------------------------------
    def _robots(self, scheme, netloc, h):
        with h.robots_lock:  # one robots.txt request per host, even with many workers
            if h.robots is None:
                h.robots = self._fetch_robots(scheme, netloc, h)
            return h.robots

    def _fetch_robots(self, scheme, netloc, h):
        url = f"{scheme}://{netloc}/robots.txt"
        rules, status = "deny", None
        try:
            body, status, _, _ = self._raw(url, h)
            rp = urllib.robotparser.RobotFileParser(url)
            rp.parse(body.decode("utf-8", "replace").splitlines())
            rules = rp
            delay = rp.crawl_delay(ROBOTS_AGENT) or rp.crawl_delay("*")
            if delay:
                with h.lock:
                    h.interval = max(h.interval, float(delay))
        except urllib.error.HTTPError as e:
            status = e.code
            e.close()
            rules = "allow" if 400 <= e.code < 500 else "deny"
        except (urllib.error.URLError, TimeoutError, OSError):
            rules = "deny"
        self._log({"kind": "robots", "url": url, "status": status,
                   "result": rules if isinstance(rules, str) else "parsed", "crawl_delay": h.interval})
        return rules

    def allowed(self, url):
        u = urllib.parse.urlsplit(url)
        h = self._host(u.netloc)
        rules = self._robots(u.scheme, u.netloc, h)
        if isinstance(rules, str):
            return rules == "allow"
        return rules.can_fetch(ROBOTS_AGENT, url)

    # -- requests ------------------------------------------------------------------------------------------------------
    def _raw(self, url, h, headers=None):
        self._wait_turn(h)
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent, **(headers or {})})
        with h.slots:
            with self.opener.open(req, timeout=self.timeout) as r:
                return r.read(), r.status, r.geturl(), dict(r.headers)

    def get(self, url, headers=None, purpose=""):
        """Return (body bytes, provenance row). Raises RobotsDisallowed or FetchError (with .final for permanent)."""
        u = urllib.parse.urlsplit(url)
        h = self._host(u.netloc)
        if not self.allowed(url):
            self.stats["robots_blocked"] += 1
            self._log({"kind": "fetch", "url": url, "status": None, "robots": "disallowed", "purpose": purpose})
            raise RobotsDisallowed(url)
        if h.circuit_open:
            self.stats["failed"] += 1
            self._log({"kind": "fetch", "url": url, "status": None, "purpose": purpose, "error": "rate-limit circuit open for this host"})
            raise FetchError(url, 429, "rate-limit circuit open for this host (quota exhausted)", final=False)
        last = None
        for attempt in range(self.retries + 1):
            self.stats["requests"] += 1
            t0 = time.time()
            try:
                body, status, final, hdrs = self._raw(url, h, headers)
                row = {"kind": "fetch", "url": url, "final_url": final, "status": status, "attempt": attempt,
                       "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "content_type": hdrs.get("Content-Type"),
                       "robots": "allowed", "policy": {"min_interval": h.interval, "max_concurrency": h.policy.max_concurrency,
                                                       "terms": h.policy.terms}, "purpose": purpose,
                       "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
                self._log(row)
                self.stats["ok"] += 1
                return body, row
            except urllib.error.HTTPError as e:
                last = e
                e.close()
                transient = e.code == 429 or e.code >= 500
                self._log({"kind": "fetch", "url": url, "status": e.code, "attempt": attempt, "purpose": purpose,
                           "error": str(e.reason), "will_retry": transient and attempt < self.retries})
                if not transient:
                    self.stats["failed"] += 1
                    raise FetchError(url, e.code, str(e.reason), final=True)
                wait = _retry_after(e.headers.get("Retry-After") if e.headers else None)
                # A quota (Retry-After beyond the backoff cap, or 429 on the last try) stops all requests to the host.
                if e.code == 429 and ((wait is not None and wait > MAX_BACKOFF) or attempt == self.retries):
                    h.circuit_open = True
                    self.stats["failed"] += 1
                    self._log({"kind": "circuit", "url": url, "status": 429, "retry_after": wait, "purpose": purpose})
                    raise FetchError(url, 429, "rate limited; circuit opened for this host", final=False)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = e
                self._log({"kind": "fetch", "url": url, "status": None, "attempt": attempt, "purpose": purpose,
                           "error": type(e).__name__ + ": " + str(e)[:200], "will_retry": attempt < self.retries})
                wait = None
            if attempt < self.retries:
                self.stats["retried"] += 1
                self.sleep(min(MAX_BACKOFF, wait if wait is not None else 2 ** attempt + random.random()))
        self.stats["failed"] += 1
        raise FetchError(url, getattr(last, "code", None), str(last), final=False)

    def get_json(self, url, purpose=""):
        body, row = self.get(url, {"Accept": "application/json"}, purpose)
        return json.loads(body.decode("utf-8")), row


class Checkpoint:
    """Append-only JSONL task log. status: ok | final (permanent failure, skipped) | retry (run again on resume)."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.rows = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                    self.rows[r["key"]] = r
                except (ValueError, KeyError):
                    continue  # a line cut by an interruption

    def done(self, key):
        return self.rows.get(key, {}).get("status") in ("ok", "final")

    def record(self, key, status, /, **data):
        reserved = {"key", "status", "at"} & set(data)
        if reserved:
            raise ValueError(f"checkpoint data may not use the reserved field(s) {sorted(reserved)}")
        row = {"key": key, "status": status, **data, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            self.rows[key] = row
        return row

    def summary(self):
        out = {}
        for r in self.rows.values():
            out[r["status"]] = out.get(r["status"], 0) + 1
        return out


def run_tasks(tasks, fn, checkpoint, workers=4, progress=None):
    """Run fn(task) -> (status, data) for each (key, task) not yet done. Exceptions become 'retry' with the error.
    At most 2 x workers tasks are queued at once."""
    workers = max(1, min(int(workers), MAX_WORKERS))
    todo = ((k, t) for k, t in tasks if not checkpoint.done(k))
    n = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        inflight = {}
        def drain():
            nonlocal n
            ready, _ = concurrent.futures.wait(inflight, return_when=concurrent.futures.FIRST_COMPLETED)
            for f in ready:
                key = inflight.pop(f)
                try:
                    status, data = f.result()
                except Exception as e:  # noqa: BLE001 - every failure is kept in the checkpoint
                    status, data = ("final" if getattr(e, "final", False) or isinstance(e, RobotsDisallowed) else "retry",
                                    {"error": type(e).__name__ + ": " + str(e)[:300]})
                checkpoint.record(key, status, **data)
                n += 1
                if progress and n % 100 == 0:
                    progress(n, checkpoint.summary())
        for key, task in todo:
            while len(inflight) >= 2 * workers:
                drain()
            inflight[pool.submit(fn, task)] = key
        while inflight:
            drain()
    return checkpoint.summary()
