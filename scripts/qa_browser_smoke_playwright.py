#!/usr/bin/env python3
"""Browser smoke tests for generated pages; no network or account required."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/"
def url(path):
    return BASE + path
# A catalog entry (no feeding grade) for the search and detail checks.
CAT = json.loads((ROOT / "data/plant-catalog/search.json").read_text(encoding="utf-8"))["rows"]
SAMPLE = next(r for r in CAT if r[5]) if any(r[5] for r in CAT) else CAT[0]

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for width, height in ((1440, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url("index.html"), wait_until="load")
        assert page.locator("#searchInput").is_visible(), f"search missing at {width}px"
        page.locator("#searchInput").fill("민들레")
        assert page.locator("#searchInput").input_value() == "민들레"
        assert not errors, f"home JS errors at {width}px: {errors}"
        page.goto(url("plant/mustard/index.html"), wait_until="load")
        assert page.locator(".decision .verdictbadge").inner_text().strip() == "C"
        assert page.locator(".decision .verdictlabel").is_visible()
        assert page.locator('a[href="#evidence"]').count() > 0
        assert page.locator("#evidence").count() > 0
        assert not errors, f"JS errors at {width}px: {errors}"
        page.goto(url("all-plants/index.html"), wait_until="load")
        grade_buttons = page.locator(".gradelegend button")
        assert grade_buttons.count() == 6, "expected A/B/C/D/hold/unassessed filters"
        if width <= 639:
            layout = page.locator(".gradelegend").evaluate("(el) => getComputedStyle(el).display")
            assert layout == "grid", f"mobile grade legend should use grid, got {layout}"
            a = grade_buttons.nth(0).bounding_box()
            b = grade_buttons.nth(1).bounding_box()
            c = grade_buttons.nth(2).bounding_box()
            assert a and b and c
            assert abs(a["y"] - b["y"]) < 5 and c["y"] > a["y"] + 10, "mobile grades should form two columns"
            for i in range(grade_buttons.count()):
                box = grade_buttons.nth(i).bounding_box()
                assert box and box["x"] >= -1 and box["x"] + box["width"] <= width + 1, f"grade {i} clipped on mobile"
        assert not errors, f"JS errors at {width}px: {errors}"
        page.locator("#q").fill(SAMPLE[1])
        link = page.locator('a[href^="../taxon/?id=' + SAMPLE[0].replace(":", "%3A") + '"]:visible').first
        link.wait_for(timeout=10000)
        link.click()
        page.wait_for_url("**/taxon/**")
        page.locator("h1").wait_for(timeout=10000)
        assert SAMPLE[1] in page.locator(".sub").inner_text(), "taxon detail shows another plant"
        assert "급여 안전성 미확정" in page.locator(".status").inner_text()
        assert page.locator(".verdictbadge").count() == 0, "catalog entry must not show a grade badge"
        page.goto(url("taxon/?id=" + SAMPLE[0] + "&lang=en"), wait_until="load")
        page.locator(".status").wait_for(timeout=10000)
        assert "Feeding safety not established" in page.locator(".status").inner_text()
        page.goto(url("index.html"), wait_until="load")
        page.locator("#searchInput").fill(SAMPLE[1])
        page.locator("#taxonomy-home-results a").first.wait_for(timeout=10000)
        assert not errors, f"JS errors at {width}px: {errors}"
        print(f"PASS browser smoke: {width}x{height}, home/search/detail/all-plants/taxon")
        page.close()
    browser.close()
server.shutdown()
