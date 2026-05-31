# publications

## database

- use [JabRef](https://www.jabref.org/) for managing [philipp-heinrich.bib](philipp-heinrich.bib)

## workflow for adding new publications

1. include bibtex in database
   - make sure KEY is unique and consistent
2. optionally include PDF at pdf/KEY.pdf
3. run [update-publications.py](update-publications.py), which
   - links all pdf/KEY*.pdf
   - exports all bib/KEY.bib
   - updates index.html
     + Journal Articles (article)
     + Articles in Conference Proceedings (inproceedings)
     + Edited Volumes (book, proceedings)
     + Articles in Collections (incollection)
     + Shared Tasks (inproceedings + note contains "SharedTask")
   - updates talks.html
     + „Lange Nacht der Wissenschaften“ in Erlangen (misc + howpublished contains "LNDW")
     + Conferences and Workshops (other misc)
