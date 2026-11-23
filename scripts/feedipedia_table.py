#!/usr/bin/env python3
"""Row-based reader for Feedipedia composition tables.

Every value is read from the cells of its own <tr>: label, unit, mean, SD, min, max, Nb and the calculated-value marker (*).
Column positions come from each section's header row ("Main analysis | Unit | Avg | SD | Min | Max | Nb"), colspan is
expanded so positions stay aligned, and a row that is part of a rowspan block is flagged instead of guessed.

This replaces the flattened-text regex formerly used in verify_nutrition_reference_sources_v1.parse_feedipedia, which let a
row with a blank Nb take the Nb (and swallow the whole line) of the next row.
"""
import html
import re

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
UNITS = ("% as fed", "% DM", "g/kg DM", "mg/kg DM", "MJ/kg DM", "kcal/kg DM", "%", "h-1")
DEFAULT_COLUMNS = {"label": 0, "unit": 1, "avg": 2, "sd": 3, "min": 4, "max": 5, "nb": 6}


def _text(cell):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"(?s)<[^>]+>", " ", cell)).replace("\xa0", " ")).strip()


def _cells(tr):
    """Cells of one row, with colspan expanded; returns (texts, has_rowspan)."""
    out, rowspan = [], False
    for attrs, body in re.findall(r"(?s)<t[dh]([^>]*)>(.*?)</t[dh]>", tr):
        span = re.search(r'colspan\s*=\s*"?(\d+)', attrs)
        if re.search(r'rowspan\s*=\s*"?([2-9]|\d{2,})', attrs):
            rowspan = True
        out.append(_text(body))
        out.extend([""] * (int(span.group(1)) - 1 if span else 0))
    return out, rowspan


def _num(s):
    return float(s) if s and NUMBER.fullmatch(s) else None


def parse_rows(page):
    """All composition rows in page order, each read only from its own cells."""
    rows, columns, section, table = [], dict(DEFAULT_COLUMNS), None, -1
    for tm in re.finditer(r"(?s)<table[^>]*>(.*?)</table>", page):
        tbody = tm.group(1)
        table += 1
        columns, section = dict(DEFAULT_COLUMNS), None
        heads = [_text(h) for h in re.findall(r"(?s)<(?:h[1-6]|strong|a)[^>]*>(.*?)</(?:h[1-6]|strong|a)>", page[max(0, tm.start() - 2500):tm.start()])]
        heading = next((h for h in reversed(heads) if h), None)
        for i, tr in enumerate(re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", tbody)):
            cells, rowspan = _cells(tr)
            if len(cells) >= 2 and cells[1] == "Unit":
                section = cells[0]
                columns = {"label": 0, "unit": 1}
                for j, c in enumerate(cells):
                    key = {"Avg": "avg", "SD": "sd", "Min": "min", "Max": "max", "Nb": "nb"}.get(c)
                    if key:
                        columns[key] = j
                continue
            if section is None or len(cells) < 3:
                continue
            get = lambda k: cells[columns[k]] if k in columns and columns[k] < len(cells) else ""  # noqa: E731
            avg = _num(get("avg"))
            if avg is None or not get("label") or get("unit") not in UNITS:
                continue
            nb_raw = get("nb")
            after = cells[columns["nb"] + 1:] if "nb" in columns else []
            rows.append({"table": table, "table_heading": heading, "row": i, "section": section, "label": get("label"), "unit": get("unit"), "avg": avg,
                         "sd": _num(get("sd")), "min": _num(get("min")), "max": _num(get("max")),
                         "nb_raw": nb_raw, "nb": int(nb_raw) if re.fullmatch(r"\d+", nb_raw or "") else None,
                         "calculated": "*" in after or nb_raw == "*", "rowspan_in_row": rowspan,
                         "cell_count": len(cells)})
    return rows


def title(page):
    m = re.search(r'property="dc:title" content="([^"]+)"', page)
    return html.unescape(m.group(1)).strip() if m else None


ALIASES = {"neutral detergent fibre": ["ndf"], "acid detergent fibre": ["adf"], "ndf": ["neutral detergent fibre"], "adf": ["acid detergent fibre"],
           "water-soluble carbohydrates": ["water soluble carbohydrates"], "water soluble carbohydrates": ["water-soluble carbohydrates"]}


def find(rows, label, unit, heading_word=None):
    """Rows with this label and unit. More than one means the page holds several tables; heading_word (e.g. 'fresh') keeps
    only the table whose heading contains it, and still returns several rows if that does not single one out."""
    names = {label.lower(), *ALIASES.get(label.lower(), [])}
    hits = [r for r in rows if r["label"].lower() in names and r["unit"] == unit]
    if len(hits) > 1 and heading_word:
        narrowed = [r for r in hits if heading_word.lower() in (r["table_heading"] or "").lower()]
        if narrowed:
            return narrowed
    return hits


def legacy_title(page):
    """The text the former parser returned as the title (the line after the donation note, before 'Main analysis').
    Kept unchanged so that rebuilt research files keep the same table_note_on_page values."""
    t = re.sub(r"\s*\|\s*(\|\s*)*", "|", html.unescape(re.sub(r"<[^>]+>", "|", page)))
    m = re.search(r"Would you consider donating\?.*?\|([^|]+)\|Main analysis", t, re.S)
    return m.group(1).strip() if m else None


def legacy(page):
    """Same return shape as the former parse_feedipedia: ({(label_lower, unit_lower): (avg, nb)}, title).
    nb is '*' for a calculated value, an int when the row prints one, and None when the row's Nb cell is blank.
    A row inside a rowspan block is left out rather than guessed."""
    out = {}
    for r in parse_rows(page):
        if r["rowspan_in_row"]:
            continue
        nb = "*" if r["calculated"] else r["nb"]
        out.setdefault((r["label"].lower(), r["unit"].lower()), (r["avg"], nb))
    return out, legacy_title(page)
