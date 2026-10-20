#!/usr/bin/env python3
"""Generate a bilingual, searchable taxonomy-only directory from staged records.

This is deliberately separate from reviewed feeding pages. Never display a
green feeding badge or an A-D grade for taxonomy-only records.
"""
import argparse
import html
import json
from pathlib import Path


def build(records):
    safe = html.escape
    payload = []
    seen = set()
    for record in records:
        if record.get("feeding_status") != "unverified" or record.get("feeding_grade") is not None:
            raise ValueError("Bulk taxonomy directory accepts only unverified feeding records")
        if record.get("publication_status") != "staged_not_public":
            raise ValueError("Bulk taxonomy directory requires staged taxonomy records")
        name = str(record.get("scientific") or "").strip()
        source = str(record.get("taxonomy_source_url") or "").strip()
        if not name or not record.get("taxon_id"):
            raise ValueError("Missing taxon identity")
        if name.casefold() in seen:
            raise ValueError("Duplicate scientific name: " + name)
        seen.add(name.casefold())
        payload.append({
            "scientific": name,
            "family": record.get("family") or "",
            "rank": record.get("rank") or "",
            "taxon_id": str(record["taxon_id"]),
            "source_url": source if source.startswith("https://") else "",
        })
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    return """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>식물 분류 검색 | Plant Taxonomy Directory</title>
<style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#152c22;background:#f7faf7}
*{box-sizing:border-box}body{max-width:1050px;margin:auto;padding:24px}
h1{font-size:clamp(1.4rem,4vw,2.2rem)}.note{border-left:4px solid #ac6b13;padding:14px;background:#fff4e4}
input{width:100%;padding:16px;border:1px solid #8da69a;border-radius:12px;font-size:1rem;margin:20px 0}
#results{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
article{background:white;border:1px solid #d6e4da;border-radius:14px;padding:16px}
article h2{font-size:1.05rem;margin:0 0 8px;font-style:italic;overflow-wrap:anywhere}
small{display:block;color:#456455;margin-bottom:10px}.hold{font-weight:700;color:#825011}
a{color:#075e4a}#count{margin:8px 0 18px}
</style></head><body>
<h1>식물 분류 검색 <span lang="en">/ Plant Taxonomy Directory</span></h1>
<p class="note"><b>급여 안전성 미확정 / Feeding safety not established.</b>
이 목록은 식물 분류 기록이며 육지거북 먹이 추천이 아닙니다.
These taxonomy records are not tortoise feeding recommendations.</p>
<label for="q">학명·과명 검색 / Search scientific name or family</label>
<input id="q" type="search" autocomplete="off" placeholder="Scientific name / Family">
<p id="count" aria-live="polite"></p><div id="results"></div>
<script>
const taxa = __DATA__;
const q = document.getElementById("q"), out=document.getElementById("results"), count=document.getElementById("count");
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pageSize=100;
function render(){
 const needle=q.value.trim().toLocaleLowerCase();
 const found=needle?taxa.filter(t=>(t.scientific+" "+t.family).toLocaleLowerCase().includes(needle)):taxa;
 count.textContent=found.length.toLocaleString()+" records / 건 (showing first "+Math.min(found.length,pageSize)+")";
 out.innerHTML=found.slice(0,pageSize).map(t=>'<article><h2>'+esc(t.scientific)+'</h2><small>'+esc(t.family)+' · '+esc(t.rank)+'</small><div class="hold">급여 안전성 미확정 / Unverified</div>'+(t.source_url?'<p><a target="_blank" rel="noopener noreferrer" href="'+esc(t.source_url)+'">분류 출처 / Taxonomy source ↗</a></p>':'')+'</article>').join("");
}
q.addEventListener("input",render);render();
</script></body></html>""".replace("__DATA__", data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    records = source["records"] if isinstance(source, dict) else source
    if not isinstance(records, list):
        raise ValueError("Expected list of records")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build(records), encoding="utf-8")
    print(f"Generated {len(records)} taxonomy-only entries at {args.output}")


if __name__ == "__main__":
    main()
