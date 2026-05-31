# publications

## database

- use [JabRef](https://www.jabref.org/) for managing [philipp-heinrich.bib](philipp-heinrich.bib)

## workflow for adding new publications

1. include bibtex in database (make sure KEY is consistent)
2. (optional) include PDF at pdf/KEY.pdf
3. run publication-manage.py, which
   - links all entries to its corresponding PDF if it exists
   - exports all bib/KEY.bib
   - updates index.html
     + Journal Articles (article)
     + Articles in Conference Proceedings (inproceedings)
     + Edited Volumes (book, proceedings)
     + Articles in Collections (incollection)
     + Shared Tasks (inproceedings + note = "SharedTask")
   - updates talks.html
     + Talks and Presentations (misc)
