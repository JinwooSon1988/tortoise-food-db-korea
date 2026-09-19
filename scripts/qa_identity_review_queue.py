#!/usr/bin/env python3
import json,pathlib,sys
p=pathlib.Path("data/reconciliation/wcvp_identity_review_queue.json")
if not p.exists(): sys.exit(0)
d=json.loads(p.read_text(encoding="utf-8")); errors=[]
if d.get("guardrail")!="Taxonomic synonym findings never alter feeding verdicts automatically.": errors.append("missing feeding/taxonomy separation guardrail")
for x in d.get("findings",[]):
 if x.get("action")!="identity_review_required": errors.append(x.get("plant_id","?")+": unsafe automatic action")
 if x.get("feeding_assessment_change")!="none": errors.append(x.get("plant_id","?")+": taxonomy changed feeding assessment")
if errors: print("\n".join(errors));sys.exit(1)
print("identity review queue QA OK")
