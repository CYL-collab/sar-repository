# SAR Repository Scripts

This directory contains the data-management and static-site generation scripts for the Software Aging Repository (SAR).

Run all commands from the repository root so that relative paths such as `data/list.csv` resolve correctly.

## Data maintenance

`librarian.py` manages papers and scholars:

- `search_new_papers()` searches DBLP for candidate software-aging and software-rejuvenation papers and writes them to `data/add.csv`. Candidates require manual relevance and metadata review before inclusion.
- `update_scholar()` derives authors from the current paper list, normalizes name variants, merges likely duplicates, and updates `data/scholar.csv`.
- `check_paper_inclusion()` checks whether a supplied list of paper titles is indexed by DBLP.

`dblp.py` contains the DBLP API client used by the librarian. `data_clean.py` provides legacy CSV normalization helpers, while `papers.py` defines the publication representation used by the HTML generator.

## Static-site generation

`generate_coauthor_preview.py` reads `data/list.csv` and generates:

- `assets/coauthor-preview.json`, the weighted co-authorship graph;
- `data/coauthor_mapping.csv`, the raw-to-canonical author mapping.

`generate_html.py` reads the maintained CSV files and templates to generate:

- `index.html`, the repository dashboard;
- `components/list.html`, the searchable and filterable paper list;
- `components/coauthor.html`, the co-author network page;
- `assets/index-chart.js`, the data-driven dashboard charts.

Paper counts, scholar counts, venue counts, publication-year ranges, and chart values are derived from the CSV data during generation.

To rebuild all generated assets:

```bash
python src/generate_coauthor_preview.py
python src/generate_html.py
```
