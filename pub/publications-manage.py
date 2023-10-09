#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from glob import glob
from pandas import DataFrame
from collections import defaultdict
from datetime import date
from argparse import ArgumentParser

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter


# SET OPTIONS
parser = BibTexParser(common_strings=True)
parser.ignore_nonstandard_types = False
parser.homogenise_fields = True


# TODO: consistencize @misc (howpublished, address, type of presentation)
# TODO: consistencize @inproceedings (location / address)
# TODO: export / include in publications.html
# TODO: identify peer-reviewed abstracts


def formatter(entry):
    """ simple preprocessor to consistencize entries """

    for key in entry:

        if type(entry[key]) is str:

            # remove newlines from values
            value = re.sub("\n+", " ", entry[key])
            entry[key] = value

        if key == 'title' or key == 'booktitle':

            # capitalize words to avoid NATBIB "feature"
            row = re.sub("{|}", "", entry[key])
            row = row.split(" ")
            row = " ".join([
                "{" + r + "}" if (
                    any(x.isupper() for x in r)
                ) else r for r in row
            ])
            entry[key] = row

        if key == 'pages':
            row = re.sub(r"\s*[-–]+\s*", "-", entry[key])
            row = re.sub("-", "–", row)
            entry[key] = row

    return entry


def author2html(author, special=["Heinrich, Philipp", "Heinrich, P."]):
    """ format authors HTML-style """

    author = author.replace(" and ", "; ")
    for s in special:
        author = author.replace(s, "<u>" + s + "</u>")
    return author


def article2html(entry):
    """ HTML formatter for @article
    required: author, title, journal, year
    optional: volume, number, pages, month, note

    style: author (year). <b>title</b>. <i>journal</i> <b>volume</b>(issue)?: pages.
    """

    volume_number = "<b>" + entry['volume'] + "</b>"
    if "number" in entry.keys():
        volume_number += "(" + entry['number'] + ")"
    return " ".join([
        author2html(entry['author']),
        "(" + entry['year'] + ").",
        "<b>" + entry['title'] + "</b>.",
        "<i>" + entry['journal'] + "</i>",
        volume_number + ":",
        entry['pages'] + "."
    ])


def book2html(entry):
    """ HTML formatter for @book and @proceedings

    @book
    required: author or editor, title, publisher, year
    optional: volume or number, series, address, edition, month, note

    @proceedings
    required: title, year
    optional: editor, volume or number, series, address, publisher,
              note, month, organization

    style:  author / editor (year). <b>title</b>. address: publisher.
    """

    if "author" in entry.keys():
        author = author2html(entry['author'])
    elif "editor" in entry.keys():
        author = author2html(entry['editor'])

    return " ".join([
        author,
        "(" + entry['year'] + ").",
        "<b>" + entry['title'] + "</b>.",
        entry['address'] + ":",
        entry['publisher'] + "."
    ])


def inproceedings2html(entry):
    """ HTML formatter for @inproceedings
    required: author, title, booktitle, year
    optional: editor, volume or number, series, pages, address, month,
              organization, publisher, note

    style: author (year). <b>title</b>. 'In' <i>booktitle</i>, 'pages' pages, address.
    """

    return " ".join([
        author2html(entry['author']),
        "(" + entry['year'] + ").",
        "<b>" + entry['title'] + "</b>.",
        "In <i>" + entry['booktitle'] + "</i>,",
        "pages " + entry['pages'] + ",",
        entry['address'] + "."
    ])


def incollection2html(entry):
    """ HTML formatter for @incollection
    required: author, title, booktitle, publisher, year
    optional: editor, volume or number, series, type, chapter,
              pages, address, edition, month, note

    style: author (year). <b>title</b>. 'In' <i>booktitle</i>,
           'edited by' editor, 'pages' pages, address: publisher.
    """

    return " ".join([
        author2html(entry['author']),
        "(" + entry['year'] + ").",
        "<b>" + entry['title'] + "</b>.",
        "In <i>" + entry['booktitle'] + "</i>,",
        "edited by " + author2html(entry['editor']) + ",",
        "pages " + entry['pages'] + ",",
        entry['address'] + ":",
        entry['publisher'] + "."
    ])


def misc2html(entry):
    """ HTML formatter for @misc
    required: none
    optional: author, title, howpublished, month, year, note

    style: author (month, year). <b>title</b>. <i>howpublished</i>.
    """

    return " ".join([
        author2html(entry['author']),
        "(" + entry['year'] + ").",
        "<b>" + entry['title'] + "</b>.",
        "<i>" + entry['howpublished'] + "</i>."
    ])


