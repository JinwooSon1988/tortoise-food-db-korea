from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]/'data'/'plants.json'
a=json.loads(p.read_text(encoding='utf-8'))
if not any(x.get('id')=='lambs_lettuce' for x in a):
    a.append(json.loads((p.parent/'master_69_lambs_lettuce.json').read_text(encoding='utf-8')))
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
