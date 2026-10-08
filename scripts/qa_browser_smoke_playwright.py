#!/usr/bin/env python3
"""Browser smoke tests for generated pages; no network or account required."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
handler = partial(SimpleHTTPRequestHandler, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/"
def url(path):
    return BASE + path

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
        assert grade_buttons.count() == 5, "expected A/B/C/D/hold filters"
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
        print(f"PASS browser smoke: {width}x{height}, home/search/detail/all-plants")
        page.close()
    browser.close()
server.shutdown()
