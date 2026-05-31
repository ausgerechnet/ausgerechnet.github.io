#!/usr/bin/env python3

import re
from pathlib import Path
from collections import defaultdict
import bibtexparser
from datetime import datetime
import os


# =========================
# CONFIG
# =========================

MASTER_BIB = Path("philipp-heinrich.bib")

PDF_DIR = Path("pdf")
PUB_DIR = Path("bib")
STYLESHEET = "../pheinrich.css"

MY_NAME = "Heinrich, Philipp"

OUTPUT_INDEX = Path("index.html")
OUTPUT_TALKS = Path("talks.html")

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

TODAY = datetime.now().strftime("%B %d, %Y")


# =========================
# LOAD BIBTEX
# =========================

def load_entries():
    with open(MASTER_BIB, encoding="utf-8") as f:
        return bibtexparser.load(f).entries


# =========================
# SAVE INDIVIDUAL BIB FILES
# =========================

def save_individual_bib(entries):
    PUB_DIR.mkdir(exist_ok=True)
    writer = bibtexparser.bwriter.BibTexWriter()

    for e in entries:

        # --- COPY entry so we don't mutate main data ---
        clean_entry = dict(e)

        # --- REMOVE PDF / file fields ---
        clean_entry.pop("pdf", None)
        clean_entry.pop("file", None)

        db = bibtexparser.bibdatabase.BibDatabase()
        db.entries = [clean_entry]

        out = PUB_DIR / f"{e['ID']}.bib"

        with open(out, "w", encoding="utf-8") as f:
            f.write(writer.write(db))


# =========================
# FORMATTER
# =========================

def formatter(entry):

    for key in list(entry.keys()):

        if isinstance(entry[key], str):
            entry[key] = re.sub(r"\n+", " ", entry[key]).strip()

        if key in ["title", "booktitle"] and entry.get(key):

            row = re.sub(r"[{}]", "", entry[key])
            words = row.split()

            row = " ".join([
                f"{{{w}}}" if any(c.isupper() for c in w) else w
                for w in words
            ])

            entry[key] = row

        if key == "pages" and entry.get(key):

            row = re.sub(r"\s*[-–]+\s*", "-", entry[key])
            row = re.sub("-", "–", row)
            entry[key] = row

        entry[key] = re.sub(r"[{}]", "", entry[key])

    # add links
    links = "["

    # bib
    links += '<a href="%s">bib</a>' % "/".join(["bib", entry['ID'] + ".bib"])

    # website
    if 'url' in entry.keys():
        links += ', <a href="%s">web</a>' % entry['url']

    # PDFs
    res = {
        'abstract': PDF_DIR / f"{entry['ID']}_abstract.pdf",
        'pdf': PDF_DIR / f"{entry['ID']}.pdf",
        'slides': PDF_DIR / f"{entry['ID']}_slides.pdf",
        'poster': PDF_DIR / f"{entry['ID']}_poster.pdf"
    }

    for key in ['abstract', 'pdf', 'slides', 'poster']:
        if os.path.isfile(res[key]):
            links += ', <a href="%s">%s</a>' % (res[key], key)

    links += "]"

    entry['links'] = links

    return entry


# =========================
# AUTHOR FORMATTER
# =========================

def author2html(author, special=[]):

    if not author:
        return ""

    author = author.replace(" and ", "; ")

    for s in special:
        author = re.sub(
            re.escape(s),
            f"<u>{s}</u>",
            author
        )

    return author


# =========================
# HTML ENTRY FORMATTERS
# =========================

def article2html(e):
    vol = ""

    if e.get("volume"):
        vol = f"<b>{e['volume']}</b>"

    if e.get("number"):
        vol += f"({e['number']})"

    parts = [
        author2html(e.get("author"), [MY_NAME]),
        f"({e.get('year','')}).",
        f"<b>{e.get('title','')}</b>.",
        f"<i>{e.get('journal','')}</i>",
        (vol + ":" if vol else ""),
        (e.get("pages", "") + "." if e.get("pages") else ""),
        e.get('links')
    ]

    return " ".join(p for p in parts if p)


def book2html(e):

    author = e.get("author") or e.get("editor") or ""

    parts = [
        author2html(author, [MY_NAME]),
        f"({e.get('year','')}).",
        f"<b>{e.get('title','')}</b>.",
        e.get("address", ""),
        ":",
        e.get("publisher", ""),
        e.get('links')
    ]

    return " ".join(p for p in parts if p)


def inproceedings2html(e):

    parts = [
        author2html(e.get("author"), [MY_NAME]),
        f"({e.get('year','')}).",
        f"<b>{e.get('title','')}</b>.",
        "In <i>" + e.get("booktitle", "") + "</i>,",
        ("pages " + e.get("pages") if e.get("pages") else ""),
        e.get("address", ""),
        e.get('links')
    ]

    return " ".join(p for p in parts if p)


def incollection2html(e):

    parts = [
        author2html(e.get("author"), [MY_NAME]),
        f"({e.get('year','')}).",
        f"<b>{e.get('title','')}</b>.",
        "In <i>" + e.get("booktitle", "") + "</i>,",
        ("edited by " + author2html(e.get("editor"), [MY_NAME]) if e.get("editor") else ""),
        ("pages " + e.get("pages") if e.get("pages") else ""),
        e.get("address", ""),
        e.get("publisher", ""),
        e.get('links')
    ]

    return " ".join(p for p in parts if p)


