"""GitHub Pages 배포용 정적 파일과 내부 연결을 검사한다."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://jinwooson1988.github.io/tortoise-food-db-korea"
errors = []


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for key in ("href", "src"):
            if key in values:
                self.refs.append((tag, key, values[key]))


def target_for(page, ref):
    path = urlsplit(ref).path
    if not path or ref.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    if ref.startswith(("http://", "https://", "//")):
        return None
    target = (page.parent / path).resolve() if not path.startswith("/") else (ROOT / path[1:]).resolve()
    return target / "index.html" if target.is_dir() else target


html_files = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/index.html")) + sorted(ROOT.glob("plant/*/index.html"))
for page in html_files:
    parser = References()
    parser.feed(page.read_text(encoding="utf-8"))
    for _, _, ref in parser.refs:
        target = target_for(page, ref)
        if target is not None and (ROOT not in target.parents or not target.exists()):
            errors.append(f"{page.relative_to(ROOT)}: broken reference {ref}")

for path in ROOT.rglob("*.json"):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")

plants = json.loads((ROOT / "data/plants.json").read_text(encoding="utf-8"))
coverage = json.loads((ROOT / "data/coverage.json").read_text(encoding="utf-8"))
plant_ids = {plant["id"] for plant in plants}
page_ids = {path.parent.name for path in ROOT.glob("plant/*/index.html")}
expected_master_count = coverage.get("plant_master_count")
if not isinstance(expected_master_count, int) or expected_master_count < 1:
    errors.append("coverage.json: plant_master_count must be a positive integer")
elif len(plants) != expected_master_count:
    errors.append(f"plant master count is {len(plants)}, coverage declares {expected_master_count}")
if plant_ids != page_ids:
    errors.append(f"plant page mismatch: missing={sorted(plant_ids-page_ids)}, extra={sorted(page_ids-plant_ids)}")

for plant_id in plant_ids:
    text = (ROOT / "plant" / plant_id / "index.html").read_text(encoding="utf-8")
    canonical = f'<link rel="canonical" href="{SITE_URL}/plant/{plant_id}/">'
    if canonical not in text:
        errors.append(f"plant/{plant_id}/index.html: incorrect canonical URL")

for route in ("index.html", "profile/index.html", "meal/index.html", "weekly/index.html", "settings/index.html"):
    if not (ROOT / route).is_file():
        errors.append(f"missing application page: {route}")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
expected_urls = {f"{SITE_URL}/plant/{plant_id}/" for plant_id in plant_ids}
missing_urls = sorted(url for url in expected_urls if f"<loc>{url}</loc>" not in sitemap)
if missing_urls:
    errors.append(f"sitemap is missing {len(missing_urls)} plant URLs")

for required in ("manifest.webmanifest", "sw.js", "offline.html", "404.html"):
    if not (ROOT / required).is_file():
        errors.append(f"missing deployment file: {required}")

placeholder_hits = []
for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts:
        try:
            if "YOUR-DOMAIN" + ".example" in path.read_text(encoding="utf-8"):
                placeholder_hits.append(str(path.relative_to(ROOT)))
        except UnicodeDecodeError:
            pass
if placeholder_hits:
    errors.append(f"deployment placeholder remains in: {', '.join(placeholder_hits)}")

if errors:
    print("FAIL")
    print("\n".join(f"- {error}" for error in errors))
    raise SystemExit(1)
print(f"PASS: {len(html_files)} HTML files, {len(plants)} plant pages, JSON and relative links verified")