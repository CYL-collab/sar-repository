# Scripts

This directory includes scripts for data management of the cit-repository.

## Librarian

`librarian.py` can be used for searching new papers and collecting scholar names.

* `search_new_papers()`: Search new papers from DBLP.
  * The new papers found will be written into an `add.csv` file.
  * After this step, need to perform further manual processing to filter out irrelvant papers, and also determine filed for each paper.

* `update_scholar()`: Update the scholar data file according to the current paper list data file.

## Generate static HTML Files

`generate_html.py` can be used to generate the final static HTML pages for the repository.

* `generate_index()`: the `index.html` file
* `generate_list()`: the `components/list.html` file