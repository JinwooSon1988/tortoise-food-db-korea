#!/usr/bin/env python3
"""Regression tests for scripts/feedipedia_table.py and the shared parse_feedipedia that now uses it. Offline; exits 1 on failure.

The fixtures are synthetic tables built like Feedipedia's: blank Nb, Nb 0 and 1, calculated values with and without Nb,
colspan, rowspan, a shuffled header, two tables holding the same nutrient, entity-encoded text, and the 11865 layout that
exposed the former neighbouring-row bug.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, ["x"]
    spec.loader.exec_module(m)
    sys.argv = argv
    return m


ft = load("feedipedia_table", HERE / "feedipedia_table.py")
shared = load("verify_ref", HERE / "verify_nutrition_reference_sources_v1.py")

HEAD = '<tr class="tableheader"><td>%s</td><td>Unit</td><td>Avg</td><td>SD</td><td>Min</td><td>Max</td><td>Nb</td><td> </td></tr>'


def row(label, unit, avg, sd="", mn="", mx="", nb="", star=""):
    return "<tr><td><a href=\"1\">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (label, unit, avg, sd, mn, mx, nb, star)


def page(*tables, title="Test feed, aerial part, fresh"):
    body = "".join("<table><tbody>%s</tbody></table>" % t for t in tables)
    return ('<span property="dc:title" content="%s"></span><p>Would you consider donating? Donate.</p><p>%s</p>%s' % (title, title, body))


FAILS = []


def check(name, cond):
    if not cond:
        FAILS.append(name)
    print("%-62s %s" % (name, "ok" if cond else "FAIL"))


# 1. the 11865 layout: blank-Nb rows followed by rows with Nb
p11865 = page(HEAD % "Main analysis" + row("Dry matter", "% as fed", "20.9") + row("Crude protein", "% DM", "21.8", "2.7", "13.4", "31.8", "165")
              + row("Crude fibre", "% DM", "21.9", star="*") + row("Neutral detergent fibre", "% DM", "37.5", "5.8", "22.4", "52.4", "93", "*")
              + "<tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"
              + HEAD % "Minerals" + row("Calcium", "g/kg DM", "16.1") + row("Phosphorus", "g/kg DM", "3.1", "0.5", "2.3", "4.4", "72"))
rows = ft.parse_rows(p11865)
by = {(r["label"], r["unit"]): r for r in rows}
check("blank Nb stays blank (dry matter)", by[("Dry matter", "% as fed")]["nb"] is None and by[("Dry matter", "% as fed")]["nb_raw"] == "")
check("next row keeps its own Nb (crude protein 165)", by[("Crude protein", "% DM")]["nb"] == 165)
check("next row is not swallowed (crude protein present)", ("Crude protein", "% DM") in by)
check("blank Nb in a new section (calcium)", by[("Calcium", "g/kg DM")]["nb"] is None)
check("phosphorus keeps Nb 72", by[("Phosphorus", "g/kg DM")]["nb"] == 72)
check("calculated without Nb is marked calculated", by[("Crude fibre", "% DM")]["calculated"] and by[("Crude fibre", "% DM")]["nb"] is None)
check("calculated with Nb keeps Nb and marker", by[("Neutral detergent fibre", "% DM")]["calculated"] and by[("Neutral detergent fibre", "% DM")]["nb"] == 93)
leg, _ = shared.parse_feedipedia(p11865)
check("shared parser: dry matter Nb is None, not 165", leg[("dry matter", "% as fed")] == (20.9, None))
check("shared parser: calcium Nb is None, not 72", leg[("calcium", "g/kg dm")] == (16.1, None))
check("shared parser: crude protein (165) is returned", leg[("crude protein", "% dm")] == (21.8, 165))
check("shared parser: calculated value returns '*'", leg[("crude fibre", "% dm")] == (21.9, "*") and leg[("neutral detergent fibre", "% dm")] == (37.5, "*"))

# 2. Nb 0 and 1, and Nb followed by an empty marker cell
p01 = page(HEAD % "Main analysis" + row("Ash", "% DM", "9.0", nb="0") + row("Lignin", "% DM", "4.5", nb="1") + row("Starch", "% DM", "2.0", "0.1", "1.9", "2.1", "2"))
r01 = {r["label"]: r for r in ft.parse_rows(p01)}
check("Nb 0 is read as 0, not blank", r01["Ash"]["nb"] == 0)
check("Nb 1 is read as 1", r01["Lignin"]["nb"] == 1)
check("Nb 2 with SD/min/max", r01["Starch"]["nb"] == 2 and r01["Starch"]["sd"] == 0.1 and not r01["Starch"]["calculated"])

# 3. colspan keeps columns aligned
pcol = page(HEAD % "Main analysis" + '<tr><td>Ether extract</td><td>% DM</td><td>3.3</td><td colspan="3"></td><td>7</td><td> </td></tr>'
            + '<tr><td>Ash</td><td>% DM</td><td>12.7</td><td colspan="4"></td><td> </td></tr>')
rc = {r["label"]: r for r in ft.parse_rows(pcol)}
check("colspan over SD-Max: Nb read from the Nb column", rc["Ether extract"]["nb"] == 7)
check("colspan over SD-Nb: Nb blank, not taken from elsewhere", rc["Ash"]["nb"] is None)

# 4. rowspan rows are flagged and left out of the shared output
prow = page(HEAD % "Main analysis" + '<tr><td>Sodium</td><td>g/kg DM</td><td>2.2</td><td></td><td></td><td></td><td rowspan="2">33</td><td></td></tr>'
            + row("Potassium", "g/kg DM", "15.8", "2.8", "12", "19", "5"))
rr = {r["label"]: r for r in ft.parse_rows(prow)}
check("rowspan row is flagged", rr["Sodium"]["rowspan_in_row"])
legr, _ = shared.parse_feedipedia(prow)
check("shared parser leaves a rowspan row out", ("sodium", "g/kg dm") not in legr and legr[("potassium", "g/kg dm")] == (15.8, 5))

# 5. header order taken from the header row
shuffled = ('<tr class="tableheader"><td>Main analysis</td><td>Unit</td><td>Avg</td><td>Nb</td><td>SD</td><td>Min</td><td>Max</td></tr>'
            '<tr><td>Dry matter</td><td>% as fed</td><td>88.0</td><td>16</td><td>3.0</td><td>84.6</td><td>92.8</td></tr>')
rs = ft.parse_rows(page(shuffled))
check("columns follow the header row", rs[0]["nb"] == 16 and rs[0]["sd"] == 3.0 and rs[0]["max"] == 92.8)

# 6. two tables with the same nutrient are reported as ambiguous
pdup = page(HEAD % "Main analysis" + row("Crude protein", "% DM", "19.3", nb="4"), HEAD % "Main analysis" + row("Crude protein", "% DM", "22.0", nb="9"))
check("same label in two tables gives two candidates", len(ft.find(ft.parse_rows(pdup), "Crude protein", "% DM")) == 2)

# 7. entities, links and non-numeric means
pent = page(HEAD % "Main analysis" + "<tr><td><a href=\"8331\">Dry&nbsp;matter</a></td><td>% as fed</td><td>88.0</td><td></td><td></td><td></td><td>3</td><td></td></tr>"
            + row("Gross energy", "MJ/kg DM", "-") + row("Tannins", "g/kg DM", "n.d."))
re_ = ft.parse_rows(pent)
check("entity-encoded label read", re_[0]["label"] == "Dry matter" and re_[0]["nb"] == 3)
check("non-numeric means are not read as values", len(re_) == 1)

# 8. title and the former title behaviour
check("dc:title is read", ft.title(p11865) == "Test feed, aerial part, fresh")

# 9. the keep rule of the unit 1, 2 and 5 builders: a value whose own row prints no Nb is never kept, even when the next row has one
b1 = load("build_v1", HERE / "build_global_plant_evidence_research_v1.py")
kept = {k for k, (avg, nb) in leg.items() if b1.has_printed_sample_count(nb)}
check("keep rule: blank-Nb rows (dry matter, calcium) are not kept", not kept & {("dry matter", "% as fed"), ("calcium", "g/kg dm")})
check("keep rule: calculated values ('*') are not kept", not kept & {("crude fibre", "% dm"), ("neutral detergent fibre", "% dm")})
check("keep rule: rows with their own Nb are kept", {("crude protein", "% dm"), ("phosphorus", "g/kg dm")} <= kept)
check("keep rule: Nb 0 is a printed count, None/''/'*'/True are not",
      b1.has_printed_sample_count(0) and not any(b1.has_printed_sample_count(x) for x in (None, "", "*", "6", True)))
# the 12645 layout: sodium's Nb cell is blank and the zinc row below prints mean 33; the former parser stored 33 as sodium's Nb
p12645 = page(HEAD % "Minerals" + row("Potassium", "g/kg DM", "20.0", "1.0", "18.5", "21.4", "6") + row("Sodium", "g/kg DM", "2.2")
              + row("Zinc", "mg/kg DM", "33", "8", "22", "41", "5"))
l12645, _ = shared.parse_feedipedia(p12645)
check("12645 layout: sodium Nb stays blank (not zinc's mean 33)", l12645[("sodium", "g/kg dm")] == (2.2, None) and not b1.has_printed_sample_count(l12645[("sodium", "g/kg dm")][1]))

print("%d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
