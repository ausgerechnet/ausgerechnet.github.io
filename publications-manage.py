import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from glob import glob
from pandas import DataFrame
import re

# READ #########################################################################

parser = BibTexParser(common_strings=True)
parser.ignore_nonstandard_types = False
parser.homogenise_fields = True

paths_in = glob("bib/*.bib")
paths_in.sort()

f_list = str()
for p in paths_in:
    with open(p, "rt") as f:
        f_list += f.read() + "\n"

db = bibtexparser.loads(f_list, parser)


# TRANSFORM ####################################################################

new_entries = list()
for entry in db.entries:

    for key in entry:

        if type(entry[key]) is str:

            # remove newlines from values
            value = re.sub("\n+", " ", entry[key])
            entry[key] = value

        if key == 'title' or key == 'booktitle':

            # capitalize words to avoid NATBIB "feature"
            row = entry[key].split(" ")
            row = " ".join([
                "{" + r + "}" if (
                    any(x.isupper() for x in r) and not r.startswith("{")
                ) else r for r in row
            ])
            entry[key] = row

    # don't append comments
    if entry['ENTRYTYPE'] != "comment":
        new_entries.append(entry)


# WRITE ########################################################################
db = BibDatabase()
db.entries = new_entries
writer = BibTexWriter()
with open('publications-pheinrich.bib', 'w') as bibfile:
    bibfile.write(writer.write(db))

# convert to df
df = DataFrame(db.entries)
df.to_csv("publications-pheinrich.tsv", sep="\t")