def bibtex2html(entry, pdf_dir):
    """ converts an entry to HTML """

    out = None

    try:
        # Journal Articles (@article)
        if entry['ENTRYTYPE'] == 'article':
            out = article2html(entry)

        # Edited Volumes (@book or @proceedings)
        elif entry['ENTRYTYPE'] == 'book' or entry['ENTRYTYPE'] == 'proceedings':
            out = book2html(entry)

        # Articles in Conference Proceedings / SharedTasks (@inproceedings)
        elif entry['ENTRYTYPE'] == 'inproceedings':
            out = inproceedings2html(entry)

        # Articles in Collections (@incollection)
        elif entry['ENTRYTYPE'] == 'incollection':
            out = incollection2html(entry)

        # Talks and Presentations (@misc)
        elif entry['ENTRYTYPE'] == 'misc':
            out = misc2html(entry)

        else:
            raise NotImplementedError(
                "ENTRYTYPE %s not supported" % entry['ENTRYTYPE']
            )

    except KeyError:
        print(entry)
        raise NotImplementedError("can't deal with this")

    # remove capitalizers
    out = re.sub("{|}", "", out)

    # links ############################
    out += " ["

    # bib
    out += '<a href="%s">bib</a>' % "/".join(["bib", entry['ID'] + ".bib"])

    # website
    if 'url' in entry.keys():
        out += ', <a href="%s">web</a>' % entry['url']

    # PDFs
    res = {
        'abstract': pdf_dir + entry['ID'] + "_abstract.pdf",
        'pdf': pdf_dir + entry['ID'] + ".pdf",
        'slides': pdf_dir + entry['ID'] + "_slides.pdf",
        'poster': pdf_dir + entry['ID'] + "_poster.pdf"
    }

    for key in ['abstract', 'pdf', 'slides', 'poster']:
        if os.path.isfile(res[key]):
            out += ', <a href="%s">%s</a>' % (res[key], key)

    out += "]\n"

    # unescape stuff ###################
    out = out.replace("``", "&ldquo;")
    out = out.replace("''", "&rdquo;")
    out = out.replace(r"\_", "_")
    out = out.replace(r"\&", "&")

    return out


def read_many_bibs(paths_in, consistencize=True):

    # READ many bibs, convert to str
    paths_in.sort()
    txt_list = str()
    for p in paths_in:
        with open(p, "rt", encoding='utf-8') as f:
            try:
                txt_list += f.read() + "\n"
            except UnicodeDecodeError:
                print(p)

    # read all bib strings
    db = bibtexparser.loads(txt_list, parser)
    # for left, right in zip(paths_in, db.entries):
    #     print(left, right['ID'])
    assert len(db.entries) == len(paths_in)

    # TRANSFORM
    if consistencize:

        entries = list()
        for entry in db.entries:
            # don't append comments
            if entry['ENTRYTYPE'] != "comment":
                entries.append(formatter(entry))

        # new database
        db = BibDatabase()
        db.entries = entries

    return db


def order_db(db, order="ENTRYTYPE"):

    col = defaultdict(BibDatabase)
    for entry in db.entries:

        if order == "ENTRYTYPE":
            # special case: SharedTasks
            if "note" in entry.keys() and re.search(
                    r"shared\s?task", entry['note'].lower()
            ):
                col['sharedtask'].entries.append(entry)
            else:
                col[entry['ENTRYTYPE']].entries.append(entry)

        if order == 'date':
            if 'date' in entry.keys():
                date = entry['date']
            else:
                date = entry['year']
            col[date].entries.append(entry)

    return col


# WRITE ########################################################################

def main(paths_in, pdf_dir, path_tsv, path_bib, path_html):

    db = read_many_bibs(paths_in)

    # convert to .tsv
    df = DataFrame(db.entries)
    df.to_csv(path_tsv, sep="\t")

    # convert to .bib
    writer = BibTexWriter()
    db_ordered = order_db(db)
    with open(path_bib, 'wt') as bibfile:
        for key in sorted(db_ordered.keys()):
            bibfile.write("%" * 60 + "\n% " + key + "\n" + "%" * 60 + "\n")
            db_ordered_dates = order_db(db_ordered[key], 'date')
            for key2 in sorted(db_ordered_dates.keys(), reverse=True):
                bibfile.write(writer.write(db_ordered_dates[key2]))

    # convert to .html
    types = {
        "article": 'Journal Articles',
        "book": 'Edited Volumes',
        "proceedings": 'Edited Conference Proceedings',
        "inproceedings": 'Articles in Conference Proceedings',
        "incollection": 'Articles in Collections',
        "sharedtask": 'Shared Tasks',
        "misc": 'Talks and Presentations'
    }
    # check if all keys are taken care of
    if len(set(db_ordered.keys()).union(set(types.keys()))) != len(types.keys()):
        raise ValueError
    # write
    with open(path_html, 'wt') as htmlfile:
        htmlfile.write("<html>\n")
        for key in types.keys():
            htmlfile.write("<h3>" + types[key] + "</h3>\n")
            db_ordered_dates = order_db(db_ordered[key], 'date')
            htmlfile.write("<ul>\n")
            for key2 in sorted(db_ordered_dates.keys(), reverse=True):
                for bib in db_ordered_dates[key2].entries:
                    htmlfile.write("<li> " + bibtex2html(bib, pdf_dir))
            htmlfile.write("</ul>\n")
        htmlfile.write("<footer>\n")
        htmlfile.write("last update: " + date.today().strftime("%B %d, %Y") + "\n")
        htmlfile.write("</footer>\n")
        htmlfile.write("</html>")


if __name__ == '__main__':

    argparser = ArgumentParser()
    argparser.add_argument("--glob_bib",
                           default="bib/*.bib",
                           help="path to *.bib")
    argparser.add_argument("--pdf_dir",
                           default="pdf/",
                           help="directory of PDFs (must end on '/')")
    args = argparser.parse_args()

    # paths out
    path_tsv = "publications-pheinrich.tsv"
    path_bib = "publications-pheinrich.bib"
    path_html = "publications-pheinrich.html"

    main(
        glob(args.glob_bib),
        args.pdf_dir,
        path_tsv,
        path_bib,
        path_html
    )
