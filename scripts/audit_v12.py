from pathlib import Path
import re,sys,json
root=Path(__file__).resolve().parents[1]
html=(root/"index.html").read_text(encoding="utf-8")
errs=[]
required=["function uid()","function migrateMeals()","petId:$(\"mealPet\").value","crypto.randomUUID","cleanP","cleanM"]
for x in required:
    if x not in html: errs.append("missing "+x)
if "rows.push({date:$(\"mealDate\").value,petIndex:" in html: errs.append("new meals still use petIndex")
sw=(root/"sw.js").read_text(encoding="utf-8")
if 'self.addEventListener("activate"' not in sw: errs.append("service worker cleanup missing")
print("PASS" if not errs else "\\n".join(errs));sys.exit(bool(errs))
