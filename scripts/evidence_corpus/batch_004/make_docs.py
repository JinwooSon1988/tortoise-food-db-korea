"""Batch 004 document list: every full text already saved by earlier batches, once per document.

- Europe PMC open-access JATS XML, from one or more "<dir with meta.jsonl and xml/>" folders (deduplicated by PMCID)
- agent folders of batches 002-003 ("<dir>/sources.jsonl" + txt/), with their citation, URL and tortoise taxa
Run: python -X utf8 -I make_docs.py <out docs.jsonl> --jats <dir> [<dir> ...] --agents <dir> [<dir> ...]
"""
import argparse
import json
import re
from pathlib import Path


def jats_docs(d):
    meta = {}
    for f in (d / "meta.jsonl",):
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    m = json.loads(line)
                except ValueError:
                    continue
                if m.get("pmcid"):
                    meta[m["pmcid"]] = m
    for x in sorted((d / "xml").glob("PMC*.xml")):
        pmcid = x.stem
        m = meta.get(pmcid, {})
        year = m.get("pubYear") or ""
        journal = ((m.get("journalInfo") or {}).get("journal") or {}).get("title") or ""
        authors = (m.get("authorString") or "").rstrip(".")
        cit = " ".join(p for p in [authors, f"({year})" if year else "", (m.get("title") or "").rstrip("."), journal] if p).strip()
        doi = m.get("doi")
        yield {"doc_id": pmcid, "path": str(x), "kind": "jats", "citation": cit or pmcid, "title": m.get("title") or "",
               "doi": doi, "url": f"https://europepmc.org/article/PMC/{pmcid}", "source_class": "peer_reviewed",
               "access": "Europe PMC open-access subset (fullTextXML endpoint)", "license": m.get("license")}


def agent_docs(d):
    for line in (d / "sources.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            s = json.loads(line)
        except ValueError:
            continue
        txt = d / (s.get("local_txt") or "")
        if not s.get("local_txt") or not txt.is_file():
            continue
        taxa = s.get("tortoise_taxa") or []
        yield {"doc_id": re.sub(r"[^A-Za-z0-9_.-]", "_", d.parent.name + "__" + d.name + "__" + s["source_id"]), "path": str(txt),
               "kind": "txt", "citation": s.get("citation") or s["source_id"], "title": s.get("citation") or "", "doi": s.get("doi"),
               "url": s.get("url"), "source_class": s.get("source_class") or "other", "access": s.get("access"),
               "tortoise_hint": taxa[0] if len(taxa) == 1 else None, "earlier_source_id": s["source_id"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--jats", nargs="*", type=Path, default=[])
    ap.add_argument("--agents", nargs="*", type=Path, default=[])
    a = ap.parse_args()
    seen, docs = set(), []
    for d in a.jats:
        for x in jats_docs(d):
            if x["doc_id"] not in seen:
                seen.add(x["doc_id"]); docs.append(x)
    for d in a.agents:
        for x in agent_docs(d):
            if x["doc_id"] not in seen:
                seen.add(x["doc_id"]); docs.append(x)
    a.out.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in docs), encoding="utf-8")
    print(len(docs), "documents;", sum(x["kind"] == "jats" for x in docs), "JATS,", sum(x["kind"] == "txt" for x in docs), "text")


if __name__ == "__main__":
    main()
