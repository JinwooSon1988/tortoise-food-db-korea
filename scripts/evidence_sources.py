"""Source identity for public evidence records.

Several evidence records can cite the same original (one paper, one database page). They are kept, because a
record can hold a different result or reading of that original, but they are one source. Every record carries a
`source_id` derived from its identifiers (DOI > PMID > PMCID > The Tortoise Table plant number > normalized URL);
records that only restate the finding of another record of the same source carry `same_finding_as`.

Used by the page generators (source counts, one card per finding), the source registry and the integrity QA.
"""
import re

TT_PLANT = re.compile(r"thetortoisetable\.org\.uk/plant-database/viewplants/\?(?:[^#]*&)?plant=(\d+)", re.I)
TT_LISTING = re.compile(r"thetortoisetable\.org\.uk/plant-database/viewplants/(?:a-z|colour|search|category)/", re.I)
SEARCH_OR_LIST_URL = re.compile(r"[?&](?:searchtxt|searchchoice|q|query|search)=|/(?:search|a-z|colour|category)/(?:\?|$)", re.I)


def norm_doi(v):
    v = str(v or "").strip()
    v = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", v, flags=re.I)
    return v.rstrip("/").lower() or None


def identifiers(r):
    """DOI, PMID, PMCID and URL key of a record, each from its field or from its URL."""
    url = str(r.get("url") or "").strip()
    out = {"doi": norm_doi(r.get("doi")), "pmid": str(r.get("pmid")).strip() if r.get("pmid") else None, "pmcid": None,
           "doi_in_url": None, "pmid_in_url": None, "url_key": None}
    m = re.search(r"doi\.org/(.+)$", url, re.I)
    if m:
        out["doi_in_url"] = norm_doi(m.group(1))
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", url)
    if m:
        out["pmid_in_url"] = m.group(1)
    m = re.search(r"\b(PMC\d+)\b", url, re.I)
    if m:
        out["pmcid"] = m.group(1).upper()
    if url:
        m = TT_PLANT.search(url)
        if m:
            out["url_key"] = f"thetortoisetable:plant={int(m.group(1))}"
        else:
            u = re.sub(r"^https?://(?:www\.)?", "", url.split("#")[0], flags=re.I).rstrip("/")
            host, _, rest = u.partition("/")
            out["url_key"] = "url:" + host.lower() + ("/" + rest if rest else "")
    return out


def computed_source_id(r):
    i = identifiers(r)
    doi = i["doi"] or i["doi_in_url"]
    if doi:
        return "doi:" + doi
    pmid = i["pmid"] or i["pmid_in_url"]
    if pmid:
        return "pmid:" + pmid
    if i["pmcid"]:
        return "pmc:" + i["pmcid"]
    return i["url_key"] or "record:" + str(r.get("id"))


def source_of(r):
    return r.get("source_id") or computed_source_id(r)


def shown_records(linked):
    """Records shown as separate cards: a record that restates another linked record of the same source is folded in."""
    ids = {e.get("id") for e in linked}
    return [e for e in linked if e.get("same_finding_as") not in ids]


def folded_into(e, linked):
    return [x.get("id") for x in linked if x.get("same_finding_as") == e.get("id")]


def same_source_others(e, shown):
    s = source_of(e)
    return [x.get("id") for x in shown if x is not e and source_of(x) == s]


def distinct_sources(records):
    return len({source_of(e) for e in records})


def is_listing_url(url):
    u = str(url or "")
    return bool(TT_LISTING.search(u) or (SEARCH_OR_LIST_URL.search(u) and not TT_PLANT.search(u)))
