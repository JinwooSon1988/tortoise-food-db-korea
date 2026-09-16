from pathlib import Path
import json,re,html
ROOT=Path(__file__).resolve().parents[1]
CURATED=('mallow','sowthistle','clover')
for pid in CURATED:
 path=ROOT/'plant'/pid/'index.html'; text=path.read_text(encoding='utf-8')
 title=re.search(r'<title>(.*?)</title>',text,re.S).group(1)
 desc=re.search(r'<meta name="description" content="([^"]+)">',text).group(1)
 canonical=re.search(r'<link rel="canonical" href="([^"]+)">',text).group(1)
 if '<meta name="robots"' not in text:
  text=text.replace('<title>', '<meta name="robots" content="index,follow"><title>',1)
 if 'property="og:url"' not in text:
  tags=(f'<meta property="og:type" content="article"><meta property="og:locale" content="ko_KR">'
        f'<meta property="og:site_name" content="거북밥 DB Korea"><meta property="og:title" content="{html.escape(title,quote=True)}">'
        f'<meta property="og:description" content="{html.escape(desc,quote=True)}"><meta property="og:url" content="{canonical}">'
        f'<meta name="twitter:card" content="summary"><meta name="twitter:title" content="{html.escape(title,quote=True)}">'
        f'<meta name="twitter:description" content="{html.escape(desc,quote=True)}">')
  text=text.replace(f'<link rel="canonical" href="{canonical}">',f'<link rel="canonical" href="{canonical}">{tags}',1)
 m=re.search(r'<script type="application/ld\+json">(.*?)</script>',text,re.S)
 schema=json.loads(m.group(1)); schema['url']=canonical; schema['inLanguage']='ko'; schema['isPartOf']={'@type':'WebSite','name':'거북밥 DB Korea','url':'https://jinwooson1988.github.io/tortoise-food-db-korea/'}
 replacement='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False,separators=(',',':'))+'</script>'
 text=text[:m.start()]+replacement+text[m.end():]
 path.write_text(text,encoding='utf-8')
print('patched curated social metadata:',','.join(CURATED))