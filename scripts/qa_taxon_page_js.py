#!/usr/bin/env python3
"""Validate the actual browser JavaScript and catalog-to-detail routing before GitHub Pages deployment."""
import json,pathlib,re,subprocess,tempfile
html=pathlib.Path('taxon/index.html').read_text(encoding='utf-8')
scripts=re.findall(r'<script[^>]*>(.*?)</script>',html,re.DOTALL)
if not scripts:raise SystemExit('No inline scripts in taxon detail page')
with tempfile.TemporaryDirectory() as folder:
 for i,script in enumerate(scripts):
  target=pathlib.Path(folder)/f'taxon-{i}.js'
  target.write_text(script,encoding='utf-8')
  result=subprocess.run(['node','--check',str(target)],capture_output=True,text=True)
  if result.returncode:raise SystemExit('Invalid taxon JavaScript: '+result.stderr)
files=sorted(pathlib.Path('data/plant-catalog').glob('taxa-*.json'))
if len(files)!=40:raise SystemExit(f'Expected 40 taxon shards, found {len(files)}')
ids=set()
for file in files:
 shard=int(file.stem.split('-')[-1])
 for record in json.loads(file.read_text(encoding='utf-8')).get('records',[]):
  identifier=record.get('id','')
  if not identifier.startswith('gbif:') or not identifier[5:].isdigit():raise SystemExit(f'Bad ID in {file}: {identifier}')
  if int(identifier.split(':')[1])%40!=shard:raise SystemExit(f'Broken detail routing for {identifier}: {file}')
  if identifier in ids:raise SystemExit(f'Duplicate taxon ID: {identifier}')
  ids.add(identifier)
print('Taxon page JavaScript valid; shard routing valid for',len(ids),'plant records')
