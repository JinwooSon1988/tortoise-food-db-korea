#!/usr/bin/env python3
import pathlib,sys
p=pathlib.Path(__file__).with_name("ingest_wcvp_dwca.py").read_text(encoding="utf-8")
need=["feed_review_status","identity_only","accepted_source_record_id","taxonomic_status","source_record_id"]
missing=[x for x in need if x not in p]
if missing: print("missing contract fields:",missing);sys.exit(1)
for forbidden in ['"safe":true','"feeding_verdict"','"verdict":"safe"']:
 if forbidden in p.replace(" ","").lower(): print("forbidden feeding judgement",forbidden);sys.exit(1)
print("WCVP ingest contract QA OK")
