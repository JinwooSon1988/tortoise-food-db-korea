from pathlib import Path
import json,sys
d=Path(__file__).resolve().parents[1]/"data";e=[]
S={x["id"]:x for x in json.loads((d/"species.json").read_text(encoding="utf-8"))}
if S["sulcata"]["assessment_group"]==S["leopard"]["assessment_group"]:e.append("shared group")
if S["horsfieldii"]["assessment_group"]=="Mediterranean_Testudo":e.append("horsfield inherited")
A=json.loads((d/"assessments.json").read_text(encoding="utf-8"))
if any(x.get("species_group")=="African_grazer" for x in A):e.append("legacy group")
h=(d.parent/"index.html").read_text(encoding="utf-8")
if "for(const scope of scopes)" not in h:e.append("resolver missing")
print("PASS" if not e else "\n".join(e));sys.exit(bool(e))