def misc2html(e):

    parts = [
        author2html(e.get("author"), [MY_NAME]),
        f"({e.get('note', e.get('year',''))}).",
        f"<b>{e.get('title','')}</b>.",
        f"<i>{e.get('howpublished','')}</i>.",
        e.get('links')
    ]

    return " ".join(parts)


# =========================
# DISPATCHER
# =========================

def entry2html(e):

    t = e.get("ENTRYTYPE", "").lower()

    if t == "article":
        return article2html(e)

    if t in ["book", "proceedings"]:
        return book2html(e)

    if t == "inproceedings":
        return inproceedings2html(e)

    if t == "incollection":
        return incollection2html(e)

    if t == "misc":
        return misc2html(e)

    return ""


# =========================
# ENRICH ENTRIES
# =========================

def parse_month(m):
    if not m:
        return 0

    m = str(m).strip().lower()

    if m.isdigit():
        return int(m)

    return MONTH_MAP.get(m[:3], 0)


def enrich(entries):

    for e in entries:

        e = formatter(e)

        key = e["ID"]

        pdf = PDF_DIR / f"{key}.pdf"
        e["pdf"] = pdf.as_posix()
        e["pdf_exists"] = pdf.exists()

        e["bib"] = f"pub/{key}.bib"

        # year
        try:
            e["_year"] = int(e.get("year", 0))
        except:
            e["_year"] = 0

        # month (NEW)
        e["_month"] = parse_month(e.get("month"))

        # HTML
        e["html"] = entry2html(e)

    return entries


# =========================
# GROUPING: INDEX
# =========================

def build_index(entries):

    groups = defaultdict(list)

    for e in entries:
        t = e["ENTRYTYPE"].lower()
        note = (e.get("note") or "").lower()

        if t == "article":
            groups["Journal Articles"].append(e)

        elif t == "inproceedings":
            if "sharedtask" in note:
                groups["Shared Tasks"].append(e)
            else:
                groups["Articles in Conference Proceedings"].append(e)

        elif t in ["book", "proceedings"]:
            groups["Edited Volumes"].append(e)

        elif t == "incollection":
            groups["Articles in Collections"].append(e)

    for k in groups:
        groups[k] = sorted(groups[k], key=lambda x: (x["_year"], x["_month"]), reverse=True)

    return groups


# =========================
# GROUPING: TALKS
# =========================

def build_talks(entries):

    lndw = []
    misc = []

    for e in entries:
        if e["ENTRYTYPE"].lower() != "misc":
            continue

        note = (e.get("howpublished") or "").lower()

        if "lndw" in note:
            e["DATE"] = e.get("note")
            lndw.append(e)
        else:
            misc.append(e)

    return {
        "„Lange Nacht der Wissenschaften“ in Erlangen": sorted(lndw, key=lambda x: (x["_year"], x["_month"]), reverse=True),
        "Conferences and Workshops": sorted(misc, key=lambda x: (x["_year"], x["_month"]), reverse=True),
    }


# =========================
# HTML RENDER
# =========================

def render_grouped(groups, title, stylesheet, preamble=None, today=TODAY):

    html = [
        "<!doctype html>",
        "<html lang='en'>",
        "<head>",
        "    <meta charset='utf-8'>",
        f"   <title>Philipp Heinrich — {title}</title>",
        "    <meta name='author' content='Philipp Heinrich'>",
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0, user-scalable=yes'>",
        f"   <link rel='stylesheet' href='{stylesheet}'>",
        "</head>",
        "<body>",

        "<header class='navigation'>",
        "<h1>Philipp Heinrich</h1>",
        "<nav>",
        "  <a href='../index.html'>home</a>",
        "  <a href='index.html'>publications</a>",
        "  <a href='../teaching.html'>teaching</a>",
        "  <a href='talks.html'>talks</a>",
        "</nav>",
        "</header>",

        f"<main><h2>{title}</h2>"
    ]

    if preamble:
        html.append(
            f'<p style="margin-left:5%; margin-right:5%;">{preamble}</p>'
        )

    for g, items in groups.items():
        html.append(f"<h3>{g}</h3><ul>")
        for e in items:
            html.append("<li>" + e["html"] + "</li>")
        html.append("</ul>")

    html += [
        "</main>",
        "<footer>",
        f"  last update: {today}",
        "</footer>",
        "</body>",
        "</html>"
    ]

    return "\n".join(html)


# =========================
# MAIN
# =========================

def render(entries):

    index_groups = build_index(entries)
    talk_groups = build_talks(entries)

    index_html = render_grouped(index_groups, "Publications", STYLESHEET, preamble="As is usual for the field of computational linguistics, most of my research is presented in the course of conferences and is published in the corresponding proceedings.")
    talks_html = render_grouped(talk_groups, "Talks and Presentations", STYLESHEET)

    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        f.write(index_html)

    with open(OUTPUT_TALKS, "w", encoding="utf-8") as f:
        f.write(talks_html)


def main():
    entries = load_entries()

    save_individual_bib(entries)

    entries = enrich(entries)

    render(entries)

    print(f"Processed {len(entries)} entries")


if __name__ == "__main__":

    main()
