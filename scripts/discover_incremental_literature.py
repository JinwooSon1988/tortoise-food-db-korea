#!/usr/bin/env python3
"""Checkpointed incremental OpenAlex discovery. Metadata leads only, never feeding verdicts.

Every run continues where the last one stopped: each query has its own page cursor, so a revisited query fetches its
NEXT page instead of page 1 again (the old single cursor wrapped after 85 queries and then re-ran the same first pages,
which is why cycles reported new_works 0). A query is closed when OpenAlex has no more results, when it reaches
--max-pages, or when a page brings no new tortoise-related work (results are relevance-ranked, so the tail is noise).

OpenAlex bills every list page the same (10 credits, measured 2026-10-25), whatever per-page is, so pages are fetched
at 200 works. Without OPENALEX_API_KEY all users on this IP share one small daily budget; the run reads
X-RateLimit-Remaining from every response and stops while --reserve credits are left. A 429 sets a cooldown until the
budget resets. One metrics line per run goes to --metrics (requests, errors, new works, new tortoise works, new
open-access PDFs, remaining credits, plan progress).

  python scripts/discover_incremental_literature.py [--max-requests 8] [--max-pages 5] [--reserve 200]
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "evidence_corpus" / "batch_004"))
from collect_worldwide_tortoise_literature import API, GENERA, normalized  # noqa: E402
from discover_openalex import TITLE as TORTOISE  # noqa: E402
from polite_http import FetchError, HostPolicy, PoliteClient, RobotsDisallowed  # noqa: E402

OPENALEX_POLICY = HostPolicy(3.0, 1, "https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication",
                             "3 s between requests, as in scripts/research_bulk_leads.py")
SELECT = ("id,doi,title,publication_year,publication_date,type,language,ids,primary_location,best_oa_location,"
          "open_access,abstract_inverted_index")


# OpenAlex title_and_abstract.search ANDs plain words ("Geochelone food plants foraging" -> 0 works), while the free
# "search" parameter matched unrelated papers. Each query is therefore "<subject> AND (any diet term)": measured
# 2026-10-25, "Geochelone AND DIET" returned 136 works in one page, nearly all tortoise diet papers.
DIET = ('(diet OR diets OR feeding OR food OR forage OR foraging OR herbivory OR frugivory OR faeces OR feces OR fecal OR '
        'faecal OR scat OR "stomach contents" OR grazing OR browsing OR "seed dispersal")')
HUSBANDRY = "(captive OR captivity OR husbandry OR zoo OR nutrition OR nutritional)"
OTHER_LANGUAGES = ['"tortuga terrestre" AND (dieta OR alimentación OR alimentacion)',
                   'jabuti AND (dieta OR alimentação OR alimentacao OR frugivoria)',
                   '"tortue terrestre" AND (alimentation OR régime)', 'kaplumbağa AND beslenme',
                   'Landschildkröte AND (Nahrung OR Ernährung)', 'testuggine AND (dieta OR alimentazione)']


def quoted(subject):
    return f'"{subject}"' if " " in subject else subject


def query_plan():
    """Deterministic, de-duplicated query list: tortoise and genus subjects x (diet, husbandry), then other languages.
    Species subjects are not queried: measured 2026-10-25, every species query returned only works its genus query
    had already returned (a genus query is complete, or is paged further), and "tortoises" stems to "tortoise"."""
    subjects = ["tortoise", "Testudinidae"] + list(GENERA)
    plan = [f"{quoted(x)} AND {DIET}" for x in subjects] + [f"{quoted(x)} AND {HUSBANDRY}" for x in subjects] + OTHER_LANGUAGES
    return list(dict.fromkeys(plan))


def is_tortoise_work(work):
    return bool(TORTOISE.search((work.get("title") or "") + " " + (work.get("abstract") or "")))


def page_url(query, page, per_page, api_key=None, email=None):
    params = {"filter": "title_and_abstract.search:" + query.replace(",", " "), "per-page": str(per_page),
              "page": str(page), "select": SELECT}
    if api_key:
        params["api_key"] = api_key
    if email:
        params["mailto"] = email
    return API + "?" + urllib.parse.urlencode(params)


def remaining_credits(row):
    try:
        return int((row.get("ratelimit") or {}).get("x-ratelimit-remaining"))
    except (TypeError, ValueError):
        return None


def run(state, works, client, args, now=time.time):
    """One bounded discovery run; mutates state and works, returns the metrics row."""
    plan = query_plan()
    queries = state.setdefault("queries", {})
    metrics = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now())), "requests": 0, "ok": 0,
               "errors": {}, "new_works": 0, "new_tortoise_works": 0, "new_open_access_pdf": 0,
               "queries_touched": [], "stopped": None, "remaining_credits": None}
    if now() < state.get("cooldown_until", 0):
        metrics["stopped"] = "cooldown"
        metrics["retry_after_seconds"] = round(state["cooldown_until"] - now())
        return metrics
    open_queries = [q for q in plan if not queries.get(q, {}).get("closed")]
    if not open_queries:
        metrics["stopped"] = "plan_exhausted"
        return metrics
    start = state.get("cursor", 0) % len(plan)
    order = [q for q in plan[start:] + plan[:start] if q in open_queries]
    for query in order:
        if metrics["requests"] >= args.max_requests:
            metrics["stopped"] = "max_requests"
            break
        # A reading taken before the budget's reset time no longer applies.
        left = state.get("remaining_credits") if now() < state.get("credits_valid_until", 0) else None
        if left is not None and left <= args.reserve:
            metrics["stopped"] = "budget_reserve"
            break
        q = queries.setdefault(query, {"next_page": 1, "closed": False})
        page = q["next_page"]
        metrics["requests"] += 1
        try:
            data, row = client.get_json(page_url(query, page, args.per_page, os.environ.get("OPENALEX_API_KEY"),
                                                 os.environ.get("OPENALEX_EMAIL")), purpose="openalex incremental discovery")
        except (FetchError, RobotsDisallowed) as exc:
            code = str(getattr(exc, "status", None) or type(exc).__name__)
            metrics["errors"][code] = metrics["errors"].get(code, 0) + 1
            state.setdefault("failures", []).append({"query": query, "page": page, "error": str(exc)[:200], "time": now()})
            state["failures"] = state["failures"][-50:]
            if code == "429":
                # Budget exhausted: no request until the reported reset (or one hour if unknown).
                state["cooldown_until"] = now() + max(1800, min(86400, int(state.get("reset_seconds") or 3600)))
                metrics["stopped"] = "rate_limited"
                break
            if getattr(exc, "final", False):
                q.update(closed=True, reason="http_" + code)
            continue
        metrics["ok"] += 1
        credits = remaining_credits(row)
        if credits is not None:
            state["remaining_credits"] = metrics["remaining_credits"] = credits
            try:
                state["reset_seconds"] = int(row["ratelimit"].get("x-ratelimit-reset"))
            except (TypeError, ValueError, KeyError):
                state["reset_seconds"] = 3600
            state["credits_valid_until"] = now() + state["reset_seconds"]
        results = data.get("results") or []
        new = new_tortoise = 0
        for w in results:
            key = w.get("id")
            if not key or key in works:
                continue
            rec = normalized(w, query.split(" AND ")[0].strip('"'), query)
            works[key] = rec
            new += 1
            if is_tortoise_work(rec):
                new_tortoise += 1
                metrics["new_open_access_pdf"] += bool(rec.get("best_oa_pdf") or rec.get("fulltext_url"))
        metrics["new_works"] += new
        metrics["new_tortoise_works"] += new_tortoise
        metrics["queries_touched"].append({"query": query, "page": page, "results": len(results), "new": new,
                                           "new_tortoise": new_tortoise})
        q["next_page"] = page + 1
        q["pages_done"] = page
        if len(results) < args.per_page:
            q.update(closed=True, reason="no_more_results")
        elif page >= args.max_pages:
            q.update(closed=True, reason="max_pages")
        elif new_tortoise == 0 and page > 1:
            q.update(closed=True, reason="no_new_tortoise_work")
        state["cursor"] = (plan.index(query) + 1) % len(plan)
    metrics["plan"] = {"queries": len(plan), "closed": sum(1 for x in plan if queries.get(x, {}).get("closed"))}
    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="worker-output/discovery-state.json")
    ap.add_argument("--out", default="worker-output/worldwide-literature.json")
    ap.add_argument("--metrics", default="worker-output/discovery-metrics.jsonl")
    ap.add_argument("--provenance", default="worker-output/discovery-requests.jsonl")
    ap.add_argument("--max-requests", type=int, default=8)
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--per-page", type=int, default=200)
    ap.add_argument("--reserve", type=int, default=200, help="credits left untouched for other users of this IP")
    # Accepted for compatibility with the existing worker command line (--queries 2 --pages 1).
    ap.add_argument("--queries", type=int, help=argparse.SUPPRESS)
    ap.add_argument("--pages", type=int, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.queries:
        args.max_requests = max(args.max_requests, args.queries)
    if not 1 <= args.max_requests <= 100 or not 1 <= args.per_page <= 200 or not 1 <= args.max_pages <= 50:
        ap.error("--max-requests 1..100, --per-page 1..200, --max-pages 1..50")
    statefile, output = Path(args.state), Path(args.out)
    state = json.loads(statefile.read_text(encoding="utf-8")) if statefile.exists() else {"cursor": 0, "failures": []}
    corpus = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"works": []}
    works = {str(w.get("openalex_id") or w.get("id")): w for w in corpus.get("works", []) if w.get("openalex_id") or w.get("id")}
    before = len(works)
    client = PoliteClient(provenance=args.provenance, retries=1, policies={"api.openalex.org": OPENALEX_POLICY})
    try:
        metrics = run(state, works, client, args)
    finally:
        # Checkpoint even after an interruption: corpus first (temp + rename), then state.
        corpus["works"] = list(works.values())
        corpus["warning"] = "Bibliographic leads only; no tortoise feeding safety assertions."
        for path, doc in ((output, corpus), (statefile, state)):
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(path)
    metrics.update(total_works=len(works), total_before=before, http=client.stats)
    Path(args.metrics).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.metrics).open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
    summary = {k: metrics.get(k) for k in ("requests", "ok", "errors", "new_works", "new_tortoise_works", "new_open_access_pdf",
                                           "total_works", "remaining_credits", "stopped", "plan")}
    summary["queries_completed"] = metrics["ok"]
    summary["cursor"] = state.get("cursor")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
