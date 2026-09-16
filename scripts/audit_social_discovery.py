import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base='https://jinwooson1988.github.io/tortoise-food-db-korea/'
plants=json.loads((root/'data/plants.json').read_text(encoding='utf-8'))
def one(text,pattern):
 m=re.search(pattern,text,re.I|re.S); assert m,pattern; return m.group(1)
def audit(path,url,plant=None):
 text=path.read_text(encoding='utf-8')
 assert one(text,r'<meta name="robots" content="([^"]+)">')=='index,follow'
 canonical=one(text,r'<link rel="canonical" href="([^"]+)">'); assert canonical==url
 assert one(text,r'<meta property="og:url" content="([^"]+)">')==url
 title=one(text,r'<title>(.*?)</title>')
 assert one(text,r'<meta property="og:title" content="([^"]+)">')==title
 desc=one(text,r'<meta name="description" content="([^"]+)">'); assert len(desc)>=20
 og_desc=one(text,r'<meta property="og:description" content="([^"]+)">'); assert len(og_desc)>=20
 assert one(text,r'<meta name="twitter:title" content="([^"]+)">')==title
 twitter_desc=one(text,r'<meta name="twitter:description" content="([^"]+)">'); assert len(twitter_desc)>=20
 schema=json.loads(one(text,r'<script type="application/ld\+json">(.*?)</script>'))
 assert schema['url']==url
 assert schema.get('inLanguage','ko')=='ko'
 if plant:
  assert schema['@type']=='WebPage' and schema['isPartOf']['name']=='거북밥 DB Korea'
 else:
  assert schema['@type']=='WebSite' and '69종' in title and '69종' in desc
audit(root/'index.html',base)
for p in plants:
 audit(root/'plant'/p['id']/'index.html',f"{base}plant/{p['id']}/",p)
print('social discovery audit: PASS',len(plants),'plant pages + home')